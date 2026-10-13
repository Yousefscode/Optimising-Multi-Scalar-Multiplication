"""
Every MSM algorithm must return exactly the same point as the naive method.

Run with:  python -m pytest tests/
"""

import random

import pytest

from msm import ALGORITHMS, generate_test_case, get_curve, naive_msm

CURVE = get_curve("secp256k1")

CASES = [
    (1, 32),
    (2, 8),
    (5, 32),
    (10, 16),
    (20, 64),
    (33, 128),
    (12, 256),
]


@pytest.mark.parametrize("name", list(ALGORITHMS))
@pytest.mark.parametrize("n,bits", CASES)
def test_matches_naive(name, n, bits):
    random.seed(f"{name}-{n}-{bits}")
    scalars, points = generate_test_case(CURVE, n, bits)
    assert ALGORITHMS[name](scalars, points) == naive_msm(scalars, points)


@pytest.mark.parametrize("name", list(ALGORITHMS))
def test_zero_scalars_are_ignored(name):
    random.seed(7)
    scalars, points = generate_test_case(CURVE, 6, 32)
    scalars[1] = scalars[4] = 0
    assert ALGORITHMS[name](scalars, points) == naive_msm(scalars, points)


@pytest.mark.parametrize("name", list(ALGORITHMS))
def test_all_zero_returns_infinity(name):
    _, points = generate_test_case(CURVE, 4, 16)
    assert ALGORITHMS[name]([0, 0, 0, 0], points) is None


@pytest.mark.parametrize("name", list(ALGORITHMS))
def test_repeated_scalars(name):
    random.seed(11)
    _, points = generate_test_case(CURVE, 6, 32)
    scalars = [12345] * 6
    assert ALGORITHMS[name](scalars, points) == naive_msm(scalars, points)
