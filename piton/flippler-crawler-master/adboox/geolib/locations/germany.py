import re
import logging
import itertools
from collections import namedtuple
from adboox import __version__
from adboox.utils import load_csv_data
from adboox.utils.progress import ProgressTracer
from adboox.geolib.locations import LocationIterator
from adboox.geolib.tools.cache import Cache
from adboox.geolib.tools.geopoint import GeoPoint
from adboox.geolib.tools.geomap import GeoQuadMap
from adboox.geolib.tools.geoindex import GeoQuadIndex
from adboox.geolib.tools.geocircle import GeoCircle
from adboox.geolib.tools import DEFAULT_MAX_RECURSION_LEVEL, DEFAULT_RADIUS_AROUND_ZIPCODE_KM

GermanyInfo = namedtuple('GermanyInfo', ['maps', 'indexes'])
logger = logging.getLogger(__name__)


class GermanyInfoCache(Cache):
    def __init__(self, name=None):
        name = name or 'de_cache_{}'.format(__version__)
        super(GermanyInfoCache, self).__init__(name)

    def make_new(self):
        # points are north-east to south-west
        territories = (
            (r'.*', (GeoPoint(55.036449, 14.735913), GeoPoint(47.214631, 6.298413))),
        )
        maps = {kv[0]: GeoQuadMap(*kv[1], max_level=DEFAULT_MAX_RECURSION_LEVEL)
                for kv in territories}

        indexes = {kv[0]: GeoQuadIndex(*kv[1], max_level=DEFAULT_MAX_RECURSION_LEVEL)
                   for kv in territories}
        territory_keys = [kv[0] for kv in territories]

        def _print_progress(pos, totalsize):
            progress = float(pos) / totalsize * 100.0
            logger.info('Building geo cache %.2f%% is complete.' % progress)

        de_cities = load_csv_data('de_cities.csv')
        tracer = ProgressTracer(len(de_cities), _print_progress, cb_num=20)
        for city in de_cities:
            zipcode = city['PostalCode']
            latitude = float(city['Latitude'])
            longitude = float(city['Longitude'])
            name = city['CityName']
            circle = GeoCircle(latitude, longitude, DEFAULT_RADIUS_AROUND_ZIPCODE_KM)

            for k in territory_keys:
                if not re.match(k, name):
                    continue

                maps[k].draw_circle(circle)
                indexes[k].insert(circle, meta={'zipcode': zipcode})
                tracer.step()
                break

        return GermanyInfo(maps, indexes)


class GermanyLocationIterator(object):
    def __init__(self, radius):
        cache = GermanyInfoCache()

        self.radius = radius
        self.de_info = cache.get()

    def __iter__(self):
        lix = [LocationIterator(self.de_info.maps[k], self.de_info.indexes[k], self.radius)
               for k in self.de_info.maps.keys()]
        return itertools.chain(*lix)
