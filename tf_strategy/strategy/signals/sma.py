import numpy as np


def sma_numpy(price: np.ndarray, period: int) -> np.ndarray:
    """
    Compute Simple Moving Average (SMA) over a given period using NumPy convolution.

    Args:
        price (np.ndarray): Array of price values.
        period (int): The period of the SMA.

    Returns:
        np.ndarray: Array of SMA values. The first `period-1` elements are NaN.
    """
    out = np.full_like(price, np.nan, dtype=float)
    if period > len(price):
        return out
    weights = np.ones(period) / period
    out[period - 1 :] = np.convolve(price, weights, mode="valid")
    return out


def sma_update(
    new_price: float, leave_price: float, last_sma_value: float, period: int
) -> float:
    """
    Incrementally update the last SMA value with a new price in realtime.

    Formula:
        SMA_t = SMA_{t-1} + (P_t - P_{t-period}) / period

    Args:
        new_price (float): The latest price to include in SMA.
        leave_price (float): The price leaving the SMA period (oldest price).
        last_sma_value (float): The previous SMA value.
        period (int): The SMA period.

    Returns:
        float: Updated SMA value.
    """
    return last_sma_value + (new_price - leave_price) / period
