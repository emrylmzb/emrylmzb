import logging
from datetime import datetime
from scrapy.http import Request
from adboox.spiders.base import BaseAdbooxBrochureSpider
from adboox.mixins.brochure import DirectBrochureDownloadMixin
from adboox.utils.types import Resource

logger = logging.getLogger(__name__)


class FamilaNordostBrochureSpider(DirectBrochureDownloadMixin, BaseAdbooxBrochureSpider):
    name = '30-brochure'
    valid_between = {}

    def start_requests(self):
        for store_id in self.stores:
            url = f'https://www.bonialserviceswidget.de/de/stores/{store_id}/brochures?storeId={store_id}&publisherId=48649527&limit=100'
            yield Request(url, meta={'store_id': store_id})

    def parse(self, response):
        store_id = response.meta['store_id']
        data = response.json()
        for brochure in data['brochures']:
            content_id = brochure['contentId']
            pdf_url = f'https://aws-ops-bonial-biz-production-published-content-pdf.s3-eu-west-1.amazonaws.com/{content_id}/{content_id}.pdf'
            if self.create_pdf_resource(pdf_url, content_id, store_id):
                self.add_valid_between(content_id, brochure)

    def add_valid_between(self, resource_key, brochure):
        start = datetime.strptime(brochure['validFrom'].split('T')[0], '%Y-%m-%d')
        end = datetime.strptime(brochure['validUntil'].split('T')[0], '%Y-%m-%d')
        self.valid_between[resource_key] = {
            'ValidBetween': {
                'StartDate': start.strftime('%d-%m-%Y'),
                'EndDate': end.strftime('%d-%m-%Y')
            }
        }

    def gen_resource_report(self, resource: Resource):
        report = super().gen_resource_report(resource)
        valid_between = self.valid_between.get(resource.key)
        if valid_between:
            report.update(valid_between)
        return report

