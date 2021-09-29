import re
import logging
from scrapy.http import FormRequest, Request
from adboox.spiders.base import BaseAdbooxSpider
from adboox.mixins.store import SendStoresWhenIdleMixin
from adboox.utils import calendar

logger = logging.getLogger(__name__)

class FamilaNordostStoresSpider(SendStoresWhenIdleMixin, BaseAdbooxSpider):
    name = '30-stores'

    def start_requests(self):
        url = 'https://www.famila-nordost.de/wp-admin/admin-ajax.php'
        formdata = {
            "action": "mmp_map_markers",
            "type": "map",
            "id": "1",
            "custom": "",
            "all": "false",
            "lang": "null"
        }
        yield FormRequest(url, formdata=formdata)

    def parse(self, response):
        stores = response.json()
        for n, store in enumerate(stores):
            yield Request(
                url=store['link'], 
                callback=self.parse_store_page,
                dont_filter=True,
                meta={'cookiejar': n})

    def parse_store_page(self, response):
        m = re.search('var marktid\s*=\s*"(\d+)"', response.text, re.I)
        if m:
            markt_id = m.group(1)
            url = f"https://www.bonialserviceswidget.de/de/v4/stores/{markt_id}?externalStore=true&publisherId=48649527"
            return Request(url, callback=self.parse_store_data)
        else:
            logger.warn(f"Unable to find store id in {response.url}")

    def parse_store_data(self, response):
        data = response.json()
        name = self.get_name(data)
        address = self.make_address(data)
        store = {
            'Name': name,
            'Address': address,
            'Street': f'{data["street"]} {data["streetNumber"]}',
            'PostCode': int(data["zip"]),
            'GeoLocation': self.make_geo(data),
            'StoreId': data["id"],
        }
        phone = self.get_phone(data)
        if phone:
            store['PhoneNumber'] = phone
        email = self.get_email(data)
        if email:
            store['Email']= email
        opening_hours = self.make_opening_hours(data)
        if opening_hours:
            store['OpeningHours'] = opening_hours
        self.stores[store['StoreId']] = store
        return store

    @staticmethod
    def get_name(data):
        name_prefix = "famila nordost"
        name: str = data['name']
        if name.lower().startswith(name_prefix):
            name = name[len(name_prefix):]
        return name.strip()

    @staticmethod
    def make_address(data):
        return f'{data["street"]} {data["streetNumber"]}, {data["zip"]} {data["city"]}'

    @staticmethod
    def get_phone(data):
        contact = data['contactDetails']
        phones = contact.get('telephoneNumbers')
        if phones:
            for phone in phones:
                if 'number' in phone:
                    return phone['number']

    @staticmethod
    def get_email(data):
        contact = data['contactDetails']
        return contact.get('emailAddress')

    @staticmethod
    def make_geo(data):
        return {
            'Lat': data["lat"],
            'Lon': data["lng"]
        }

    @staticmethod
    def make_opening_hours(data):
        def parse_opening_hour(data):
            day_num = data['dayOfWeek']
            day = calendar.pairs_day_de[day_num-1][0]
            begin = data['minutesFrom'] // 60
            end = data['minutesTo'] // 60
            return day, {'Open': f'{begin}:00', 'Close': f'{end}:00'}

        openings = data['openingHours']
        regular = openings.get('regularOpeningHours', [])
        ret = {}
        for opening_hour in regular:
            day, hour = parse_opening_hour(opening_hour)
            ret[day] = hour
        return ret
