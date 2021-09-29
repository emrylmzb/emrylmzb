"""
Contains implementation of square area class with base useful methods.
"""
from adboox.geolib.tools.geocircle import GeoCircle
from adboox.geolib.tools.geopoint import GeoPoint


class Area(object):
    """
    Describes 'square' area on the Earth surface, laying between two
    corners - left down corner and upper right.

    """
    def __init__(self, p1, p2):
        """
        :param p1: left down corner
        :type p1: GeoPoint
        :param p2: upper right corner
        :type p2: GeoPoint
        """

        self.p1 = GeoPoint(min(p1.lat, p2.lat), min(p1.lng, p2.lng))
        self.p2 = GeoPoint(max(p1.lat, p2.lat), max(p1.lng, p2.lng))

    def contains_point(self, p):
        """
        :param p: point to check
        :type p: GeoPoint
        :return: True if point is within area
        """

        if p.lat < self.p1.lat:
            return False

        if p.lat > self.p2.lat:
            return False

        if p.lng < self.p1.lng:
            return False

        if p.lng > self.p2.lng:
            return False

        return True

    def intersects_circle(self, circle):
        """
        This method is not mathematically strict.
        It assumes that the circle intersects
        with the area, if circumcircle, extended to
        circle.radius, around the area contains the
        center of given circle.

        :param circle: circle to check
        :type circle: GeoCircle
        :return: True if this area intersects given circle
        """
        circum_circle = GeoCircle(
            (self.p2.lat + self.p1.lat) / 2, (self.p1.lng + self.p2.lng) / 2,
            self.p1.distance(self.p2) / 2 + circle.radius)

        return circum_circle.contains_point(circle)
