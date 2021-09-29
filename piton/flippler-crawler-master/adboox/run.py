import logging
import sys

from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

if __name__ == '__main__':
    process = CrawlerProcess(settings=get_project_settings())
    spider_name = sys.argv[1]
    if spider_name in process.spider_loader.list():
        process.crawl(spider_name)
        process.start()
    else:
        logging.error("there is no spider for '{}'".format(spider_name))
