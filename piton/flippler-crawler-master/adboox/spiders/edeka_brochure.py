import logging
from scrapy.http import Request
from adboox.spiders.base import BaseAdbooxBrochureSpider
from adboox.utils.types import Resource
from adboox.mixins.blaetter import BlaetterkatalogMixin

logger = logging.getLogger(__name__)


class EdekaBrochureSpider(BlaetterkatalogMixin, BaseAdbooxBrochureSpider):
    name = '29-brochure'

    def start_requests(self):
        for n, store_id in enumerate(self.stores):
                store_details_url = 'https://www.edeka.de/eh/technische-seiten/navigation/{}.json'.format(store_id)
                yield Request(
                    store_details_url,
                    callback=self.parse_store_details,
                    errback=self.catalog_page_failed,
                    meta={'cookiejar': n, 'store_id': store_id})

    def parse_store_details(self, response):
        store_details = response.json()
        catalog_url = store_details.get('market', {}).get('catalogueUrl', '')
        store_id = response.meta.get('store_id')
        cookiejar = response.meta.get('cookie_jar')
        try:
            key1, key2 = self.get_keys_from_catalog_url(catalog_url)
            catalog_xml_url = 'https://blaetterkatalog.edeka.de/{}/{}/blaetterkatalog/xml/catalog.xml'.format(key1, key2)
            resource_key = store_id
            resource = self.resources.get(resource_key)
            if resource is None:
                resource = Resource.from_kw(outfile='{}.pdf'.format(resource_key))
                self.resources[resource_key] = resource
                yield Request(
                    catalog_xml_url,
                    callback=self.parse_catalog_page,
                    errback=self.catalog_page_failed,
                    meta={'cookiejar': cookiejar, 'resource_key': resource_key})
            resource.stores.append(store_id)
        except Exception as ex:
            self.logger.error(
                'Unable to make catalog request for store: %s, catalog_url: %s',
                store_id, catalog_url, exc_info=ex)
            self.invalid_stores.append(store_id)
    
    @staticmethod
    def get_keys_from_catalog_url(url):
        frags = url.split('/')
        if frags and frags[-1] == 'index.html':
            return frags[-3], frags[-2]
