from adboox.geolib.tools.geocircle import GeoCircle


class GeoCircleWithMeta(GeoCircle):
    """
    Geocircle with additional attribute meta (default = None).
    You can store whatever you want there
    """

    def __init__(self, lat, lng, radius, meta=None):
        super(GeoCircleWithMeta, self).__init__(lat, lng, radius)
        self.meta = meta


class LocationIterator(object):
    """
    Iterator yielding locations, iterating through the
     quad map and quad index of some territory.
    """

    def __init__(self, quad_tree, quad_index, radius):
        self.radius = radius
        self.quad_tree = quad_tree
        self.quad_index = quad_index

    def __iter__(self):
        circle = GeoCircleWithMeta(self.quad_tree.p1.lat,
                                   self.quad_tree.p1.lng,
                                   self.radius)
        while True:
            if self.quad_tree.filled_at_circle_edge(circle):
                circle.meta = self.quad_index.search(circle).meta
                yield circle
                circle = circle.step(self.radius, 0)
            else:
                circle = circle.step(self.radius / 10.0, 0)

            if circle.lat > self.quad_tree.p2.lat:
                circle.lat = self.quad_tree.p1.lat
                circle = circle.step(0, self.radius)
            if circle.lng > self.quad_tree.p2.lng:
                break
