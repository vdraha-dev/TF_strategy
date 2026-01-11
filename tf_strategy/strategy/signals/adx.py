from typing import NamedTuple

import numpy as np
from scipy.signal import lfilter

__all__ = ["adx", "adx_update", "AdxIncremental", "AdxBatch"]


class AdxIncremental(NamedTuple):
    adx: float
    trs: float
    pdms: float
    mdms: float


class AdxBatch(NamedTuple):
    adx: np.ndarray
    trs: np.ndarray
    pdms: np.ndarray
    mdms: np.ndarray


def __wilder_smoothing(data: np.ndarray, period: int):
    """
    Apply Wilder's smoothing to data.

    Parameters
    ----------
    data : np.ndarray
        Input data
    period : int
        Smoothing period

    Returns
    -------
    np.ndarray
        Smoothed values. First period-1 values are NaN.
    """
    coef = (period - 1) / period
    result = np.full_like(data, np.nan)

    result[period - 1 :], _ = lfilter(
        b=[1.0 / period],
        a=[1.0, -coef],
        x=data[period - 1 :],
        zi=[data[:period].mean() * coef],
    )

    return result


def adx(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int) -> AdxBatch:
    """
    Calculate Average Directional Index (ADX).

    ADX measures trend strength (not direction) from 0 to 100:
    - 0-25: Weak or no trend
    - 25-50: Strong trend
    - 50-75: Very strong trend
    - 75-100: Extremely strong trend

    Parameters
    ----------
    high : np.ndarray
        High prices
    low : np.ndarray
        Low prices
    close : np.ndarray
        Close prices
    period : int, default 14
        ADX calculation period

    Returns
    -------
    np.ndarray
        ADX values. First 2*period-1 values are 0 or unreliable.
    """
    # True Range
    tr = np.zeros_like(high)
    tr[0] = high[0] - low[0]
    tr[1:] = np.maximum(
        high[1:] - low[1:],
        np.maximum(
            np.abs(high[1:] - close[:-1]),
            np.abs(low[1:] - close[:-1]),
        ),
    )

    # Directional movements
    upmove = np.zeros_like(high)
    downmove = np.zeros_like(high)

    upmove[1:] = high[1:] - high[:-1]
    downmove[1:] = low[:-1] - low[1:]

    pdm = np.where((upmove > downmove) & (upmove > 0), upmove, 0)
    mdm = np.where((downmove > upmove) & (downmove > 0), downmove, 0)

    # Update smoothed TR
    trs = __wilder_smoothing(tr, period)

    # Update smoothed DM
    pdms = __wilder_smoothing(pdm, period)
    mdms = __wilder_smoothing(mdm, period)

    # Calculate DI
    pdi = np.divide(pdms, trs, out=np.full_like(trs, np.nan), where=trs != 0) * 100
    mdi = np.divide(mdms, trs, out=np.full_like(trs, np.nan), where=trs != 0) * 100

    # Calculate DX
    di_sum = pdi + mdi
    dx = (
        np.divide(
            np.abs(pdi - mdi),
            di_sum,
            out=np.full_like(di_sum, np.nan),
            where=di_sum != 0,
        )
        * 100
    )

    # Calculate ADX
    adx_values = np.full_like(dx, np.nan)
    adx_values[2 * period - 1 :] = __wilder_smoothing(dx[period - 1 :], period)[period:]

    return AdxBatch(adx=adx_values, trs=trs, pdms=pdms, mdms=mdms)


def adx_update(
    high: float,
    prev_high: float,
    low: float,
    prev_low: float,
    prev_close: float,
    last_adx: float,
    last_trs: float,
    last_pdms: float,
    last_mdms: float,
    period: int,
) -> AdxIncremental:
    """
    Update ADX incrementally with new price bar.

    Parameters
    ----------
    high : float
        Current bar's high price
    prev_high : float
        Previous bar's high price
    low : float
        Current bar's low price
    prev_low : float
        Previous bar's low price
    prev_close : float
        Previous bar's close price
    last_adx : float
        Last ADX value
    last_trs : float
        Last smoothed True Range
    last_pdms : float
        Last smoothed +DM
    last_mdms : float
        Last smoothed -DM
    period : int, default 14
        ADX period

    Returns
    -------
    ADXIncremental
        NamedTuple with updated values: adx, trs, pdms, mdms
    """
    # True Range
    tr = max(high - low, abs(high - prev_close), abs(low - prev_close))

    rperiod = 1 / period

    # Wilder's smoothing coefficient
    coef = (period - 1) * rperiod

    # Update smoothed TR
    trs = last_trs * coef + tr * rperiod

    # Directional movements
    upmove = high - prev_high
    downmove = prev_low - low

    pdm = upmove if (upmove > downmove and upmove > 0) else 0
    mdm = downmove if (downmove > upmove and downmove > 0) else 0

    # Update smoothed DM
    pdms = last_pdms * coef + pdm * rperiod
    mdms = last_mdms * coef + mdm * rperiod

    # Calculate DI
    if trs == 0:
        return AdxIncremental(adx=np.nan, trs=trs, pdms=pdms, mdms=mdms)

    pdi = 100 * pdms / trs
    mdi = 100 * mdms / trs

    # Calculate DX
    di_sum = pdi + mdi
    dx = 0 if di_sum == 0 else 100 * abs(pdi - mdi) / di_sum

    adx = last_adx * coef + dx * rperiod

    return AdxIncremental(adx=adx, trs=trs, pdms=pdms, mdms=mdms)
