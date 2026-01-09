import numpy as np
from scipy.signal import lfilter


def ema_scipy(price: np.ndarray, period: int) -> np.ndarray:
    """
    Compute Exponential Moving Average (EMA) using SciPy IIR filter.

    Args:
        price (np.ndarray): Array of price values.
        period (int): EMA period.

    Returns:
        np.ndarray: Array of EMA values. The first `period-1` elements are NaN.
    """
    price = np.asarray(price, dtype=float)
    out = np.full(price.shape, np.nan)

    if period <= 0 or period > price.size:
        return out

    alpha = 2.0 / (period + 1.0)

    # IIR filter coefficients
    b = [alpha]
    a = [1.0, -(1.0 - alpha)]

    # Initial condition = SMA of first `period` prices
    zi = [price[:period].mean() * (1.0 - alpha)]

    filtered, _ = lfilter(b, a, price[period - 1 :], zi=zi)
    out[period - 1 :] = filtered

    return out


def ema_update(new_price: float, last_ema_value: float, alpha: float) -> float:
    """
    Incrementally update EMA with a new price (realtime).

    Formula:
        EMA_new = EMA_last + alpha * (price_new - EMA_last)

    Args:
        new_price (float): The latest price to include in EMA.
        last_ema_value (float): The previous EMA value.
        alpha (float): Smoothing factor (2 / (period + 1)).

    Returns:
        float: Updated EMA value.
    """
    return last_ema_value + alpha * (new_price - last_ema_value)
