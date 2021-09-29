import json
from adboox.utils.encoders import ItemEncoder
from scrapy.exceptions import DontCloseSpider
from scrapy.signals import spider_idle


class SendStoresWhenIdleMixin(object):
    stores = {}
    outfile = ''

    @classmethod
    def from_crawler(cls, crawler, *a, **kw):
        spider = super(SendStoresWhenIdleMixin, cls).from_crawler(crawler, *a, **kw)
        crawler.signals.connect(spider.spider_idle, spider_idle)
        return spider

    def spider_idle(self, spider):
        if self.stores:
            stores = list(self.stores.values())
            if self.outfile:
                with open(self.outfile, 'w') as f:
                    json.dump(stores, f, cls=ItemEncoder)
            r = self.send_results(stores)
            spider.crawler.engine.schedule(r, spider)
            self.stores = None
            raise DontCloseSpider
