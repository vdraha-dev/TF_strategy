from collections import deque
from typing import NamedTuple

import numpy as np
import pandas as pd

from .base import BaseStrategy
from .signals.rsi import RsiBatch, RsiIncremental, rsi_sma_numpy, rsi_update
from .signals.sma import sma_numpy, sma_update
from .tools import crossed_above, crossed_below


class TrendFollowing(BaseStrategy):
    """Momentum/Trend Following strategy"""

    class FullSignals(NamedTuple):
        signals: np.ndarray
        fast_ma: np.ndarray
        slow_ma: np.ndarray
        rsi: RsiBatch

    class RsiSignal(NamedTuple):
        rsi: np.ndarray
        gain: np.ndarray
        loss: np.ndarray

    class LimitedRsiSignal(NamedTuple):
        rsi: deque
        gain: deque
        loss: deque

        def update(self, incremental: RsiIncremental):
            self.rsi.append(incremental.rsi)
            self.gain.append(incremental.gain)
            self.loss.append(incremental.loss)

    class LimitedSignals(NamedTuple):
        signals: deque
        fast_ma: deque
        slow_ma: deque
        rsi: TrendFollowing.LimitedRsiSignal

    def __init__(self, params: dict = None):
        """
        Args
        ----
        params : dict
        'fast_period': fast MA period (default 20),
        'slow_period': slow MA period (default 50),
        'rsi_period': RSI period (default 14),
        'rsi_overbought': overbought level (default 70),
        'rsi_oversold': oversold level (default 30)
        """
        default_params = {
            'fast_period': 20,
            'slow_period': 50,
            'rsi_period': 14,
            'rsi_overbought': 70,
            'rsi_oversold': 30,
        }
        if params:
            default_params.update(params)
        super().__init__(default_params)
        self._signals: TrendFollowing.LimitedSignals | None = None

    @property
    def signals(self) -> np.ndarray:
        return self._signals.signals

    def update_batch(self, data: pd.DataFrame):
        close = data["close"].to_numpy(dtype=float)

        result = self._generate_signals(
            close=close,
            fast_period=self._params["fast_period"],
            slow_period=self._params["slow_period"],
            rsi_period=self._params["rsi_period"],
            rsi_overbought=self._params["rsi_overbought"],
            rsi_oversold=self._params["rsi_oversold"],
        )

        self._signals = TrendFollowing.LimitedSignals(
            signals=deque(result.signals[-100:], maxlen=100),
            fast_ma=deque(
                result.fast_ma[-self._params["fast_period"] :],
                maxlen=self._params["fast_period"],
            ),
            slow_ma=deque(
                result.slow_ma[-self._params["slow_period"] :],
                maxlen=self._params["slow_period"],
            ),
            rsi=TrendFollowing.LimitedRsiSignal(
                rsi=deque(
                    result.rsi.rsi[-self._params["rsi_period"] :],
                    maxlen=self._params["rsi_period"],
                ),
                gain=deque(
                    result.rsi.avg_gain[-self._params["rsi_period"] :],
                    maxlen=self._params["rsi_period"],
                ),
                loss=deque(
                    result.rsi.avg_loss[-self._params["rsi_period"] :],
                    maxlen=self._params["rsi_period"],
                ),
            ),
        )

    def update_incremental(self, data: pd.DataFrame):
        if not self._signals:
            raise

        close = data["close"].to_numpy(dtype=float)

        fast_period = self._params["fast_period"]
        slow_period = self._params["slow_period"]
        rsi_period = self._params["rsi_period"]

        fast_ma = sma_update(
            new_price=close[-1],
            leave_price=close[-fast_period - 1],
            last_sma_value=self._signals.fast_ma[-1],
            period=fast_period,
        )

        slow_ma = sma_update(
            new_price=close[-1],
            leave_price=close[-slow_period - 1],
            last_sma_value=self._signals.slow_ma[-1],
            period=slow_period,
        )

        rsi = rsi_update(
            new_delta=close[-1] - close[-2],
            last_gain=self._signals.rsi.gain[-1],
            leave_gain=self._signals.rsi.gain[0],
            last_loss=self._signals.rsi.loss[-1],
            leave_loss=self._signals.rsi.loss[0],
            period=rsi_period,
        )

        self._signals.fast_ma.append(fast_ma)
        self._signals.slow_ma.append(slow_ma)
        self._signals.rsi.update(rsi)

        lfast_ma = np.array([self._signals.fast_ma[-2], self._signals.fast_ma[-1]])
        lslow_ma = np.array([self._signals.slow_ma[-2], self._signals.slow_ma[-1]])

        entries = crossed_above(lfast_ma, lslow_ma) & (
            rsi.rsi < self._params["rsi_oversold"]
        )
        exits = crossed_below(lfast_ma, lslow_ma) & (
            rsi.rsi > self._params["rsi_overbought"]
        )

        signal = 0
        if entries[-1]:
            signal = 1
        elif exits[-1]:
            signal = -1

        self._signals.signals.append(signal)

    def _generate_signals(
        self,
        close: np.ndarray,
        fast_period: int,
        slow_period: int,
        rsi_period: int,
        rsi_overbought: float,
        rsi_oversold: float,
    ) -> FullSignals:

        fast_ma = sma_numpy(close, fast_period)
        slow_ma = sma_numpy(close, slow_period)
        rsi = rsi_sma_numpy(close, rsi_period)

        entries = crossed_above(fast_ma, slow_ma) & (rsi.rsi < rsi_oversold)
        exits = crossed_below(fast_ma, slow_ma) & (rsi.rsi > rsi_overbought)

        signals = np.zeros_like(close, dtype=np.int8)
        signals[entries] = 1
        signals[exits] = -1

        return self.FullSignals(
            signals=signals, fast_ma=fast_ma, slow_ma=slow_ma, rsi=rsi
        )

    def generate_signals(
        self,
        close: np.ndarray,
        fast_period: int,
        slow_period: int,
        rsi_period: int,
        rsi_overbought: float,
        rsi_oversold: float,
    ) -> np.ndarray:

        signals = self._generate_signals(
            close, fast_period, slow_period, rsi_period, rsi_overbought, rsi_oversold
        )

        return signals.signals
