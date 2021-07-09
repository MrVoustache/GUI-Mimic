from typing import Tuple


class Bezier_curve:

    def __init__(self, start : Tuple[int, int], inter : Tuple[int, int], stop : Tuple[int, int]) -> None:
        self._p0 = start
        self._p1 = inter
        self._p2 = stop
    

    def __call__(self, t : float) -> Tuple[int, int]:
        """
        t must be between 0 and 1 included.
        """
        x = self._p1[0] + (1 - t) ** 2 * (self._p0[0] - self._p1[0]) + t ** 2 * (self._p2[0] - self._p1[0])
        y = self._p1[1] + (1 - t) ** 2 * (self._p0[1] - self._p1[1]) + t ** 2 * (self._p2[1] - self._p1[1])
        return round(x), round(y)


def random_circle_point(start : Tuple[int, int], stop : Tuple[int, int]) -> Tuple[int, int]:
    from random import random
    from math import pi, sin, cos
    angle = (random() - 0.5) * 2 * pi
    vect = ((stop[0] - start[0]) / 2, (stop[1] - start[1]) / 2)
    nvect = (vect[0] * sin(angle) - vect[1] * cos(angle), vect[0] * cos(angle) - vect[1] * sin(angle))
    r = random() * 1.2
    nvect = (nvect[0] * r, nvect[1] * r)
    res = ((start[0] + stop[0]) / 2 + nvect[0], (start[1] + stop[1]) / 2 + nvect[1])
    return round(res[0]), round(res[1])