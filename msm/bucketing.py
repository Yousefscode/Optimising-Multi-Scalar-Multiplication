"""
Bucket-method multi-scalar multiplication.

Each scalar is split into fixed-width windows. Within a window, every point is
dropped into the bucket matching its window value v, and the window's
contribution is  sum_v v * B_v.  That weighted sum is computed with the
running-sum trick (2 additions per bucket, no scalar multiplications):

    running = B_max ;  total = running
    running += B_{max-1} ;  total += running
    ...

Windows are combined from most to least significant with w doublings between
them (Horner's rule).
"""

from .curve_utils import add


def weighted_bucket_sum(buckets):
    """
    Return sum_{v=1}^{len-1} v * buckets[v] using the running-sum trick.

    ``buckets[v]`` may be ``None`` (empty bucket). Empty buckets must still
    contribute the current running sum, otherwise every lower bucket loses
    weight.
    """
    running = None
    total = None
    for v in range(len(buckets) - 1, 0, -1):
        running = add(running, buckets[v])
        total = add(total, running)
    return total


def _double(P, times):
    for _ in range(times):
        if P is None:
            return None
        P = P + P
    return P


def _fill_buckets(pairs, shift, window_size):
    buckets = [None] * (1 << window_size)
    mask = (1 << window_size) - 1
    for scalar, point in pairs:
        v = (scalar >> shift) & mask
        if v:
            buckets[v] = add(buckets[v], point)
    return buckets


def bucketing(scalars, points, window_size=4):
    """
    Basic bucket method: process windows from the most significant end,
    filling and summing one window's buckets at a time.

    Args:
        scalars: list of integer scalars
        points:  list of ECPy points
        window_size: bits per window (w)

    Returns:
        sum a_i * P_i, or ``None`` for the point at infinity.
    """
    pairs = [(s, p) for s, p in zip(scalars, points) if s != 0]
    if not pairs:
        return None

    max_bits = max(s.bit_length() for s, _ in pairs)
    num_windows = (max_bits + window_size - 1) // window_size

    result = None
    for i in range(num_windows - 1, -1, -1):
        result = _double(result, window_size)
        buckets = _fill_buckets(pairs, i * window_size, window_size)
        result = add(result, weighted_bucket_sum(buckets))
    return result


def interleaved_bucketing(scalars, points, window_size=4):
    """
    Bucket method that first builds the buckets for every window, then
    combines the window sums with Horner's rule.

    Same arguments and return value as :func:`bucketing`.
    """
    pairs = [(s, p) for s, p in zip(scalars, points) if s != 0]
    if not pairs:
        return None

    max_bits = max(s.bit_length() for s, _ in pairs)
    num_windows = (max_bits + window_size - 1) // window_size

    window_sums = [weighted_bucket_sum(_fill_buckets(pairs, i * window_size, window_size))
                   for i in range(num_windows)]

    result = None
    for i in range(num_windows - 1, -1, -1):
        result = _double(result, window_size)
        result = add(result, window_sums[i])
    return result


def comb_bucketing(scalars, points, window_size=4, comb_count=2):
    """
    Comb + bucket method.

    The scalar is cut into ``comb_count`` equal "teeth" of ``L`` bits.
    Each point P is replaced by shifted copies  2^(j*L) * P  (one per tooth),
    so a single pass over L bits handles every tooth at once and only
    L doublings of the accumulator are needed instead of max_bits.

    The shifted copies cost (comb_count - 1) * L doublings per point. In a
    fixed-base setting these are precomputed once and reused; here they are
    computed (and counted) on every call so the comparison stays like-for-like.

    Args:
        scalars, points: as in :func:`bucketing`
        window_size: bits per window within a tooth
        comb_count: number of teeth

    Returns:
        sum a_i * P_i, or ``None`` for the point at infinity.
    """
    pairs = [(s, p) for s, p in zip(scalars, points) if s != 0]
    if not pairs:
        return None

    max_bits = max(s.bit_length() for s, _ in pairs)
    tooth_bits = (max_bits + comb_count - 1) // comb_count
    tooth_mask = (1 << tooth_bits) - 1

    # Split every scalar into teeth and pair each tooth with its shifted point.
    expanded = []
    for scalar, point in pairs:
        shifted = point
        for j in range(comb_count):
            piece = (scalar >> (j * tooth_bits)) & tooth_mask
            if piece:
                expanded.append((piece, shifted))
            if j < comb_count - 1:
                shifted = _double(shifted, tooth_bits)

    num_windows = (tooth_bits + window_size - 1) // window_size
    result = None
    for i in range(num_windows - 1, -1, -1):
        result = _double(result, window_size)
        buckets = _fill_buckets(expanded, i * window_size, window_size)
        result = add(result, weighted_bucket_sum(buckets))
    return result
