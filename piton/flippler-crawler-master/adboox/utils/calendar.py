def import_non_local(name, custom_name=None):
    import imp, sys

    custom_name = custom_name or name
    f, pathname, desc = imp.find_module(name, sys.path[1:])
    module = imp.load_module(custom_name, f, pathname, desc)
    f.close()
    return module

std_calendar = import_non_local('calendar', 'std_calendar')
from collections import OrderedDict
from copy import copy


def _set_od(od, pairs, reverse=False):
    for k, v in pairs:
        if reverse:
            od[v] = k
        else:
            od[k] = v


day_to_abbr = OrderedDict()
pairs_en = [('Monday', 'mo'), ('Tuesday', 'tu'), ('Wednesday', 'we'), ('Thursday', 'th'),
            ('Friday', 'fr'), ('Saturday', 'sa'), ('Sunday', 'su')]
_set_od(day_to_abbr, pairs_en)

pairs_de = [('Monday', 'mo'), ('Tuesday', 'di'), ('Wednesday', 'mi'), ('Thursday', 'do'),
            ('Friday', 'fr'), ('Saturday', 'sa'), ('Sunday', 'so')]
day_to_abbr_de = OrderedDict()
_set_od(day_to_abbr_de, pairs_de)


pairs_day_de = [('Montag', 'mo'), ('Dienstag', 'tu'), ('Mittwoch', 'we'), ('Donnerstag', 'th'),
                ('Freitag', 'fr'), ('Samstag', 'sa'), ('Sonntag', 'su')]
de_day_to_abbr = OrderedDict()
_set_od(de_day_to_abbr, pairs_day_de)

abbr_to_day = OrderedDict()
_set_od(abbr_to_day, day_to_abbr.items(), True)

abbr_to_day_de = OrderedDict()
_set_od(abbr_to_day_de, day_to_abbr_de.items(), True)

abbr_to_day_mixed = copy(abbr_to_day)
abbr_to_day_mixed.update(abbr_to_day_de)


def iter_from_abbr(from_day, to_day, abbr2day):
    abbrs = list(abbr2day.keys())
    start = abbrs.index(from_day)
    end = abbrs.index(to_day) + 1
    for d in abbrs[start:end]:
        yield d, abbr2day[d]


def iter_from_abbr_de(from_day, to_day):
    return iter_from_abbr(from_day, to_day, abbr_to_day_de)


def iter_from_abbr_en(from_day, to_day):
    return iter_from_abbr(from_day, to_day, abbr_to_day)


def get_en_month_names():
    return get_month_names('en_US.UTF-8')


def get_de_month_names():
    return get_month_names('de_DE.UTF-8')


def get_month_names(locale):
    with std_calendar.TimeEncoding(locale) as encoding:
        names = [mn for mn in std_calendar.month_name if mn]
        return [name.decode(encoding) for name in names]
