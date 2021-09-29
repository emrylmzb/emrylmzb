import re
import logging
from urllib.parse import urljoin
from scrapy.http.request import Request
from adboox.spiders.base import BaseAdbooxSpider
from adboox.mixins.store import SendStoresWhenIdleMixin
from adboox.items import StoreLoader
from adboox.utils.calendar import de_day_to_abbr, abbr_to_day

logger = logging.getLogger(__name__)


class HitStoresSpider(SendStoresWhenIdleMixin, BaseAdbooxSpider):
    name = '17-stores'
    start_urls = ['https://www.hit.de/marktauswahl.html']
    store_url = ''

    def start_requests(self):
        if self.store_url:
            return [Request(url=self.store_url, callback=self.parse_store)]
        else:
            return super(HitStoresSpider, self).start_requests()

    def parse(self, response):
        for elem in response.xpath('//li[has-class("item") and @data-uid]'):
            geo = {
                'Lan': elem.xpath('@data-lat').extract_first(),
                'Lon': elem.xpath('@data-lng').extract_first()
            }
            sl = StoreLoader(selector=elem)
            with sl.push_xpath('.//div[has-class("store-information")]'):
                sl.add_xpath('Name', './/li[has-class("name")]//text()')
                with sl.push_xpath('.//li[has-class("market-position")]'):
                    sl.add_xpath('PostCode', './/text()', re=r'(\d{5,})')
                    sl.add_xpath('City', './/text()', re=r'(\D+)')

                sl.add_xpath('Street', '(.//li)[2]')
            sl.add_xpath('StoreId', '@data-uid')
            store_extras = sl.load_item()
            store_extras.update({'GeoLocation': geo})
            meta = {'store_extras': store_extras}
            urlpath = elem.xpath('.//a[lower-case(text())="details"]/@href').extract_first()
            url = urljoin(response.url, urlpath)
            yield Request(url=url, callback=self.parse_store, meta=meta)

    def parse_store(self, response):
        sl = StoreLoader(response=response)
        handlers = {
            # 'adresse': self.address_handler,
            'telefonnummer': self.phone_handler,
        }
        col_tmpl = '(//div[has-class("entry")]/div[has-class("text-col")])[{}]'
        with sl.push_xpath(col_tmpl.format(1)):
            for n, label in enumerate(sl.selector.xpath('h3/text()').extract(), 1):
                label = label.lower()
                value = ' '.join([x.strip() for x in sl.selector.xpath(
                    'p[count(preceding-sibling::h3)={}]//text()'.format(n)).extract()])
                handler = handlers.get(label.lower())
                if handler:
                    handler(sl, value)

        store = sl.load_item()
        extras = response.meta.get('store_extras', {})
        for k, v in extras.items():
            store[k] = v

        with sl.push_xpath(col_tmpl.format(2) + '/div[has-class("row")]'):
            date_hours_tmpl = './/div[has-class("col-md-{}")]/text()'
            label = date_hours_tmpl.format(4)
            value = date_hours_tmpl.format(8)
            for date, hours in zip(
                    sl.selector.xpath(label).extract(), sl.selector.xpath(value).extract()):
                self.zeiten_handler(store, date, hours)

        self.stores[store.get('StoreId')] = store
        yield store

    def address_handler(self, loader, value):
        zre = r'(\d{5})'
        loader.add_value('Address', value)
        street, postcode, city = re.split(zre, value)
        loader.add_value('PostCode', postcode)
        loader.add_value('Street', street)
        loader.add_value('City', city)

    def phone_handler(self, loader, value):
        loader.add_value('PhoneNumber', value)

    def zeiten_handler(self, store, de_day, hours):
        try:
            open_hours, close_hours = re.search(
                r'([\d:]+)\s*-\s*([\d:]+)', hours).groups()
            abbr = de_day_to_abbr[de_day.title()]
            day = abbr_to_day[abbr]
            store[day] = {
                'Open': open_hours, 'Close': close_hours
            }
        except (AttributeError, IndexError):
            logger.warn('Cannot parse opening hours "{}" or invalid day "{}" (item: {})'.format(
                hours, de_day, store))
