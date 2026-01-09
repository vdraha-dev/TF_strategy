from abc import ABC, abstractmethod
from enum import IntEnum

import numpy as np
import pandas as pd


class TradeSignal(IntEnum):
    OpenPosition = 1
    ClosePosition = -1
    Nonthing = 0


class BaseStrategy(ABC):
    """Base class for all trading strategies"""

    def __init__(self, params: dict | None = None):
        """
        Initialize strategy

        Args:
            params: Dictionary with strategy parameters
        """
        self._params = params or {}
        self._signals = []

    @property
    def signals(self) -> list:
        return self._signals

    @abstractmethod
    def update_batch(self, data: pd.DataFrame):
        """
        Update trading signals for the entire dataset (batch mode).

        This method should replace existing signals with newly calculated ones
        based on the full DataFrame of OHLCV data. Typically used in backtesting
        or when recalculating indicators over historical data.

        Args:
            data (pd.DataFrame): DataFrame containing OHLCV price data.
                Expected columns: ['open', 'high', 'low', 'close', 'volume'].
        """

    @abstractmethod
    def update_incremental(self, data: pd.DataFrame):
        """
        Update only the most recent signal and append it to existing signals (realtime/live mode).

        This method is intended for streaming or incremental updates where only
        the latest price or bar is available.

        Args:
            data (pd.DataFrame): DataFrame containing the latest OHLCV bar(s).
                Expected columns: ['open', 'high', 'low', 'close', 'volume'].
        """

    def get_last_signal(self) -> TradeSignal:
        """
        Return the most recent trading signal.

        Returns:
            TradeSignal: Last signal in self.signals. If no signals exist, returns TradeSignal.Nonthing.
        """
        if self.signals:
            return TradeSignal(self.signals[-1])

        return TradeSignal.Nonthing

    @abstractmethod
    def generate_signals(self, data: pd.DataFrame) -> np.ndarray:
        """
        Generate trading signals based on OHLCV data using the Trend Following strategy.

        Parameters
        ----------
        data : pd.DataFrame
            DataFrame containing at least a 'close' column with price data.

        Returns
        -------
        np.ndarray
            Array of signals with values in {-1, 0, 1}:
            - 1 : enter long position
            - -1 : exit position
            - 0 : hold / do nothing
        """
