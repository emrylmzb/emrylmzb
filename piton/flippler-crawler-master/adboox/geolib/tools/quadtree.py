"""
Contains base class for data structures based on quad tree.
"""
from adboox.geolib.tools.area import Area
from adboox.geolib.tools.geopoint import GeoPoint


class GenericGeoQuadTree(Area):
    """
    Base class for data structures based on quad tree.
    """

    def __init__(self, p1, p2, max_level, level=0):
        super(GenericGeoQuadTree, self).__init__(p1, p2)
        self._subtrees = []
        self.level = level
        self.max_level = max_level

    @property
    def nw(self):
        """
        North-West quarter of map (submap)
        """
        return self._subtrees[0] or None

    @property
    def ne(self):
        """
        North-East quarter of map (submap)
        """
        return self._subtrees[1] or None

    @property
    def sw(self):
        """
        South-West quarter of map (submap)
        """
        return self._subtrees[2] or None

    @property
    def se(self):
        """
        South-East quarter of map (submap)
        """
        return self._subtrees[3] or None

    def _instantiate_subtree(self, *args, **kwargs):
        """
        'Magic' method that creates a subtree for current
        tree, that has the same class as current.
        """
        subtree = GenericGeoQuadTree.__new__(self.__class__)
        subtree.__init__(*args, **kwargs)
        return subtree

    def make_subtrees(self):
        """
        Calculates mid-point of current map, divides the square
         in to 4 parts and makes a subtree for each of them.
        """
        if len(self._subtrees) > 0:
            assert len(self._subtrees) == 4
            return

        midpoint = GeoPoint((self.p2.lat + self.p1.lat) / 2.0,
                            (self.p2.lng + self.p1.lng) / 2.0)
        mk = self._instantiate_subtree

        self._subtrees.append(
            mk(GeoPoint(midpoint.lat, self.p1.lng),
               GeoPoint(self.p2.lat, midpoint.lng),
               level=self.level + 1))  # 0

        self._subtrees.append(
            mk(midpoint,
               self.p2,
               level=self.level + 1))  # 1

        self._subtrees.append(
            mk(self.p1,
               midpoint,
               level=self.level + 1))  # 2

        self._subtrees.append(
            mk(
                GeoPoint(self.p1.lat, midpoint.lng),
                GeoPoint(midpoint.lat, self.p2.lng),
                level=self.level + 1))  # 3
