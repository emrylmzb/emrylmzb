"""
Contains implementation of quad tee data structure
 (http://en.wikipedia.org/wiki/Quadtree)
"""
from math import pi, sin, cos
from adboox.geolib.tools.geopoint import GeoPoint
from adboox.geolib.tools.quadtree import GenericGeoQuadTree


class GeoQuadMap(GenericGeoQuadTree):
    """
    Implementation of quad tee data structure
     (http://en.wikipedia.org/wiki/Quadtree)
     in order to  store map, formed from circles
     around some points, known to be part of a territory.
    """
    def __init__(self, p1, p2, level=0, max_level=8):
        super(GeoQuadMap, self).__init__(p1, p2, max_level, level=level)
        self.full = False

    def draw_circle(self, circle):
        """
        Draws a circle on a map, marking
        contents within the circle as filled.
        """
        if self.full:
            return

        if reduce(lambda a, b: a and b,
                  [s.full for s in self._subtrees],
                  len(self._subtrees) > 0):

            self.set_full()
            return

        p1 = self.p1
        p2 = self.p2
        p3 = GeoPoint(p1.lat, p2.lng)
        p4 = GeoPoint(p2.lat, p1.lng)

        box_in_circle = True
        for p in [p1, p2, p3, p4]:
            if not circle.contains_point(p):
                box_in_circle = False
                break

        if box_in_circle:
            self.set_full()
            return

        box_has_part_of_circle = self.intersects_circle(circle)

        if self.level == self.max_level and box_has_part_of_circle:
            self.set_full()
            return

        if box_has_part_of_circle:
            self.make_subtrees()
            for subtree in self._subtrees:
                subtree.draw_circle(circle)

    def circle_adds_area(self, circle):
        """
        Checks if this circle will
        change somethign when drawn.
        """
        if self.full:
            return False

        if len(self._subtrees) > 0:
            for subtree in self._subtrees:
                if subtree.circle_adds_area(circle):
                    return True

        return self.intersects_circle(circle)

    def filled_at(self, point):
        """
        Checks if the map is filled at given point
        """
        if self.full:
            return True

        if not self.contains_point(point):
            return False

        for subtree in self._subtrees:
            if subtree.filled_at(point):
                return True

        return False

    def visualize(self, x, y, width, height, draw_function):
        """
        Visualizes the map via calling user defined
        draw_function(x, y, width, height)
        for each filled part of map.
        """
        if self.full:
            draw_function(x, y, width, height)
            return

        if len(self._subtrees) == 0:
            return

        assert len(self._subtrees) == 4

        half_width = width / 2.0
        half_height = height / 2.0

        mx = x + half_width
        my = y + half_height

        self.nw.visualize(x, y, half_width, half_height, draw_function)
        self.ne.visualize(mx, y, half_width, half_height, draw_function)
        self.sw.visualize(x, my, half_width, half_height, draw_function)
        self.se.visualize(mx, my, half_width, half_height, draw_function)

    def filled_at_circle_edge(self, c):
        """
        Checks if the map is filled at the edge of the circle.
         Actually performs check in 10 points on the circle.
        """
        n = 10
        step = (2.0*pi) / n
        r = c.radius

        for a in range(0, n):
            angle = a * step
            dlat = r * sin(angle)
            dlng = r * cos(angle)
            if self.filled_at(c.step(dlat, dlng)):
                return True
        return False

    def set_full(self):
        """
        Marks current map as totally filled
        """
        self._subtrees = []
        self.full = True
