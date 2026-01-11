from collections import deque
from typing import NamedTuple

import numpy as np
import pandas as pd

from .base import BaseStrategy
from .signals.adx import AdxBatch, AdxIncremental, adx, adx_update
from .signals.ema import ema_scipy, ema_update
from .signals.rsi import RsiBatch, RsiIncremental, rsi_sma_numpy, rsi_update
from .tools import crossed_above, crossed_below


class TrendFollowing(BaseStrategy):
    """Momentum/Trend Following strategy"""

    class FullSignals(NamedTuple):
        signals: np.ndarray
        fast_ma: np.ndarray
        slow_ma: np.ndarray
        rsi: RsiBatch
        adx: AdxBatch

    class LimitedRsiSignal(NamedTuple):
        rsi: deque
        gain: deque
        loss: deque

        def update(self, incremental: RsiIncremental):
            self.rsi.append(incremental.rsi)
            self.gain.append(incremental.gain)
            self.loss.append(incremental.loss)

    class LimitedAdxSignal(NamedTuple):
        adx: deque
        trs: deque
        pdms: deque
        mdms: deque

        def update(self, incremental: AdxIncremental):
            self.adx.append(incremental.adx)
            self.trs.append(incremental.trs)
            self.pdms.append(incremental.pdms)
            self.mdms.append(incremental.mdms)

    class LimitedSignals(NamedTuple):
        signals: deque
        fast_ma: deque
        slow_ma: deque
        rsi: TrendFollowing.LimitedRsiSignal
        adx: TrendFollowing.LimitedAdxSignal

    def __init__(self, params: dict = None):
        """
        Args
        ----
        params : dict
        'fast_period': fast MA period (default 20),
        'slow_period': slow MA period (default 50),
        'adx_period': ADX period (default 20)
        'adx_strength': The strength of trend (default 25)
        'rsi_period': RSI period (default 14),
        'rsi_overbought': overbought level (default 70),
        'rsi_oversold': oversold level (default 30)
        """
        default_params = {
            'fast_period': 20,
            'slow_period': 50,
            'adx_period': 20,
            'adx_strength': 25,
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
        high = data["high"].to_numpy(dtype=float)
        low = data["low"].to_numpy(dtype=float)
        close = data["close"].to_numpy(dtype=float)

        result: TrendFollowing.FullSignals = self._generate_signals(
            high=high,
            low=low,
            close=close,
            fast_period=self._params["fast_period"],
            slow_period=self._params["slow_period"],
            adx_period=self._params["adx_period"],
            adx_strength=self._params["adx_strength"],
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
            adx=TrendFollowing.LimitedAdxSignal(
                adx=deque(
                    result.adx.adx[-self._params["adx_period"] :],
                    maxlen=self._params["adx_period"],
                ),
                trs=deque(
                    result.adx.trs[-self._params["adx_period"] :],
                    maxlen=self._params["adx_period"],
                ),
                pdms=deque(
                    result.adx.pdms[-self._params["adx_period"] :],
                    maxlen=self._params["adx_period"],
                ),
                mdms=deque(
                    result.adx.mdms[-self._params["adx_period"] :],
                    maxlen=self._params["adx_period"],
                ),
            ),
        )

    def update_incremental(self, data: pd.DataFrame):
        if not self._signals:
            raise

        high = data["high"].to_numpy(dtype=float)
        low = data["low"].to_numpy(dtype=float)
        close = data["close"].to_numpy(dtype=float)

        fast_period = self._params["fast_period"]
        slow_period = self._params["slow_period"]
        rsi_period = self._params["rsi_period"]

        fast_ma = ema_update(
            new_price=close[-1],
            last_ema_value=self._signals.fast_ma[-1],
            alpha=2 / (fast_period + 1),
        )

        slow_ma = ema_update(
            new_price=close[-1],
            last_ema_value=self._signals.slow_ma[-1],
            alpha=2 / (slow_period + 1),
        )

        rsi = rsi_update(
            new_delta=close[-1] - close[-2],
            last_gain=self._signals.rsi.gain[-1],
            leave_gain=self._signals.rsi.gain[0],
            last_loss=self._signals.rsi.loss[-1],
            leave_loss=self._signals.rsi.loss[0],
            period=rsi_period,
        )

        adx_ = adx_update(
            high=high[-1],
            prev_high=high[-2],
            low=low[-1],
            prev_low=low[-2],
            prev_close=close[-2],
            last_adx=self._signals.adx.adx[-1],
            last_trs=self._signals.adx.trs[-1],
            last_pdms=self._signals.adx.pdms[-1],
            last_mdms=self._signals.adx.mdms[-1],
            period=self._params["adx_period"],
        )

        self._signals.fast_ma.append(fast_ma)
        self._signals.slow_ma.append(slow_ma)
        self._signals.rsi.update(rsi)
        self._signals.adx.update(adx_)

        lfast_ma = np.array([self._signals.fast_ma[-2], self._signals.fast_ma[-1]])
        lslow_ma = np.array([self._signals.slow_ma[-2], self._signals.slow_ma[-1]])

        entries = (
            crossed_above(lfast_ma, lslow_ma)[-1]
            and rsi.rsi < self._params["rsi_oversold"]
            and adx_.adx > self._params["adx_strength"]
        )
        exits = (
            crossed_below(lfast_ma, lslow_ma)[-1]
            and rsi.rsi > self._params["rsi_overbought"]
        )

        signal = 0
        if entries:
            signal = 1
        elif exits:
            signal = -1

        self._signals.signals.append(signal)

    def _generate_signals(
        self,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        fast_period: int,
        slow_period: int,
        adx_period: int,
        adx_strength: float,
        rsi_period: int,
        rsi_overbought: float,
        rsi_oversold: float,
    ) -> FullSignals:
        fast_ma = ema_scipy(close, fast_period)
        slow_ma = ema_scipy(close, slow_period)
        rsi = rsi_sma_numpy(close, rsi_period)
        adx_ = adx(high, low, close, adx_period)

        entries = (
            crossed_above(fast_ma, slow_ma)
            & (rsi.rsi < rsi_oversold)
            & (adx_.adx > adx_strength)
        )
        exits = crossed_below(fast_ma, slow_ma) & (rsi.rsi > rsi_overbought)

        signals = np.zeros_like(close, dtype=np.int8)
        signals[entries] = 1
        signals[exits] = -1

        return self.FullSignals( 
            signals=signals, fast_ma=fast_ma, slow_ma=slow_ma, rsi=rsi, adx=adx_
        )

    def generate_signals(
        self,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        fast_period: int,
        slow_period: int,
        adx_period: int,
        adx_strength: float,
        rsi_period: int,
        rsi_overbought: float,
        rsi_oversold: float,
    ) -> np.ndarray:
        high = high.squeeze()
        low = low.squeeze()
        close = close.squeeze()
        signals = self._generate_signals(
            high,
            low,
            close,
            fast_period,
            slow_period,
            adx_period,
            adx_strength,
            rsi_period,
            rsi_overbought,
            rsi_oversold,
        )

        return signals.signals
