import pkgutil
import random
from io import StringIO


def gen_random_digits(digits, prefix=''):
    selection = range(0, 10)
    return prefix + ''.join([str(random.choice(selection)) for _ in range(digits - len(prefix))])


def load_csv_data(name):
    data = pkgutil.get_data('adboox', 'data/{}'.format(name))
    sio = StringIO(data.decode('utf-8'))
    keys = next(sio).split(';')
    return [dict(zip(keys, line.strip().split(';'))) for line in sio.readlines()]

de_cities = set([x['CityName'] for x in load_csv_data('de_cities.csv')])
