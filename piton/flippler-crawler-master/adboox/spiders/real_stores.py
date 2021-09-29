import logging
from adboox.spiders.base import BaseAdbooxSpider
from adboox.mixins.store import SendStoresWhenIdleMixin

logger = logging.getLogger(__name__)

class RealStoresSpider(SendStoresWhenIdleMixin, BaseAdbooxSpider):
    name = '16-stores'

    allowed_domains = ['real.de']
    start_urls = ['http://www.real.de/markt/markt-aendern/?type=1357643188']

    def parse(self, response):
        data = response.json()
        for store_data in data:
            try:
                store = self.convert_store(store_data)
                self.stores[store['StoreId']] = store
            except IndexError:
                logger.warn('Unable to parse store data: "{}"'.format(store_data))

    def convert_store(self, data):
        store = {
            'StoreId': data['bkz'],
            'Name': data['storeName'],
            'Address': ', '.join([data['street'], data['zipCode'], data['city']]),
            'Street': data['street'],
            'City': data['city'],
            'PostCode': data['zipCode'],
            'FaxNumber': data['fax'] if data.get('fax', '0') != '0' else None,
            'Email': None,
            'OpeningDays': None,
            'GeoLocation': {
                'Lat': data['latitude'],
                'Lon': data['longitude']
            },
        }
        phone = data.get('dialingCode', '') + data.get('phone', '')
        store['PhoneNumber'] = phone if phone else None
        weekdays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        for day in weekdays:
            open_hour = data.get(day + 'Start', '')
            close_hour = data.get(day + 'End', '')
            if open_hour and close_hour:
                store[day.title()] = {
                    'Open': open_hour,
                    'Close': close_hour
                }
        return store
