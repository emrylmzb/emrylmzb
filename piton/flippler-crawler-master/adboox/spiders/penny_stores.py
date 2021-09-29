from __future__ import unicode_literals
import re
import json
import logging
import pprint
from scrapy.http.request.form import FormRequest
from adboox.spiders.base import BaseAdbooxSpider
from adboox.mixins.store import SendStoresWhenIdleMixin
from adboox.utils import load_csv_data
from adboox.utils.calendar import iter_from_abbr_de

logger = logging.getLogger(__name__)


class PennyStoresSpider(SendStoresWhenIdleMixin, BaseAdbooxSpider):
    name = '37-stores'

    def start_requests(self):
        tmpl = ('http://www.penny.de/marktsuche/?type=666&tx_pennyregionalization_googlemarket['
                'location]=Deutschland,%20{}')
        de_cities = load_csv_data('de_cities.csv')
        zipcodes = {x['PostalCode'] for x in de_cities}
        for n, zipcode in enumerate(zipcodes):
            url = tmpl.format(zipcode)
            yield FormRequest(url=url, callback=self.parse_stores, cookies={'cookiejar': n})

    def parse_stores(self, response):
        data = json.loads(response.body)
        for store_raw in data['markets']:
            store = self.convert_store(store_raw)
            self.stores[store['StoreId']] = store
            yield store

    def convert_store(self, store_raw):
        addr_keys = ['address', 'zip', 'city']
        store = {
            'StoreId': str(store_raw['marketId']),
            'Street': store_raw['address'],
            'City': store_raw['city'],
            'PostCode': store_raw['zip'],
            'Address': ', '.join([store_raw[k] for k in addr_keys]),
            'GeoLocation': {
                'Lat': str(store_raw['lat']),
                'Lon': str(store_raw['lng']),
            }
        }

        try:
            opening_time = store_raw['openingTime']
            day_from, day_to, open_hour, close_hour = re.search(
                r'(\w+)\s*-\s*(\w+)\s*:\s*([\d:]+)\s*-([\d:]+)', opening_time).groups()
            for _, day in iter_from_abbr_de(day_from[:2].lower(), day_to[:2].lower()):
                store[day] = {
                    'Open': open_hour,
                    'Close': close_hour
                }
        except AttributeError:
            logger.error('Unable to parse opening time {}'.format(pprint.pformat(store_raw)))
        return store
