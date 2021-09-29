"""
Contains implementation of reverse index - from coordinates to metadata.

"""
from collections import deque
from adboox.geolib.tools.geopoint import GeoPoint
from adboox.geolib.tools.quadtree import GenericGeoQuadTree


class GeoPointWithMeta(GeoPoint):
    """
    Geo Point with additional metadata
    """

    def __init__(self, point, meta=None):
        super(GeoPointWithMeta, self).__init__(point.lat, point.lng)
        self.meta = meta


class GeoQuadIndex(GenericGeoQuadTree):
    """
    Contains index of points on the
    globe with associated metadata (usually zipcode)
    """
    def __init__(self, p1, p2, level=0, max_level=8, points_maxlen=None):
        super(GeoQuadIndex, self).__init__(p1, p2, max_level, level)
        self.points = deque(maxlen=points_maxlen)

    def insert(self, p, meta=None):
        """
        Inserts a point to index with given meta
        """
        if self.level < self.max_level:
            self.make_subtrees()

            for subtree in self._subtrees:
                if subtree.contains_point(p):
                    subtree.insert(p, meta)
                    return
        else:
            self.points.append(GeoPointWithMeta(p, meta))

    def _all_points(self):
        result = []
        result.extend(self.points)
        for subtree in self._subtrees:
            result.extend(subtree._all_points())

        return result

    def _search_points_close_to(self, query_p):
        if self.level < self.max_level:

            result = self.points

            for subtree in self._subtrees:
                if subtree.contains_point(query_p):
                    result = subtree._search_points_close_to(query_p)
                    break

            if len(result) > 0:
                return result
            else:
                return self._all_points()

        else:
            return self.points

    def search(self, query_p):
        """
        Returns a single point that is the closest match to
         given query_p. Result contains associated metadata
         in the field `meta`
        """
        candidates = self._search_points_close_to(query_p)

        if not candidates:
            return None

        if len(candidates) == 1:
            return candidates[0]

        best_match = candidates[0]
        for match in candidates:
            if match.distance(query_p) \
                    < best_match.distance(query_p):
                best_match = match

        return best_match

    def _instantiate_subtree(self, *args, **kwargs):
        """
        Override base class' method. Need to pass points_maxlen
        constructor parameter.
        """
        return self.__class__(*args, points_maxlen=self.points.maxlen, **kwargs)
