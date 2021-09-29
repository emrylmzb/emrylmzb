import logging
from datetime import datetime, timedelta
from urllib.parse import urljoin, urlparse, quote
from scrapy.http import Request
from scrapy.linkextractors import LinkExtractor
from adboox.spiders.base import BaseAdbooxBrochureSpider
from adboox.mixins.brochure import DirectBrochureDownloadMixin

logger = logging.getLogger(__name__)

class NormaBrochureSpider(DirectBrochureDownloadMixin, BaseAdbooxBrochureSpider):
    name = '36-brochure'
    allowed_domains = ['norma-online.de']
    url = 'https://www.norma-online.de/de/angebote/onlineprospekt/'
    max_retry = 5
    # crawlera_enabled = True

    def start_requests(self):
        for n, store_id in enumerate(self.stores):
            norma_cookie = self.make_norma_cookie(store_id)
            yield self.make_request(store_id, n, norma_cookie)

    def parse_catalog(self, response):
        store = response.meta.get('store')
        le = LinkExtractor(restrict_xpaths=['//div[has-class("contentBox")]'], deny_extensions=[])
        predicates = [
            lambda parsed: 'online-prospekt' in parsed.path,
            lambda parsed: parsed.path.lower().endswith('.pdf')
        ]
        links = [
            l for l in le.extract_links(response) if all([p(urlparse(l.url)) for p in predicates])]
        if not links:
            logger.error(
                'Unable to find catalog links for store {}'.format(store))
            retry = self.retry(response.meta)
            if retry:
                yield retry
            return

        for link in links:
            key = self.get_catalog_key(link.url)
            if not key:
                logger.error(
                    'Unable to extract key from {} (store: {})'.format(link.url, store))
                continue

            resource = self.resources.get(key)
            if resource:
                resource.stores.append(store)
            else:
                try:
                    pdf_url = urljoin(response.url, link.url)
                    yield self.create_pdf_resource(pdf_url, key, store)
                except Exception as ex:
                    logger.error('Failed to download. Error: "{}" (store: {}, link: {})'.format(
                        ex, store, link.url))
                    self.invalid_stores.append(store)

    def retry(self, meta):
        retried = meta.get('retried', 0)
        store_id = meta['store']
        cookiejar = meta['cookiejar']
        norma_cookie = self.make_norma_cookie(store_id)
        if retried < self.max_retry:
            logger.info(f'Retrying for {norma_cookie} - {cookiejar}')
            return self.make_request(store_id, cookiejar, norma_cookie, retried+1)

    def make_request(self, store_id, cookiejar, norma_cookie, retried=0):
        return Request(
            url=self.url,
            callback=self.parse_catalog,
            dont_filter=True,
            headers={
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:92.0) Gecko/20100101 Firefox/92.0',
                'Referer': 'https://www.norma-online.de/de/angebote/',
            },
            meta={'cookiejar': cookiejar, 'store': store_id, 'retried': retried},
            cookies={
                'NORMA': norma_cookie,
            })

    @staticmethod
    def make_norma_cookie(store_id):
        expire = (datetime.utcnow() + timedelta(weeks=8, days=4)).strftime('%s')
        return quote(f'expire={expire}:clid={store_id}')

    @staticmethod
    def get_catalog_key(url):
        return url.split('/')[-1]
