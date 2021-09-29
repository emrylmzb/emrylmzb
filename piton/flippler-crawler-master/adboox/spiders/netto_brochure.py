import re
import logging
from datetime import datetime
from urllib.parse import urljoin, parse_qs
from scrapy.http import Request, FormRequest
from adboox.spiders.base import BaseAdbooxBrochureSpider
from adboox.utils.types import Resource
from adboox.mixins.blaetter import BlaetterkatalogMixin

logger = logging.getLogger(__name__)

class NettoBrochureSpider(BlaetterkatalogMixin, BaseAdbooxBrochureSpider):
    name = "10-brochure"
    allowed_domains = ["netto-online.de"]
    start_urls = ['https://www.netto-online.de/filialfinder/']

    stores_url = None
    total_stores = 0
    resource_sorted = True
    report_extras = {}

    def parse(self, response):
        token_name = token_value = None

        for scr in response.xpath('//script[contains(@type, "javascript")]/text()').extract():
            m = re.search(r'var SYNCHRONIZER_TOKEN_NAME\s*=\s*([^;]+);', scr)
            if m:
                token_name = m.group(1)[1:-1]

            m = re.search(r'var SYNCHRONIZER_TOKEN_VALUE\s*=\s*([^;]+);', scr)
            if m:
                token_value = m.group(1)[1:-1]

            if token_name and token_value:
                break

        if not (token_name and token_value):
            logger.warning('Unable to find synchronizer variables!')
            return

        logger.info('Captured synchronizer variables %s: %s', token_name, token_value)
        store_set_url = ('https://www.netto-online.de/INTERSHOP/web/WFS/Plus-NettoDE-Site/de_DE/-/'
                         'EUR/ViewNettoStoreFinder-AddNettoStoreID')
        for i, store_id in enumerate(self.stores):
            yield FormRequest(
                url=store_set_url, callback=self.store_set, dont_filter=True,
                formdata={token_name: token_value, 'StoreID': store_id},
                errback=self.set_store_failed, meta={'cookiejar': i, 'storeid': store_id})

    def set_store_failed(self, failure):
        request = failure.request
        storeid = request.meta.get('storeid')
        logger.error('Could not set store {}'.format(storeid))
        self.invalid_stores.append(storeid)

    async def store_set(self, response):
        storeid = response.meta.get('storeid')
        cookiejar = response.meta.get('cookiejar', 0)
        # We're done with resource collection for this store.
        self.stores.remove(storeid)
        del response  # no need anymore. better to remove to prevent misuse below.

        meta = {'cookiejar': cookiejar,
                'storeid': storeid, 'catalog_size': 'normal'}
        cookies = {'netto_user_stores_id': storeid}
        prospekte_url = 'https://www.netto-online.de/ueber-netto/Online-Prospekte.chtm'
        yield Request(url=prospekte_url, callback=self.parse_prospekte, meta=meta, cookies=cookies, dont_filter=True)

    def parse_prospekte(self, response):
        catalog_sels = response.xpath('//a[@data-catalog="true"][1]')
        storeid = response.meta['storeid']
        cookies = {'netto_user_stores_id': storeid}
        if not catalog_sels:
            self.invalid_stores.append(storeid)

        for catalog_sel in catalog_sels:
            catalog_url = catalog_sel.xpath('@href').extract_first()
            from_date = self.parse_from_date(catalog_sel)
            to_date = self.parse_to_date(catalog_url)
            meta = response.meta.copy()
            meta['from_date'] = from_date
            meta['to_date'] = to_date
            yield Request(url=catalog_url, callback=self.parse_catalog, meta=meta, cookies=cookies, dont_filter=True)

    def parse_catalog(self, response):
        from_date = response.meta['from_date']
        to_date = response.meta['to_date']
        storeid = response.meta['storeid']
        meta = response.meta.copy()
        ret = self.parse_xml_catalog_url(response)
        if ret:
            key, xml_catalog_url = ret
            resource = self.resources.get(key)
            if not resource:
                resource = Resource.from_kw(key=key)
                self.resources[key] = resource
                self.add_valid_between(key, from_date, to_date)
                meta.update(resource_key=key)
                yield Request(
                    url=xml_catalog_url,
                    callback=self.parse_catalog_page,
                    errback=self.catalog_page_failed,
                    meta=meta)
            resource.stores.append(storeid)
        else:
            self.invalid_stores.append(storeid)

    def parse_xml_catalog_url(self, response):
        catalogs_base_path = re.search("catalogsBasePath:\s*'(.+)'", response.text)
        if catalogs_base_path:
            catalogs_base_path = catalogs_base_path.group(1).replace("\\", "")
            catalog = re.search("catalog:\s*'(.+)'", response.text)
            if catalog:
                catalog = catalog.group(1).replace("\\", "")
                path = catalogs_base_path + catalog + "/xml/catalog.xml"
                return [catalog.split('/')[0], urljoin(response.url, path)]

    def parse_from_date(self, sel):
        texts = sel.xpath('//text()').extract()
        for text in texts:
            m = re.search(r'ab \w+,\s*(\d+\.\d+\.\d+)', text)
            if m:
                return m.group(1)

    def parse_to_date(self, catalog_url):
        qs = parse_qs(catalog_url)
        expires = qs.get('expires')
        if expires:
            expires = int(expires[0])
            try:
                expires = datetime.fromtimestamp(expires)
                return expires.strftime('%d.%m.%Y')
            except Exception as ex:
                logger.error('Unable to parse {}'.format(expires), exc_info=ex)

    def add_valid_between(self, key, from_date, to_date):
        extras = self.report_extras.get(key, {})
        extras['ValidBetween'] = {
            'StartDate': from_date,
            'EndDate': to_date
        }
        self.report_extras[key] = extras

    def gen_resource_report(self, resource):
        report = super(NettoBrochureSpider, self).gen_resource_report(resource)
        extras = self.report_extras.get(resource.key)
        if extras:
            report.update(extras)
        return report
