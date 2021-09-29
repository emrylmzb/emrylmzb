import re
import logging
from scrapy.http import FormRequest
from adboox.spiders.base import BaseAdbooxSpider
from adboox.mixins.store import SendStoresWhenIdleMixin
from adboox.utils import de_cities
from adboox.items import StoreLoader

logger = logging.getLogger(__name__)

WEEKDAYS_MAP = {
    'montag': 'Monday', 'dienstag': 'Tuesday', 'mittwoch': 'Wednesday',
    'donnerstag': 'Thursday', 'freitag': 'Friday', 'samstag': 'Saturday',
    'sonntag': 'Sunday'}
WEEKDAYS = list(WEEKDAYS_MAP.keys())

class NormaStoresSpider(SendStoresWhenIdleMixin, BaseAdbooxSpider):
    name = '36-stores'
    key = 'filialfinder[suche][stadt]'

    def start_requests(self):
        url = 'https://www.norma-online.de/ext/ajax/validate.php'

        for n, city in enumerate(de_cities):
            form = {
                'action': 'ajax_validate_filialfinder__filialfinder_stadt',
                self.key: city,
                'lang': 'de'
            }
            yield FormRequest(
                url=url, callback=self.post_search,
                formdata=form, dont_filter=True,
                meta={'city': city, 'cookiejar': n})

    def post_search(self, response):
        validation = response.json()
        success = validation.get('success', False)
        city = response.meta.get('city')
        if success:
            url = 'https://www.norma-online.de/de/filialfinder/'
            cookiejar = response.meta.get('cookiejar')
            params = {
                'filialfinder[suche][land]': 'Deutschland',
                'filialfinder[suche][radius]': '192000',
                'filialfinder[suche][plz]': '',
                'filialfinder[suche][strasse]': '',
                self.key: city
            }
            yield FormRequest(
                url=url, callback=self.parse_stores,
                formdata=params, dont_filter=True,
                meta={'city': city, 'cookiejar': cookiejar})
        else:
            self.logger.warning('Failed validation: %s for city: %s', validation, city)

    def parse_stores(self, response):
        city = response.meta.get('city')
        stores = response.xpath('//*[@id="map-results-list"]/div[has-class("row")]')
        if not stores:
            logger.warn('There is no result for city %s', city)
        for store in stores:
            item = self.parse_store(store, response)
            store_id = item.get('StoreId')
            if not store_id:
                self.logger.warning('Unable to get store id: %s', item)
                continue

            if store_id in self.stores:
                existing = self.stores[store_id]
                if existing['Street'] != item['Street']:
                    logger.warn('Store id clash between %r and %r', existing, item)
                continue

            def _parse_and_add(day, text):
                store_open, store_close = re.search(r'([^-\s]+)\s*-\s*([^-\s]+)', text).groups()
                key = WEEKDAYS_MAP.get(day)
                item[key] = {'Open': store_open, 'Close': store_close}

            for tr in store.xpath('.//table[has-class("shopHours")]//tr'):
                try:
                    days = tr.xpath('./th/text()').extract_first()
                    hours = tr.xpath('./td/text()').extract_first()
                    begin, end = re.search(r'(\w+)\s*-\s*(\w+)', days).groups()
                    sindex = WEEKDAYS.index(begin.lower())
                    eindex = WEEKDAYS.index(end.lower())
                    for x in WEEKDAYS[sindex:eindex + 1]:
                        _parse_and_add(x.lower(), hours)
                except AttributeError as ex:
                    single = re.search(r'(\w+)', days).group(1)
                    _parse_and_add(single.lower(), hours)
            self.stores[store_id] = item
            yield item

    @staticmethod
    def parse_store(selector, response):
        sl = StoreLoader(selector=selector, response=response)
        sl.add_xpath(
            'StoreId', './/a[starts-with(@href, "#") and contains(text(), "Filiale")]/@href',
            re=r'\d+')
        with sl.push_xpath('(.//div[has-class("row")]/div[not(has-class("counter"))])[1]'):
            sl.add_xpath('Street', './*[not(is-heading())]//text()[1]')
            sl.add_xpath('PostCode', './*[not(is-heading())]//text()[2]', re=r'\d+')
            sl.add_xpath('City', './*[not(is-heading())]//text()[2]',
                         lambda xs: [x.strip() for x in xs], re=r'\D+')

        return sl.load_item()

    @staticmethod
    def stores_failed(failure):
        request = failure.request
        msg = failure.getErrorMessage()
        logger.error('Failed request: %r, reason: %s', request, msg)
