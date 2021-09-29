"""
Contains implementation of point on earth surface.
"""
from math import radians, sin, cos, atan2, sqrt, degrees

EARTH_RADIUS_KM = 6371


class GeoPoint(object):
    """
    Represents a point on the globe,
    with latitude and longitude.
    """

    def __init__(self, lat, lng):
        self.lat = lat
        self.lng = lng
        self.lat_rad = radians(lat)
        self.lng_rad = radians(lng)

    def __distance__(self, lat2_rad, lng2_rad):
        """
        see http://gis-lab.info/qa/great-circles.html
        """

        cl1 = cos(self.lat_rad)
        cl2 = cos(lat2_rad)
        sl1 = sin(self.lat_rad)
        sl2 = sin(lat2_rad)
        delta = lng2_rad - self.lng_rad
        c_delta = cos(delta)
        s_delta = sin(delta)

        y = sqrt(pow(cl2*s_delta, 2)+pow(cl1*sl2-sl1*cl2*c_delta, 2))
        x = sl1*sl2+cl1*cl2*c_delta
        return atan2(y, x) * EARTH_RADIUS_KM

    def distance(self, other):
        """
        Calculates distance (in km)
        between this and given points on the globe.
        """
        return self.__distance__(other.lat_rad, other.lng_rad)

    def step(self, dlat, dlon):
        """
        Returns the next point on the globe, making a step
        from current in delta latitude and delta longitude, both in km.
        """
        dlat = degrees(dlat / EARTH_RADIUS_KM)
        dlng = degrees(dlon / EARTH_RADIUS_KM / cos(radians(self.lat)))

        return GeoPoint(lat=self.lat + dlat, lng=self.lng + dlng)
