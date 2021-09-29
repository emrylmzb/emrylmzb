import re
import contextlib
from urllib.parse import urljoin
from w3lib import html
from scrapy import Item, Field
from scrapy.loader import ItemLoader
from itemloaders.processors import Identity, TakeFirst, MapCompose

_clean_spaces_re = re.compile("\s+", re.U)

def clean_spaces(value):
    return _clean_spaces_re.sub(' ', value)


def make_absolute_url(val, loader_context):
    base_url = loader_context.get('base_url')
    if base_url is None:
        response = loader_context.get('response')
        if response is None:
            raise AttributeError('You must provide a base_url or a response '
                                 'to the loader context')
        base_url = response.url
    return urljoin(base_url, val)


def remove_query_params(value):
    # some urls don't have ? but have &
    return value.split('?')[0].split('&')[0]


_br_re = re.compile('<br\s?\/?>', re.IGNORECASE)
def replace_br(value):
    return _br_re.sub(' ', value)


def replace_escape(value):
    return html.replace_escape_chars(value, replace_by=u' ')


def split(value):
    return [v.strip() for v in value.split(',')]


def strip(value):
    return value.strip()

class BaseItem(Item):
    def to_dict(self):
        return {
            key: value.to_dict() if isinstance(value, BaseItem) else value
            for key, value in self.items()
        }


class StoreItem(BaseItem):
    StoreId = Field()
    Name = Field()
    Address = Field()
    Street = Field()
    City = Field()
    PostCode = Field()
    PhoneNumber = Field()
    FaxNumber = Field()
    Email = Field()
    OpeningDays = Field()
    GeoLocation = Field()
    Monday = Field()
    Tuesday = Field()
    Wednesday = Field()
    Thursday = Field()
    Friday = Field()
    Saturday = Field()
    Sunday = Field()


class LoaderMixin(object):
    @contextlib.contextmanager
    def push_selector(self, sel):
        orig, self.selector = self.selector, sel
        try:
            yield
        finally:
            self.selector = orig

    def push_css(self, expr):
        return self.push_selector(self.selector.css(expr))

    def push_xpath(self, expr):
        return self.push_selector(self.selector.xpath(expr))

    def add_xpath_if_empty(self, field_name, xpath, *processors, **kw):
        if not any(self.get_collected_values(field_name)):
            self.add_xpath(field_name, xpath, *processors, **kw)

    def add_value_if_empty(self, field_name, value, *processors, **kw):
        if not any(self.get_collected_values(field_name)):
            self.add_value(field_name, value, *processors, **kw)


class StoreLoader(LoaderMixin, ItemLoader):
    default_item_class = StoreItem
    default_input_processor = MapCompose(replace_br, html.remove_tags, html.unquote_markup,
                                         replace_escape, strip, clean_spaces)
    default_output_processor = TakeFirst()

    Monday_in = Identity()
    Tuesday_in = Identity()
    Wednesday_in = Identity()
    Thursday_in = Identity()
    Friday_in = Identity()
    Saturday_in = Identity()
    Sunday_in = Identity()

    Monday_out = Identity()
    Tuesday_out = Identity()
    Wednesday_out = Identity()
    Thursday_out = Identity()
    Friday_out = Identity()
    Saturday_out = Identity()
    Sunday_out = Identity()
