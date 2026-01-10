import numpy as np


def crossed_above(fast, slow) -> np.ndarray:
    """
    Detect where fast line crosses above slow line.

    Returns a boolean array where True indicates a crossover point
    (fast line transitions from below to above/equal the slow line).

    Args
    ----------
    fast : np.ndarray
        Fast line (e.g., short moving average)
    slow : np.ndarray
        Slow line (e.g., long moving average)

    Returns
    -------
    np.ndarray
        Boolean array of same shape. First element is always False.
    """
    out = np.zeros_like(fast, dtype=bool)
    out[1:] = (fast[:-1] < slow[:-1]) & (fast[1:] >= slow[1:])
    return out


def crossed_below(fast, slow) -> np.ndarray:
    """
    Detect where fast line crosses below slow line.

    Returns a boolean array where True indicates a crossunder point
    (fast line transitions from above to below/equal the slow line).

    Args
    ----------
    fast : np.ndarray
        Fast line (e.g., short moving average)
    slow : np.ndarray
        Slow line (e.g., long moving average)

    Returns
    -------
    np.ndarray
        Boolean array of same shape. First element is always False.
    """
    out = np.zeros_like(fast, dtype=bool)
    out[1:] = (fast[:-1] > slow[:-1]) & (fast[1:] <= slow[1:])
    return out
