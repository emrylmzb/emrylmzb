import re
import logging
import itertools
from functools import reduce
from datetime import datetime
from collections import defaultdict
from adboox.spiders.base import BaseAdbooxBrochureSpider
from adboox.utils.types import ResourceItem
from adboox.mixins.brochure import DirectBrochureDownloadMixin

logger = logging.getLogger(__name__)

class LidlBrochureSpider(DirectBrochureDownloadMixin, BaseAdbooxBrochureSpider):
    name = '1-brochure'
    allowed_domains = ['lidl.de', 'lidl-pageflip.com', 'lidl-flyer.com']
    warehouse_resource_mapping = defaultdict(list)
    start_urls = ['https://endpoints.lidl-flyer.com/v1/overview/de-DE.json']
    parsed_reports = {}
    today = datetime.today().date()

    def parse(self, response):
        return self.parse_national_flyers(response)

    def get_store_zones(self):
        zones = defaultdict(list)
        for store in self.stores:
            try:
                zone = int(store.split('-')[1])
                zones[zone].append(store)
            except (IndexError, TypeError, ValueError):
                logger.warning('Unable to get zone from store %s', store)
        return zones

    @staticmethod
    def get_national_flyer_resource_key(filename):
        try:
            xs = filename.split('_')
            return '_'.join(itertools.chain(xs[:2], xs[-2:]))
        except:
            return filename

    def parse_national_flyers(self, response):
        try:
            data = response.json()
        except:
            logger.warning("Unable to parse global flyerdata in %s", response.text)
            return

        store_zones = self.get_store_zones()
        for category in data.get('categories', []):
            for subcategory in category.get('subcategories', []):
                for flyer in subcategory.get('flyers', []):
                    if not self.future_brochure(flyer):
                        logger.info('Ignoring flyer source %s', flyer)
                        continue

                    zone_codes = [region.get('code') for region in flyer.get('regions', [])]
                    national = 0 in zone_codes
                    stores = self.stores if national else \
                        [store for zone_code in zone_codes for store in store_zones[zone_code]]

                    pdf_url = flyer.get('pdfUrl')
                    pdf_id = flyer.get('id')
                    if pdf_url and pdf_id:
                        resource_key = self.get_national_flyer_resource_key(pdf_id)

                        for store in stores:
                            self.create_pdf_resource(pdf_url, resource_key, store)

                        if resource_key not in self.parsed_reports:
                            report = {
                                'start_date': flyer.get('offerStartDate', flyer.get('startDate')),
                                'end_date': flyer.get('offerEndDate', flyer.get('endDate')),
                                'is_national': national,
                                'title': flyer.get('title'),
                            }
                            self.parsed_reports[resource_key] = report
                    else:
                        logger.warning('Invalid global flyer entry %s', flyer)

    def future_brochure(self, flyer):
        offer_start = flyer.get('offerStartDate', flyer.get('startDate'))
        if not offer_start:
            logger.error('Unable to find offer start date from %s', flyer)
            return

        try:
            offer_start = datetime.strptime(offer_start, '%Y-%m-%d').date()
            return self.today < offer_start
        except:
            logger.exception('Unable to parse the date %s', offer_start)

    def get_brochure_items_from_national_flyer(self, response):
        """ The existing item information available in national flyers lack width/height """
        data = response.json()
        pages = data.get('flyer', {}).get('pages', [])
        for page in pages:
            for link in page.get('links', []):
                pass

    @staticmethod
    def get_items_from_catalog_file(response):
        def convert_area_pos(pos):
            # Coordinate values float between 0 and 1
            # X values: 0 means left, 1 means right.
            # Y values: 0 means top, 1 means bottom.
            coords = [float(p.strip()) for p in pos.split(',')]
            xs = [x for index, x in enumerate(coords) if not index % 2]
            ys = [y for index, y in enumerate(coords) if index % 2]
            height = max(ys) - min(ys)
            width = max(xs) - min(xs)
            points = zip(xs, ys)
            top_left = reduce(lambda p1, p2: p1 if p1[0] <= p2[0] and p1[1] <= p2[1] else p2,
                              points, (1, 1))
            x, y = top_left
            return x, y, width, height

        items = []
        for page in response.xpath('//page'):
            num = page.xpath('./@number').extract_first()
            for area in page.xpath('.//area'):
                pos = area.xpath('./shape/@coords').extract_first()
                try:
                    x, y, width, height = convert_area_pos(pos)
                except:
                    logger.exception('Cannot convert item position %s (url: %s)', pos, response.url)
                else:
                    item_url = area.xpath('./@url').extract_first()
                    item = ResourceItem.from_kw(
                        position_info='relative', page=num, x=x, y=y, width=width, height=height,
                        url=item_url
                    )
                    items.append(item)
        return items

    def use_parsed_report(self, resource, report):
        def get_valid_between():

            def get_safe(key):
                try:
                    val = report[key]
                    return datetime.strptime(val, '%Y-%m-%d').strftime('%d.%m.%Y')
                except:
                    pass
            start_date = get_safe('start_date')
            end_date = get_safe('end_date')
            return {k: v for k, v in zip(['StartDate', 'EndDate'], [start_date, end_date]) if v}

        resource_report = {
            'MemberOfGroup': self.get_member_of_group(url=resource.urls[0]),
            'IsNational': report.get('is_national', False),
            'Title': report.get('title', ''),
        }
        valid_between = get_valid_between()
        if valid_between:
            resource_report['ValidBetween'] = valid_between
        return resource_report

    def gen_resource_report(self, resource):
        key = resource.key
        parsed_report = self.parsed_reports.get(key)
        if key and parsed_report:
            return self.use_parsed_report(resource, parsed_report)

        url = resource.urls[0]
        report = super(LidlBrochureSpider, self).gen_resource_report(resource)
        m = re.search(r'(\d{8})_(\d{8})', url)
        if m:
            def fix_dt_format(s):
                try:
                    return datetime.strptime(s, '%Y%m%d').strftime('%d.%m.%Y')
                except ValueError:
                    return ''

            start, end = m.groups()
            report['ValidBetween'] = {
                'StartDate': fix_dt_format(start),
                'EndDate': fix_dt_format(end)
            }

        report['MemberOfGroup'] = self.get_member_of_group(url=url)
        return report

    def get_member_of_group(self, *a, **kw):
        try:
            url = kw['url']
            path = url.split('/')[-1]
            return path.split('.')[0]
        except (AttributeError, IndexError, KeyError):
            return super(LidlBrochureSpider, self).get_member_of_group()
