# -*- coding: utf-8 -*-

# Scrapy settings for adboox project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#     http://scrapy.readthedocs.org/en/latest/topics/downloader-middleware.html
#     http://scrapy.readthedocs.org/en/latest/topics/spider-middleware.html
import os
import socket

BOT_NAME = 'adboox'

SPIDER_MODULES = ['adboox.spiders']
NEWSPIDER_MODULE = 'adboox.spiders'

USER_AGENTS = [
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/49.0.2623.87 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.104 Safari/537.36',
    'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:11.0) Gecko/20100101 Firefox/11.0',
]

DOWNLOADER_MIDDLEWARES = {
    'adboox.downloadermiddlewares.random_user_agent.RandomUserAgentMiddleware': 543,
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'scrapy_crawlera.CrawleraMiddleware': 610,
}

DOWNLOAD_HANDLERS = {'s3': None}

# COOKIES_DEBUG = True
AUTOTHROTTLE_ENABLED = True
FILESERVER_PATH = '/data'
FILESERVER_URL = 'http://localhost:8080'

# Update fileserver url if running on server
HOSTNAME_IP_MAPPING = {
    'scrapy1.docker.adx': '46.101.217.73',
}

hostname = os.environ.get('HOST_HOSTNAME', '') or socket.gethostname()
if hostname in HOSTNAME_IP_MAPPING:
    addr = HOSTNAME_IP_MAPPING[hostname]
    FILESERVER_URL = FILESERVER_URL.replace('localhost', addr)

CRAWLERA_ENABLED = False
CRAWLERA_APIKEY = 'f0e54dda9ae841a8b27fe26daf0a6712'