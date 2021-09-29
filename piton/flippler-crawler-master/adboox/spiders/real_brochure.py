import re
import logging
from scrapy.http import Request
from adboox.spiders.base import BaseAdbooxBrochureSpider
from adboox.mixins.brochure import DirectBrochureDownloadMixin

logger = logging.getLogger(__name__)

class RealBrochureSpider(DirectBrochureDownloadMixin, BaseAdbooxBrochureSpider):
    name = '16-brochure'
    allowed_domains = ['real.de']
    brochure_start_date = ''
    brochure_end_date = ''

    def start_requests(self):
        url = 'http://prospekt.real.de/wochenprospekte.html'
        for n, store in enumerate(self.stores):
            yield Request(url, callback=self.parse_brochure_page, cookies={'real_bkz': store},
                          dont_filter=True, meta={'cookiejar': n, 'store': store})

    def parse_brochure_page(self, response):
        self.parse_brochure_valid_dates(response)
        store = response.meta.get('store')
        brochures = response.xpath(
            '//div[starts-with(@id, "pageflip_") and not(@id="pageflip_config")]')
        if not brochures:
            logger.warn('Unable to find brochure for {}'.format(store))
            self.invalid_stores.append(store)

        pdflink_xpath = './@data-pdflink[re:test(., "\.pdf$")]'
        for brochure in brochures:
            key = self.get_resource_key(brochure.xpath(pdflink_xpath).extract_first())
            if not key:
                logger.warn('Unable to extract key from {}'.format(brochure.extract()))
                continue

            resource = self.resources.get(key)
            if resource:
                resource.stores.append(store)
            else:
                url = brochure.xpath(pdflink_xpath).extract_first()
                if not url:
                    logger.warn("Unable to get the pdflink from {}".format(brochure.extract()))
                    continue
                yield self.create_pdf_resource(url, key, store)

    def parse_brochure_valid_dates(self, response):
        if self.brochure_start_date or self.brochure_end_date:
            return
        text = response.xpath(
            u'//*[contains(text(), "gültig") and contains(text(), "bis")]/text()').extract_first()
        try:
            start, end = re.search(r'([\.\d]+)\s*bis\s*([\.\d]+)', text).groups()
            self.brochure_start_date, self.brochure_end_date = start, end
        except (AttributeError, TypeError, ValueError):
            pass

    @staticmethod
    def get_resource_key(text):
        try:
            return text.split('/')[-1].split('.')[0]
        except (AttributeError, IndexError):
            pass

    def gen_resource_report(self, resource):
        report = super(RealBrochureSpider, self).gen_resource_report(resource)
        if self.brochure_start_date or self.brochure_end_date:
            report['ValidBetween'] = {
                'StartDate': self.brochure_start_date,
                'EndDate': self.brochure_end_date
            }
        url = resource.urls[0]
        report['MemberOfGroup'] = self.get_member_of_group(url=url)
        return report

    def get_member_of_group(self, *a, **kw):
        default = super(RealBrochureSpider, self).get_member_of_group()
        try:
            url = kw.get('url', '')
            identifier = re.search(r'(?:\bKW\d+\b)/([^/]+)', url).group(1)
        except (AttributeError, KeyError):
            identifier = 'Unknown'
        return default + '_' + identifier
