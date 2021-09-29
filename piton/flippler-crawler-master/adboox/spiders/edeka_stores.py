from __future__ import unicode_literals
import re
import json
import logging
from urllib.parse import urljoin
from scrapy.http import Request
from adboox.spiders.base import BaseAdbooxSpider
from adboox.mixins.store import SendStoresWhenIdleMixin

logger = logging.getLogger(__name__)


class EdekaStoresSpider(SendStoresWhenIdleMixin, BaseAdbooxSpider):
    name = '29-stores'
    allowed_domains = ['edeka.de']
    start_urls = ['https://www.edeka.de/marktsuche.jsp']

    def parse(self, response):
        for href in response.xpath('//li[contains(@class, "o-store-search-outro")]//@href').extract():
            url = urljoin(response.url, href)
            yield Request(url=url, callback=self.parse_city_page)

    def parse_city_page(self, response):
        try:
            search_results_str = re.search('storesearchresults\s*=\s*([^;]+)', response.text, re.I).groups()[0]
            search_results = json.loads(search_results_str)
            for search_result in search_results:
                if self.supported_store(search_result):
                    store = self.convert_store_data(search_result)
                    self.stores[store['StoreId']] = store
                    yield store
        except Exception as ex:
            logger.warn('Unable to find store search results from {} ({})'.format(response.url, ex))

    def convert_store_data(self, store_data):
        contact = store_data['contact']
        address = contact['address']
        street = address['street']
        city = address['city']
        zipcode = city.get('zipCode')
        city_name = city.get('name')
        state = address.get('federalState')
        data = [street, zipcode, city_name, state]
        address = ', '.join([d for d in data if d])
        store = {
            'StoreId': store_data['id'],
            'Name': store_data['name'],
            'Address': address,
            'Street': street,
            'City': city_name,
            'PostCode': zipcode,
            'PhoneNumber': contact.get('phoneNumber'),
            'FaxNumber': contact.get('facsimileNumber'),
            'Email': contact.get('emailAddress'),
            'GeoLocation': {
                'Lat': store_data['coordinates']['lat'],
                'Lon': store_data['coordinates']['lon']
            },
            'OpeningHours': self.convert_business_hours(store_data['businessHours'])
        }
        return store

    def convert_business_hours(self, business_hours):
        if not business_hours:
            return

        opening_hours = {}
        for value in business_hours.values():
            day = value['weekday'].title()
            opening_hours[day] = {
                'Open': value['from'],
                'Close': value['to']
            }
        return opening_hours

    def supported_store(self, store_data):
        return self.is_distributed_by(store_data, 'edeka') and self.is_edeka(store_data)

    def is_distributed_by(self, store_data, expected_distribution):
        distribution_channel = store_data['distributionChannel']
        distribution_type = distribution_channel.get('type', '').lower()
        return  distribution_type == expected_distribution

    def is_edeka(self, store_data):
        props = [
            self.is_edeka_center(store_data),
            self.is_express(store_data),
        ]
        return not any(props)

    def is_edeka_center(self, store_data):
        name = store_data['name'].lower()
        return name.startswith('e center') or name.startswith('edeka center')

    def is_express(self, store_data):
        name = store_data['name'].lower()
        return name == 'e xpress'
