"""
Bos-Coster algorithm for multi-scalar multiplication.

Repeatedly takes the two largest scalars a1 >= a2 and rewrites
    a1*P1 + a2*P2  =  (a1 - a2)*P1 + a2*(P1 + P2)
until a single (scalar, point) pair is left, then finishes with one scalar
multiplication.

Reference: D.J. Bernstein, J. Doumen, T. Lange, J.-J. Oosterwijk,
"Faster Batch Forgery Identification" (INDOCRYPT 2012).
"""


def bos_coster(scalars, points):
    """
    Bos-Coster MSM that re-sorts the working list after every step.

    Args:
        scalars: list of integer scalars [a1, ..., an]
        points:  list of ECPy points [P1, ..., Pn]

    Returns:
        a1*P1 + ... + an*Pn, or ``None`` for the point at infinity.
    """
    pairs = [(s, p) for s, p in zip(scalars, points) if s != 0]
    if not pairs:
        return None

    pairs.sort(key=lambda pair: pair[0], reverse=True)

    while len(pairs) > 1:
        a1, P1 = pairs[0]
        a2, P2 = pairs[1]
        if a1 == a2:
            pairs = pairs[2:] + [(a1, P1 + P2)]
        else:
            pairs = pairs[2:] + [(a1 - a2, P1), (a2, P1 + P2)]
        pairs.sort(key=lambda pair: pair[0], reverse=True)

    final_scalar, final_point = pairs[0]
    return final_point * final_scalar


def bos_coster_efficient(scalars, points):
    """
    Bos-Coster MSM that keeps the list ordered with insertion instead of
    re-sorting the whole list each iteration.

    Same arguments and return value as :func:`bos_coster`.
    """
    heap = sorted(((s, p) for s, p in zip(scalars, points) if s != 0),
                  key=lambda pair: pair[0], reverse=True)
    if not heap:
        return None

    def insert(pair):
        pos = 0
        while pos < len(heap) and heap[pos][0] > pair[0]:
            pos += 1
        heap.insert(pos, pair)

    while len(heap) > 1:
        (a1, P1), (a2, P2) = heap[0], heap[1]
        del heap[:2]
        P1_plus_P2 = P1 + P2
        if a1 > a2:
            insert((a1 - a2, P1))
        insert((a2, P1_plus_P2))

    final_scalar, final_point = heap[0]
    return final_point * final_scalar
