import logging
from datetime import datetime
from scrapy.http import Request
from adboox.spiders.base import BaseAdbooxBrochureSpider
from adboox.utils.types import Resource

logger = logging.getLogger(__name__)

class ReweBrochureSpider(BaseAdbooxBrochureSpider):
    name = '38-brochure'
    report_extras = {}
    crawlera_enabled = True
    
    def start_requests(self):
        tmpl = "https://www.bonialserviceswidget.de/de/v4/stores/{}?externalStore=true&publisherId=1062"
        for _, store in enumerate(self.stores):
            url = tmpl.format(store)
            yield Request(url=url, callback=self.parse_store, meta={'store_id': store})

    def parse_store(self, response):
        data = response.json()
        store_ext_id = data['id']
        url = 'https://www.bonialserviceswidget.de/de/stores/{store_id}/brochures?storeId={store_id}&publisherId=1062&limit=100'.format(store_id=store_ext_id)
        yield Request(url=url, callback=self.parse_brochures, meta=response.meta)

    def parse_brochures(self, response):
        data = response.json()
        store_id = response.meta.get('store_id')
        brochures = data.get('brochures', [])
        tmpl = 'https://www.bonialserviceswidget.de//de/v5/brochureDetails/{}?publisherId=1062'
        for brochure in brochures:
            key = brochure['contentId']
            id_ = brochure['id']
            resource = self.resources.get(key)
            if not resource:
                resource = Resource.from_kw(key=key)
                self.add_valid_between(key, brochure)
                self.resources[key] = resource
                meta = {
                    'resource_id': key,
                    'store_id': store_id,
                }
                yield Request(url=tmpl.format(id_), callback=self.parse_brochure_details, meta=meta)
            resource.stores.append(store_id)

    def parse_brochure_details(self, response):
        resource_id = response.meta['resource_id']
        store_id = response.meta['store_id']
        resource = self.resources[resource_id]
        data = response.json()
        for page_num in range(1, data['pageCount']+1):
            page = data['pages'].get(str(page_num))
            if not page:
                logger.warn('Page {} is missing (store id: {})'.format(page_num, store_id))
                continue
            image_url = page['imageUrls']['zoom']
            resource.urls.append(image_url)

    def add_valid_between(self, key, brochure):
        valid_from = self.try_get_valid(brochure, "validFrom")
        valid_until = self.try_get_valid(brochure, "validUntil")
        extras = self.report_extras.get(key, {})
        extras['ValidBetween'] = {
            'StartDate': valid_from,
            'EndDate': valid_until,
        }
        self.report_extras[key] = extras

    def try_get_valid(self, brochure, key):
        try:
            dt = self.parse_isostring(brochure[key])
            return dt.strftime('%d.%m.%Y')
        except:
            pass

    def parse_isostring(self, dt):
        try:
            return datetime.strptime(dt[:16], "%Y-%m-%dT%H:%M")
        except:
            logger.warn("Unable to parse: {}".format(dt))

    def gen_resource_report(self, resource):
        report = super(ReweBrochureSpider, self).gen_resource_report(resource)
        extras = self.report_extras.get(resource.key)
        if extras:
            report.update(extras)
        return report