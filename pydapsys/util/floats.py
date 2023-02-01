from __future__ import annotations

import sys


def float_comp(f1: float, f2: float, epsilon=sys.float_info.epsilon) -> bool:
    """
    Checks if two floats are equal enough
    :param f1: Value 1
    :param f2: Value 2
    :param epsilon: Value used for check
    :return: abs(f1-f2) <= epsilon
    """
    return abs(f1 - f2) <= epsilon
