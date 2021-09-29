from __future__ import unicode_literals
import os
import re
import json
import logging
import tempfile
from urllib.parse import urljoin
import hashlib
import shutil
import pprint
from datetime import datetime
from scrapy import signals
from scrapy.http.request import Request
from scrapy.spiders import Spider
from scrapy.exceptions import DontCloseSpider
from adboox import settings
from adboox.exceptions import FatalError
from adboox.utils.os_level import fix_permissions
from adboox.utils.encoders import ItemEncoder
from adboox.utils.url import get_ext_from_url

logger = logging.getLogger(__name__)

class BaseAdbooxSpider(Spider):
    crawl_id = 0
    notification_url = getattr(settings, 'NOTIFICATION_URL', '')
    save_dir = ''

    def __init__(self, *a, **kw):
        super(BaseAdbooxSpider, self).__init__(*a, **kw)
        if not self.notification_url:
            raise RuntimeError('Notification url must be provided.')
        self.jobid = getattr(self, 'jobid', 'unknown')
        self.started_at = datetime.now().replace(microsecond=0)
        self.reports_send = False

    @classmethod
    def from_crawler(cls, crawler, *a, **kw):
        spider = super(BaseAdbooxSpider, cls).from_crawler(crawler, *a, **kw)
        crawler.signals.connect(spider.spider_error, signals.spider_error)
        return spider

    def spider_error(self, failure, spider):
        ex = failure.value
        if isinstance(ex, FatalError):
            error = failure.getErrorMessage()
            r = self.send_error(error)
            spider.crawler.engine.schedule(r, spider)

    def notification_failed(self, _):
        logger.error('Unable to notify {} about job {}'.format(self.notification_url, self.jobid))

    def send_data(self, data):
        logger.info('Sending report: {}'.format(pprint.pformat(data)))
        headers = {'Content-Type': 'application/json'}
        r = Request(url=self.notification_url, method='POST', headers=headers,
                    body=json.dumps(data, cls=ItemEncoder),
                    callback=lambda _: None, errback=self.notification_failed, dont_filter=True,
                    meta={'dont_proxy': True})
        return r

    def send_results(self, results, **kw):
        data = {
            'JobId': self.jobid,
            'Status': 'finished',
            'Results': results,
            'CrawlTime': self.started_at.isoformat()
        }
        data.update(kw)
        self.reports_send = True
        return self.send_data(data)

    def send_error(self, error):
        data = {
            'JobId': self.jobid,
            'Status': 'failed',
            'Error': error,
            'CrawlTime': self.started_at.isoformat()
        }
        return self.send_results(data)


class BaseAdbooxBrochureSpider(BaseAdbooxSpider):
    save_dir = 'brochures'
    stores = ''
    download_warnsize = 0
    resource_sorted = False

    def __init__(self, *a, **kw):
        super(BaseAdbooxBrochureSpider, self).__init__(*a, **kw)
        self.tempdir = tempfile.mkdtemp()
        fix_permissions(self.tempdir)
        stores = [s.strip() for s in self.stores.split(',')]
        stores = [s for s in stores if s]
        self.stores = stores
        self.total_stores = len(self.stores)
        self.resources = {}
        self.invalid_stores = []

        self.fileserver_url = urljoin(
            getattr(settings, 'FILESERVER_URL'), self.save_dir + '/')

        logger.info(
            '{} settings: fileserver url: {}, stores: {}'
            .format(self.name, self.fileserver_url, ', '.join(self.stores)))

    @classmethod
    def from_crawler(cls, crawler, *a, **kw):
        spider = super(BaseAdbooxBrochureSpider, cls).from_crawler(crawler, *a, **kw)
        # Most of task waiting will be done in spider_idle function.
        crawler.signals.connect(spider.spider_idle, signals.spider_idle)
        return spider

    def spider_idle(self, spider):
        if not self.reports_send:
            # Resource collection is done, report it now.
            results = self.get_resource_results()
            reports = self.gen_reports()
            reports.update(dict(Version='1.3', CrawlerType='SN'))
            r = self.send_results(results, **reports)
            spider.crawler.engine.schedule(r, spider)
            self.resources.clear()
            raise DontCloseSpider

    def get_resource_results(self):
        results = []
        for resource in self.resources.values():
            if len(resource.urls) <= 0:
                logger.warn('Invalid resource is will not be reported %s', resource)
                continue

            if len(resource.urls) == 1:
                ext = get_ext_from_url(resource.urls[0])
                result = {
                    'Type': ext,
                    'Path': resource.urls[0],
                    'Stores': resource.stores,
                    'SelectAllStores': set(resource.stores) == set(self.stores)
                }
            elif len(resource.urls) > 1:
                try:
                    exts = set([get_ext_from_url(u) for u in resource.urls])
                    if len(exts) != 1:
                        logger.warn('Resource with multiple extension types {} (resource: {})'.format(
                            exts, resource))
                    result_type = resource.type or list(exts)[0]
                except IndexError:
                    result_type = 'Unknown'

                try:
                    urls = resource.urls
                    if not self.resource_sorted:
                        urls = sorted(urls, key=lambda x: int(re.findall(r'(\d+)', x)[-1]))
                except IndexError:
                    logger.warn('Unable to sort urls {}'.format(resource))
                    urls = resource.urls

                pages = []
                for n, url in enumerate(urls, start=1):
                    page = {
                        'PageNumber': n,
                        'Path': url
                    }
                    pages.append(page)
                result = {
                    'Type': result_type,
                    'Pages': pages,
                    'Stores': resource.stores,
                    'SelectAllStores': set(resource.stores) == set(self.stores)
                }

            result.update(self.gen_resource_report(resource))
            result['Items'] = [item.to_report() for item in resource.items]
            results.append(result)
        return results

    def gen_reports(self):
        return {'FailedStores': self.invalid_stores}

    def gen_resource_report(self, resource):
        return {
            'MemberOfGroup': self.get_member_of_group(resource=resource),
            'IsNational': False
        }

    def save_asset(self, url, response):
        fname = hashlib.sha1(url).hexdigest() + '.' + url.split('.')[-1]
        path = os.path.join(self.tempdir, fname)
        with open(path, 'w') as f:
            f.write(response.body)
            return path

    def delete_downloaded_files(self):
        shutil.rmtree(self.tempdir)

    def get_member_of_group(self, *a, **kw):
        name = self.name.split('-')[0].title()
        started = self.started_at.strftime('%Y-%m-%d-%H-%M')
        return name + '_' + started
