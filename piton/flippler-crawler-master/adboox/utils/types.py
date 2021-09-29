from typing import List, Optional
from dataclasses import dataclass

@dataclass
class ResourceItem:
    position_info: str
    title: Optional[str]
    page: Optional[int]
    x: Optional[int]
    y: Optional[int]
    width: Optional[int]
    height: Optional[int]
    url: Optional[str]

    @classmethod
    def from_kw(cls, **kw):

        def safe_cast(field, type):
            val = kw.get(field)
            if val is not None:
                return type(val)

        position_info = kw.get('position_info', 'absolute')
        title = kw.get('title')
        page = safe_cast('page', int)
        x = safe_cast('x', lambda _x: round(float(_x), 4))
        y = safe_cast('y', lambda _x: round(float(_x), 4))
        width = safe_cast('width', lambda _x: round(float(_x), 4))
        height = safe_cast('height', lambda _x: round(float(_x), 4))
        url = kw.get('url')
        return cls(position_info, title, page, x, y, width, height, url)

    def to_report(self):
        def make_field(key):
            return ''.join([k.title() for k in key.split('_')])

        return {make_field(key): val for key, val in self._asdict().items() if val is not None}

@dataclass
class Resource:
    urls: List[str]
    files: List[str]
    outfile: Optional[str]
    stores: List[str]
    items: List[ResourceItem]
    key: Optional[str]
    type: Optional[str]

    @classmethod
    def from_kw(cls, **kw):
        urls = kw.get('urls', [])
        files = kw.get('files', [])
        outfile = kw.get('outfile')
        stores = kw.get('stores', [])
        items = kw.get('items', [])
        key = kw.get('key', None)
        type = kw.get('type', None)
        return cls(urls, files, outfile, stores, items, key, type)
