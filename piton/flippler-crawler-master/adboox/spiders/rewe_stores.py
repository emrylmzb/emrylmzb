import re
import logging
import urllib
from scrapy.http import Request
from adboox.spiders.base import BaseAdbooxSpider
from adboox.mixins.store import SendStoresWhenIdleMixin
from adboox.utils.js_parser import parse_variables
from adboox.utils.calendar import abbr_to_day_de, iter_from_abbr_de

logger = logging.getLogger(__name__)

class ReweStoresSpider(SendStoresWhenIdleMixin, BaseAdbooxSpider):
    name = '38-stores'
    start_urls = ['https://marktsuche.rewe.de/']

    def parse(self, response):
        data = response.xpath('//script[contains(text(), "gmapsTempData")]/text()').extract_first()
        if not data:
            logger.error('Unable to find gmapsTempData variable!')
            return

        variables = parse_variables(data)
        gmaps_data = variables.get('gmapsTempData', [])
        if not gmaps_data:
            logger.error('Empty gmapsTempData or failed to be parsed!')

        for n, store in enumerate(gmaps_data):
            try:
                postcode = re.search(r'(\d{4,})+', store['content']).group(1)
            except AttributeError:
                logger.warn('Unable to extract postcode for {}'.format(store))

            query = {
                'addressDisplayName': '{},+{}'.format(
                    postcode, store['city']).encode('utf-8'),
                'customerZip': '{}'.format(postcode),
                'customerLocation': '{},{}'.format(store['lat'], store['lon'])
            }

            url = 'https://marktauswahl.rewe.de/stationarymarkets?' + urllib.urlencode(query)
            yield Request(url=url, callback=self.parse_store,
                          meta={'cookiejar': n, 'store_data': store['city']})

    def parse_store(self, response):
        store = response.meta.get('store_data')
        jscode = response.xpath('//script/text()[contains(., "marketData")]').extract_first()
        if not jscode:
            logger.warn('Unable to query about store data: %s', store)
            return

        variables = parse_variables(jscode)
        market_data = variables.get('marketSelectorData', {}).get('marketData')
        if not market_data:
            logger.warn('Unable to get marketData from query made for %s', store)
            return

        for data in market_data:
            store = {
                'GeoLocation': {
                    'Lat': data.get('marketLatitude'),
                    'Lon': data.get('marketLongitude'),
                },
                'Street': data.get('marketAddress'),
                'PostCode': data.get('marketZip'),
                'City': data.get('marketCity')
            }
            store['StoreId'] = data['marketId']
            store['PhoneNumber'] = data.get('marketPhone')
            store['Name'] = data.get('marketName')
            addr_keys = ['Street', 'PostCode', 'City']
            store['Address'] = ', '.join([x for x in [store.get(x) for x in addr_keys] if x])
            for opening in data['marketHours']:
                days, times = opening['days'], opening['hours']
                try:
                    open_hour, close_hour = re.search(r'([\d:]+)\s*-\s*([\d:]+)', times).groups()
                except AttributeError:
                    continue
                hours = {'Open': open_hour, 'Close': close_hour}
                try:
                    day_from, day_to = re.search(r'(\w+)\s*-\s*(\w+)', days).groups()
                    for _, day in iter_from_abbr_de(day_from[:2].lower(), day_to[:2].lower()):
                        store[day] = hours
                except AttributeError:
                    day = abbr_to_day_de.get(days[:2].lower())
                    store[day] = hours
            self.stores[store['StoreId']] = store
            yield store
