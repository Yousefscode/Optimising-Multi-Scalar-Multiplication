"""
Pippenger's algorithm for multi-scalar multiplication.

This is the bucket method with the window width chosen from the input size,
c ~ log2(n), which is what gives Pippenger its O(b * n / log n) asymptotic
cost. Only non-empty buckets are stored (a dict), which matters when 2^c is
large relative to n.

References: N. Pippenger, "On the evaluation of powers and monomials" (1980);
R. Henry, "Pippenger's Multiproduct and Multiexponentiation Algorithms",
CACR technical report (2010).
"""

import math

from .curve_utils import add, naive_msm


def _window_size_for(n):
    return max(2, round(math.log2(n)))


def pippenger(scalars, points, c=None):
    """
    Pippenger MSM.

    Args:
        scalars: list of integer scalars
        points:  list of ECPy points
        c: window width in bits (default: max(2, round(log2 n)))

    Returns:
        sum a_i * P_i, or ``None`` for the point at infinity.
    """
    pairs = [(s, p) for s, p in zip(scalars, points) if s != 0]
    if not pairs:
        return None
    if len(pairs) == 1:
        return pairs[0][1] * pairs[0][0]

    if c is None:
        c = _window_size_for(len(pairs))

    max_bits = max(s.bit_length() for s, _ in pairs)
    if max_bits <= c:
        # A single window: buckets would cost more than direct multiplication.
        return naive_msm([s for s, _ in pairs], [p for _, p in pairs])

    num_windows = (max_bits + c - 1) // c
    mask = (1 << c) - 1

    result = None
    for i in range(num_windows - 1, -1, -1):
        if result is not None:
            for _ in range(c):
                result = result + result

        buckets = {}
        for scalar, point in pairs:
            v = (scalar >> (i * c)) & mask
            if v:
                buckets[v] = add(buckets.get(v), point)

        # Weighted sum  sum_v v * B_v  via the running-sum trick over the
        # occupied bucket indices, from highest to lowest. Gaps between
        # occupied indices are bridged by adding the running sum once per
        # skipped index.
        running = None
        window_sum = None
        occupied = sorted(buckets, reverse=True)
        for k, v in enumerate(occupied):
            running = add(running, buckets[v])
            next_v = occupied[k + 1] if k + 1 < len(occupied) else 0
            for _ in range(v - next_v):
                window_sum = add(window_sum, running)

        result = add(result, window_sum)

    return result


def pippenger_input_partitioning(scalars, points, chunk_size=None):
    """
    Pippenger with input partitioning: split the n inputs into chunks of
    ``chunk_size``, solve each chunk with :func:`pippenger`, and add the
    partial results.

    Args:
        scalars, points: as in :func:`pippenger`
        chunk_size: inputs per chunk (default: max(2, round(log2 n)))
    """
    pairs = [(s, p) for s, p in zip(scalars, points) if s != 0]
    if not pairs:
        return None

    if chunk_size is None:
        chunk_size = _window_size_for(len(pairs))

    result = None
    for start in range(0, len(pairs), chunk_size):
        chunk = pairs[start:start + chunk_size]
        partial = pippenger([s for s, _ in chunk], [p for _, p in chunk], c=chunk_size)
        result = add(result, partial)
    return result
