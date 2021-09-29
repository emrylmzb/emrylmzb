import random
import logging
from scrapy.exceptions import NotConfigured
from adboox import settings


logger = logging.getLogger(__file__)


class RandomUserAgentMiddleware(object):
    """This middleware allows spiders to override the user_agent"""

    def __init__(self, user_agents):
        self.user_agents = user_agents

    @classmethod
    def from_crawler(cls, crawler):
        user_agents = getattr(settings, 'USER_AGENTS', [])
        if not user_agents:
            raise NotConfigured
        return cls(user_agents)

    def process_request(self, request, spider):
        if self.user_agents:
            user_agent = random.choice(self.user_agents)
            request.headers.setdefault('User-Agent', user_agent)
