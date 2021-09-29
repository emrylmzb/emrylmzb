from lxml import etree
from scrapy.utils.misc import arg_to_iter

_XPATH_FUNCS = {}
_HASCLASS_EXPR = 'contains(concat(" ", @class, " "), " {} ")'
_HEADINGS = ['h{}'.format(x) for x in range(1, 7)]


def register(func):
    fname = func.__name__.replace('_', '-')
    _XPATH_FUNCS[fname] = func
    return func


def setup():
    fns = etree.FunctionNamespace(None)
    for name, func in _XPATH_FUNCS.items():
        fns[name] = func


@register
def lower_case(context, s):
    """Native lowercase function."""
    sl = arg_to_iter(s)
    return [s.lower() for s in sl]


@register
def upper_case(context, s):
    """Native uppercase function."""
    sl = arg_to_iter(s)
    return [s.upper() for s in sl]


@register
def has_class(context, *classes):
    """has-class function."""
    expr = ' and '.join([_HASCLASS_EXPR.format(cls) for cls in classes])
    xpath = 'self::*[%s]' % expr
    return bool(context.context_node.xpath(xpath))


@register
def is_heading(context):
    return context.context_node.tag in _HEADINGS
