from typing import NamedTuple

import numpy as np

from .sma import sma_numpy, sma_update


class RsiIncremental(NamedTuple):
    rsi: float
    gain: float
    loss: float


class RsiBatch(NamedTuple):
    rsi: np.ndarray
    avg_gain: np.ndarray
    avg_loss: np.ndarray

    def update(self, incremental: RsiIncremental):
        self.rsi = np.concatenate(self.rsi, [incremental.rsi])
        self.avg_gain = np.concatenate(self.avg_gain, [incremental.gain])
        self.avg_loss = np.concatenate(self.avg_loss, [incremental.loss])


def rsi_sma_numpy(close, period) -> RsiBatch:
    """
    Compute RSI using SMA over gains and losses (vectorized, batch mode).

    Args
    ----
    close : np.ndarray
        Array of closing prices.
    period : int
        RSI lookback period (SMA window).

    Returns
    -------
    RsiBatch
        Container with RSI and intermediate SMA values.
    --------------------------------------------------
    rsi : np.ndarray
        RSI values, same length as `close`. The first element is NaN.
    avg_gain : np.ndarray:
        Average gains (SMA), same length as `close`. The first element is NaN.
    avg_loss : np.ndarray:
        Average losses (SMA), same length as `close`. The first element is NaN.
    """
    delta = np.diff(close)
    gains = np.where(delta > 0, delta, 0.0)
    losses = np.where(delta < 0, -delta, 0.0)

    avg_gain = sma_numpy(gains, period)
    avg_loss = sma_numpy(losses, period)

    rsi = 100 - (100 / (1 + avg_gain / avg_loss))
    return RsiBatch(
        rsi=np.concatenate([[np.nan], rsi]),
        avg_gain=np.concatenate([[np.nan], avg_gain]),
        avg_loss=np.concatenate([[np.nan], avg_loss]),
    )


def rsi_update(
    new_delta: float,
    last_gain: float,
    leave_gain: float,
    last_loss: float,
    leave_loss: float,
    period: int,
) -> RsiIncremental:
    """
    Incrementally update RSI with a new price change (delta) using SMA update formula.

    Args
    ----
    new_delta : float
        Price change for the current step (close_t - close_{t-1}).
    last_gain : float
        Previous average gain (SMA over the last `period` gains).
    leave_gain : float
        Gain value leaving the rolling window.
    last_loss : float
        Previous average loss (SMA over the last `period` losses).
    leave_loss : float
        Loss value leaving the rolling window.
    period : int
        RSI lookback period (SMA window size).

    Returns
    -------
    RsiIncremental
        Container with RSI and intermediate SMA values.
    --------------------------------------------------
    rsi : float
        Updated RSI value in the range [0, 100].
    gain : float
        Updated average gain.
    loss : float
        Updated average loss.
    """
    if new_delta > 0:
        gain = sma_update(
            new_price=new_delta,
            leave_price=leave_gain,
            last_sma_value=last_gain,
            period=period,
        )

        loss = sma_update(
            new_price=0, leave_price=leave_loss, last_sma_value=last_loss, period=period
        )
    else:
        gain = sma_update(
            new_price=0, leave_price=leave_gain, last_sma_value=last_gain, period=period
        )

        loss = sma_update(
            new_price=-new_delta,
            leave_price=leave_loss,
            last_sma_value=last_loss,
            period=period,
        )
    return RsiIncremental(rsi=100 - (100 / (1 + gain / loss)), gain=gain, loss=loss)
