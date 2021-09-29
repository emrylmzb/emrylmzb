import re
import logging
from urllib.parse import urljoin
from scrapy.http.request import Request
from adboox.utils.types import Resource
from adboox.spiders.base import BaseAdbooxBrochureSpider
from adboox.mixins.brochure import DirectBrochureDownloadMixin

logger = logging.getLogger(__name__)


class HitBrochureSpider(DirectBrochureDownloadMixin, BaseAdbooxBrochureSpider):
    name = '17-brochure'
    valid_between = {}
    report_extras = {}

    def start_requests(self):
        url_tmpl = 'https://www.hit.de/1.0/api/store/setMy.json?store_id={}'
        for n, store in enumerate(self.stores):
            url = url_tmpl.format(store)
            yield Request(url, callback=self.store_set, errback=self.store_set_failed,
                          meta={'cookiejar': n, 'store': store})

    def store_set_failed(self, failure):
        request = failure.request
        store = request.meta.get('store')
        logger.warn('Cannot set store {}'.format(store))
        self.invalid_stores.append(store)

    def store_set(self, response):
        cj = response.meta['cookiejar']
        store = response.meta['store']
        return Request(url='https://www.hit.de/handzettel.html', dont_filter=True,
                       callback=self.parse_brochure, meta={'cookiejar': cj, 'store': store})

    def parse_brochure(self, response):
        pdf_path = response.xpath('//a[contains(@href, ".pdf")]/@href').extract_first()
        if pdf_path:
            response.meta.update({'pdf_path': pdf_path})
            return self.pdf_brochure(response)

        images = response.xpath('//div[re:test(@page, "\d+")]/img/@data-highres').extract()
        if images:
            response.meta.update({'images': images})
            return self.img_brochure(response)

        store = response.meta['store']
        logger.error("Neither pdf nor brochure images could be found for {}".format(store))

    def pdf_brochure(self, response):
        store = response.meta['store']
        pdf_path = response.meta['pdf_path']
        resource_key = self.get_resource_key(pdf_path)
        self.parse_report_extras(resource_key, response)
        if not resource_key:
            logger.error('Unable to get resource key from {} (store: {})'.format(pdf_path, store))
            self.invalid_stores.append(store)
            return

        resource = self.resources.get(resource_key)
        if not resource:
            self.get_valid_between(resource_key, response)
            pdf_url = urljoin(response.url, pdf_path)
            cj = response.meta['cookiejar']
            return self.create_pdf_resource(pdf_url, resource_key, store, meta={'cookiejar': cj})
        else:
            resource.stores.append(store)

    def img_brochure(self, response):
        store = response.meta['store']
        images = response.meta['images']
        resource_key_base = self.get_resource_key(images[0])
        if not resource_key_base:
            logger.error('Unable to get resource key from {} (store: {})'.format(images[0], store))
            self.invalid_stores.append(store)
            return

        suffix = images[0].split('.')[-1]
        resource_key = resource_key_base + '-' + suffix
        self.parse_report_extras(resource_key, response)
        resource = self.resources.get(resource_key)
        if not resource:
            # fix image urls
            images = [urljoin(response.url, i) for i in images]
            resource = Resource.from_kw(urls=images, stores=[store])
            self.resources[resource_key] = resource
        else:
            resource.stores.append(store)

    def parse_report_extras(self, key, response):
        title = response.xpath('//h1/text()').extract_first()
        if title:
            extras = self.report_extras.get(key, {})
            extras['Title'] = title
            self.report_extras[key] = extras

    def get_valid_between(self, resource_key, response):
        store = response.meta['store']
        try:
            vb_day, vb_month, vb_year, ve_day, ve_month, ve_year = re.search(
                r'(\d+)\.(\d+)\.(\d+|)\s*-\s*(\d+)\.(\d+)\.(\d+|)', response.text, re.DOTALL).groups()
            if not (vb_year and ve_year):
                vb_year = ve_year = (vb_year or ve_year) or '2016'
            entry = {
                'ValidBetween': {
                    'StartDate': '.'.join([vb_day, vb_month, vb_year]),
                    'EndDate': '.'.join([ve_day, ve_month, ve_year])
                }
            }
            self.valid_between[resource_key] = entry
        except AttributeError:
            logger.error('Unable to get valid between info for store {}'.format(store))

    @staticmethod
    def get_resource_key(url):
        try:
            return re.search(r'([A-Z_\d]+)', url).group(1)
        except (AttributeError, TypeError):
            pass

    def gen_resource_report(self, resource):
        report = super(HitBrochureSpider, self).gen_resource_report(resource)
        url = resource.urls[0]
        key = self.get_resource_key(url)
        report.update(self.valid_between.get(key, {}))
        report.update(self.report_extras.get(key, {}))
        return report
