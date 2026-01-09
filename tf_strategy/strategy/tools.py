import numpy as np


def crossed_above(fast, slow) -> np.ndarray:
    out = np.zeros_like(fast, dtype=bool)
    out[1:] = (fast[1:] >= slow[1:]) & (fast[:-1] < slow[:-1])
    return out


def crossed_below(fast, slow) -> np.ndarray:
    out = np.zeros_like(fast, dtype=bool)
    out[1:] = (fast[1:] < slow[1:]) & (fast[:-1] >= slow[:-1])
    return out
