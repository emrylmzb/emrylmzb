import re
import logging
import pprint
import codecs
from urllib.parse import urlencode, quote
from scrapy.http import Request
from adboox.spiders.base import BaseAdbooxSpider
from adboox.mixins.store import SendStoresWhenIdleMixin
from adboox.utils.js_parser import parse_variables
from adboox.utils import load_csv_data
from adboox.utils.geo import calculate_distance

logger = logging.getLogger(__name__)

class LidlStoresSpider(SendStoresWhenIdleMixin, BaseAdbooxSpider):
    name = '1-stores'
    allowed_domains = ['lidl.de']
    test_zip = ''

    def start_requests(self):
        url = 'https://www.lidl.de/de/asset/other/storeFinder.js'
        yield Request(url=url, callback=self.parse_store_finder_js)

    def parse_store_finder_js(self, response):
        m = re.search(r'bingMap:\s*{', response.text)
        if not m:
            logger.error('Unable to find bingMap data (url: %s)', response.url)
            return

        stack = ['{']
        text = '{'
        pos = m.end()
        while len(stack):
            try:
                c = response.text[pos]
            except IndexError:
                logger.warning('StoreFinder response is too short')
                break
            text += c
            if c == '{':
                stack.append('{')
            elif c == '}':
                stack.pop()

            pos += 1
        logger.info('Captured text: %s', text)
        js_var = 'var data = {};'.format(text)
        parsed = parse_variables(js_var)
        data = parsed.get('data')
        if not data:
            logger.error('Unable to get map data')
            return

        query_url = data.get('DATA_SOURCE_URL', {}).get('DE')
        login_key = data.get('DATA_SOURCE_QUERY_KEY', {}).get('DE')
        if not (query_url and login_key):
            logger.error('Unable to get query url or login key from %s', pprint.pformat(data))
            return

        meta = {
            'query_url': query_url
        }
        query_params = {
            'entry': 0, 'fmt': 1, 'group': 'MapControl', 'name': 'MVC', 'version': 'v8',
            'mkt': 'de-DE', 'auth': login_key, 'type': 3,
            'jsonp': 'Microsoft.Maps.NetworkCallbacks.f_logCallbackRequest'
        }
        query = urlencode(query_params)
        login_url = ('https://dev.virtualearth.net/webservices/v1/LoggingService/'
                     'LoggingService.svc/Log?{}').format(query)
        return Request(url=login_url, callback=self.parse_login, meta=meta, dont_filter=True)

    def parse_login(self, response):
        m = re.search(r'Microsoft.Maps.NetworkCallbacks.f_logCallbackRequest\((.*)\)',
                      response.text)
        if not m:
            logger.error('Unable to capture js variable from %s', response.text)
            return

        js_var = 'var auth_data = {};'.format(m.group(1))
        parsed = parse_variables(js_var)
        logger.info('Parsed auth data %s', pprint.pformat(parsed))
        session_id = parsed.get('auth_data', {}).get('sessionId')
        if not session_id:
            logger.error('Unable to find session id from %s', pprint.pformat(parsed))
            return

        cities = load_csv_data('de_cities.csv')
        if self.test_zip:
            cities = [c for c in cities if c['PostalCode'] == self.test_zip]

        last = (0, 0)
        limit = 100  # in km
        for city in cities:
            loc = list(map(float, (city['Latitude'], city['Longitude'])))
            dist = calculate_distance(loc, last)
            if dist < limit:
                continue

            radius = limit * 1.5
            logger.info('Searching lidl stores around %s (radius %s)', loc, radius)
            last = loc
            params = [
                ('$select', '*'),
                ('$filter', quote('Adresstyp Eq 1')),
                ('key', session_id),
                ('$format', 'json'),
                ('jsonp', 'Microsoft_Maps_Network_QueryAPI_1'),
                ('spatialFilter', 'nearby(%27{},{}%27,{})'.format(loc[0], loc[1], radius))
            ]
            query = '&'.join(['{}={}'.format(k, v) for k, v in params])
            url = response.meta['query_url'] + '?' + query
            meta = {
                'location': loc,
                'radius': radius
            }
            yield Request(url=url, callback=self.parse_stores, dont_filter=True, meta=meta)

    def parse_stores(self, response):
        m = re.search(r'Microsoft_Maps_Network_QueryAPI_1\((.*)\)', response.text)
        if not m:
            logger.error('Unable to capture stores data from %s', response.text)
            return

        cb_data_raw = 'var cb_data = {};'.format(m.group(1))
        cb_data = parse_variables(cb_data_raw)
        try:
            stores = cb_data['cb_data']['d']['results']
        except KeyError:
            logger.error('Unable to find results from parsed data %s', pprint.pformat(cb_data))
            return

        logger.info(
            'Parsing number of %s stores (location %s)', len(stores), response.meta['location'])

        for store in stores:
            converted = self.convert_store(store)
            self.stores[converted['StoreId']] = converted
            yield converted

    def convert_store(self, store_js):
        address = ', '.join([store_js['AddressLine'], store_js['PostalCode'], store_js['Locality']])
        store = {
            'StoreId': store_js['EntityID'] + '-' + str(store_js['AR']),
            'Name': codecs.decode(store_js['ShownStoreName'], 'unicode-escape'),
            'Address': codecs.decode(address, 'unicode-escape'),
            'Street': codecs.decode(store_js['AddressLine'], 'unicode-escape'),
            'City': codecs.decode(store_js['Locality'], 'unicode-escape'),
            'PostCode': store_js['PostalCode'],
            'PhoneNumber': None,
            'FaxNumber': None,
            'Email': None,
            'OpeningDays': None,
            'GeoLocation': {
                'Lat': store_js['Latitude'],
                'Lon': store_js['Longitude']
            }
        }
        mapping = {
            'mo': 'Monday', 'di': 'Tuesday', 'mi': 'Wednesday', 'do': 'Thursday', 'fr': 'Friday',
            'sa': 'Saturday', 'so': 'Sunday'
        }
        opening = store_js['OpeningTimes']
        for opening_data in re.findall(r'([a-z]{2})\s+([\d:]+)-([\d:]+)', opening, re.I):
            day_abbr, open_time, close_time = opening_data
            day = mapping.get(day_abbr.lower())
            if not day:
                logger.warning('Unable to find day %s (opening days: %s)', day_abbr, opening)
                continue
            store[day] = {
                'Open': open_time, 'Close': close_time
            }
        return store
