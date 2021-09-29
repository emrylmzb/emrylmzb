from json import JSONEncoder
from adboox.items import BaseItem


class ItemEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, BaseItem):
            return o.to_dict()
        return super(ItemEncoder, self).default(o)
