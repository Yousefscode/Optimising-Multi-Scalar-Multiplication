"""
Multi-scalar multiplication (MSM) algorithms on elliptic curves.

Computes  a1*P1 + a2*P2 + ... + an*Pn  with several classic algorithms so
they can be compared on operation count, time and memory.
"""

from .bos_coster import bos_coster, bos_coster_efficient
from .bucketing import bucketing, comb_bucketing, interleaved_bucketing
from .curve_utils import count_operations, generate_test_case, get_curve, naive_msm
from .pippenger import pippenger, pippenger_input_partitioning

ALGORITHMS = {
    "Bos-Coster": bos_coster,
    "Bos-Coster (Efficient)": bos_coster_efficient,
    "Bucketing": bucketing,
    "Bucketing (Interleaved)": interleaved_bucketing,
    "Comb-Bucketing": comb_bucketing,
    "Pippenger": pippenger,
    "Pippenger (Input Partitioning)": pippenger_input_partitioning,
}

__all__ = [
    "ALGORITHMS",
    "bos_coster",
    "bos_coster_efficient",
    "bucketing",
    "interleaved_bucketing",
    "comb_bucketing",
    "pippenger",
    "pippenger_input_partitioning",
    "naive_msm",
    "get_curve",
    "generate_test_case",
    "count_operations",
]
