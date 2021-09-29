"""
Contains representation of a circle on the globe.
"""

from adboox.geolib.tools.geopoint import GeoPoint


class GeoCircle(GeoPoint):
    """
    Represents a circle on the globe, with latitude, longitude and radius (in km).
    Usually, in location crawling, we search for stores within a circle
    around some geo point and radius.
    """

    def __init__(self, lat, lng, radius):
        super(GeoCircle, self).__init__(lat, lng)
        self.radius = radius

    def contains_point(self, p):
        """
        Returns true, if the circle contains given point
        """
        return self.distance(p) <= self.radius

    def intersects_area(self, area):
        """
        Returns true, if the circle intercects area
        """
        return area.intersects_circle(self)

    def step(self, dlat, dlon):
        """
        Returns the new circle, with center in point on the globe, that is
        away from current in delta latitude and delta longitude, both in km.
        """
        p = super(GeoCircle, self).step(dlat, dlon)
        return GeoCircle(p.lat, p.lng, self.radius)
