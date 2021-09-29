from __future__ import unicode_literals
import logging
from urllib.parse import urljoin
from collections import defaultdict
from datetime import datetime

logger = logging.getLogger(__name__)


class BlaetterkatalogMixin(object):
    resource_valid_dates = defaultdict(lambda: [])

    def catalog_page_failed(self, failure):
        request = failure.request
        resource_key = request.meta.get('resource_key')
        resource = self.resources.get(resource_key)
        if resource:
            for store in resource.stores:
                self.invalid_stores.append(store)
            logger.warn('Removing invalid resource: {} (key: {})'.format(resource, resource_key))
            del self.resources[resource_key]

    def parse_catalog_page(self, response):
        catalog_size = response.meta.get('catalog_size', 'large')
        start = int(response.xpath('//mapping//range/@nr_start').extract_first() or 1)
        end = int(response.xpath('//mapping//range/@pages').extract_first()) + 1
        detail_level = '//structure/detaillevel[@name="{}"]'.format(catalog_size)
        rel_path = response.xpath(detail_level + '/@path').extract_first()
        base_path = urljoin(response.url, rel_path)
        prefix = response.xpath(detail_level + '/@filename').extract_first()
        ext = response.xpath(detail_level + '/@extension').extract_first()
        resource_key = response.meta.get('resource_key')
        resource = self.resources[resource_key]
        for i in range(start, end):
            url = base_path + prefix + str(i) + '.' + ext
            resource.urls.append(url)

        ignore_date_parsing = response.meta.get('ignore_date_parsing', False)

        if not ignore_date_parsing:
            try:
                valid_from_raw = response.xpath('//valid/from/text()').extract_first()
                valid_to_raw = response.xpath('//valid/to/text()').extract_first()
                valid_from = self.parse_valid_dt(valid_from_raw)
                valid_to = self.parse_valid_dt(valid_to_raw)
                valid_between_key = valid_from + '-' + valid_to
                self.resource_valid_dates[valid_between_key].append(resource_key)
            except Exception as ex:
                logger.error('Unable to get valid dates for {} (error: {})'.format(response.url, ex))

    @staticmethod
    def parse_valid_dt(dt_raw):
        try:
            return datetime.strptime(dt_raw, '%Y-%m-%d %H:%M:%S').strftime('%d.%m.%Y')
        except:
            return datetime.strptime(dt_raw, '%Y-%m-%d').strftime('%d.%m.%Y')

    def gen_resource_report(self, resource):
        report = super(BlaetterkatalogMixin, self).gen_resource_report(resource)
        resource_key = ([k for k, v in self.resources.items() if v == resource] or [None])[0]
        if not resource_key:
            logger.error('Unable to find resource key for {}'.format(resource))
            return report

        valid_between = [k for k, v in self.resource_valid_dates.items() if resource_key in v]
        if not valid_between:
            logger.error('Unable to find valid between dates for resource {}'.format(resource))
            return report

        valid_from, valid_to = valid_between[0].split('-', 1)
        report['ValidBetween'] = {
            'StartDate': valid_from,
            'EndDate': valid_to
        }
        return report
