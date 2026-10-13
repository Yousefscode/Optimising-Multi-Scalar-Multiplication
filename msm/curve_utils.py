"""
Elliptic-curve helpers shared by every MSM algorithm.

All algorithms use ``None`` to represent the point at infinity (the group
identity), so ``add`` below is the one place that convention is handled.
"""

import random
from contextlib import contextmanager

from ecpy.curves import Curve, Point


def get_curve(name="secp256k1"):
    """Return a named ECPy curve (default: secp256k1)."""
    return Curve.get_curve(name)


def add(P, Q):
    """Add two points, treating ``None`` as the point at infinity."""
    if P is None:
        return Q
    if Q is None:
        return P
    return P + Q


def random_scalar(order, bits=None):
    """Random scalar in [1, order-1], optionally capped at ``bits`` bits."""
    if bits is None:
        return random.randint(1, order - 1)
    return random.randint(1, min(order - 1, 2**bits - 1))


def generate_test_case(curve, n, scalar_bits=None):
    """Generate ``n`` random points and ``n`` random scalars on ``curve``."""
    G = curve.generator
    points = [G * random_scalar(curve.order) for _ in range(n)]
    scalars = [random_scalar(curve.order, scalar_bits) for _ in range(n)]
    return scalars, points


def naive_msm(scalars, points):
    """Reference MSM: compute each a_i * P_i separately and sum them."""
    result = None
    for scalar, point in zip(scalars, points):
        if scalar == 0 or point is None:
            continue
        result = add(result, point * scalar)
    return result


@contextmanager
def count_operations():
    """
    Count elliptic-curve point operations performed inside the ``with`` block.

    Additions of a point to itself are counted as doublings. Calls to
    ``Point.__mul__`` (used by Bos-Coster's final step and the naive
    reference) are charged as a double-and-add: ``bit_length - 1`` doublings
    plus ``popcount - 1`` additions.

    Usage::

        with count_operations() as ops:
            pippenger(scalars, points)
        print(ops["additions"], ops["doublings"])
    """
    stats = {"additions": 0, "doublings": 0}
    original_add, original_mul = Point.__add__, Point.__mul__
    depth = {"mul": 0}

    def counting_add(self, other):
        if depth["mul"] == 0 and other is not None:
            if self == other:
                stats["doublings"] += 1
            else:
                stats["additions"] += 1
        return original_add(self, other)

    def counting_mul(self, scalar):
        if depth["mul"] == 0 and scalar > 0:
            stats["doublings"] += scalar.bit_length() - 1
            stats["additions"] += bin(scalar).count("1") - 1
        depth["mul"] += 1
        try:
            return original_mul(self, scalar)
        finally:
            depth["mul"] -= 1

    Point.__add__, Point.__mul__ = counting_add, counting_mul
    try:
        yield stats
    finally:
        Point.__add__, Point.__mul__ = original_add, original_mul
