import re
from scrapy.http.request.form import FormRequest
from adboox.spiders.base import BaseAdbooxSpider
from adboox.mixins.store import SendStoresWhenIdleMixin
from adboox.utils import calendar


class NettoStoresSpider(SendStoresWhenIdleMixin, BaseAdbooxSpider):
    name = "10-stores"
    allowed_domains = ["netto-online.de"]
    start_urls = (
        'https://www.netto-online.de',
    )
    outfile = ''

    def parse(self, response):
        formdata = {
            # s=47.271954&n=54.695638&w=6.078287&e=14.95088
            's': '47.271954',
            'n': '54.695638',
            'w': '6.078287',
            'e': '14.95088',
        }

        yield FormRequest(
            url=('https://www.netto-online.de/INTERSHOP/web/WFS/Plus-NettoDE-Site/'
                 'de_DE/-/EUR/ViewNettoStoreFinder-GetStoreItems'),
            callback=self.parse_location, formdata=formdata)

    def parse_location(self, response):
        stores = response.json()
        for store_raw in stores:
            store = self.convert_format(store_raw)
            self.stores[store['StoreId']] = store

    @staticmethod
    def convert_format(store):
        converted = {
            'StoreId': store['store_id'],
            'Name': store['store_name'],
            'Address': (', '.join([store['street'], store['city'], store['state']])),
            'Street': store['street'],
            'City': store['city'],
            'PostCode': store['post_code'],
            'PhoneNumber': None,
            'FaxNumber': None,
            'Email': None,
            'OpeningDays': None,
            'GeoLocation': {
                'Lat': store['coord_latitude'],
                'Lon': store['coord_longitude']
            }
        }

        openings = store['store_opening']
        try:
            begin_date, end_date, open_, close = re.search(
                r'\s*([^.]+)\.-([^.]+)\.:\s*([\d.]+)\s*-\s*([\d.]+)', openings).groups()
            for date_tuple in calendar.iter_from_abbr_de(begin_date.lower(), end_date.lower()):
                _, date = date_tuple
                converted[date] = {'Open': open_, 'Close': close}
        except AttributeError:
            pass

        return converted
