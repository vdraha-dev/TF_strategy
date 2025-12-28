import logging
from datetime import datetime

import httpx
import orjson

from .enums import TimeInterval
from .rest_paths import rest_path
from .schemas import Symbol
from .tools import dt_to_ms, tz_to_offset

logger = logging.getLogger(__name__)


class BinancePublicREST:
    def __init__(self, base_url: str):
        self._http_pub_client = httpx.AsyncClient(base_url=base_url)

    async def get_historical_candles(
        self,
        symbol: Symbol,
        interval: TimeInterval,
        *,
        limit: int | None = None,
        start_ts: datetime | None = None,
        end_ts: datetime | None = None,
        timezone: str | None = None,
    ) -> list[list[str | int]]:
        """
        Fetch historical kline/candlestick bars for a symbol.

        Klines are uniquely identified by their open time.

        If `start_ts` and `end_ts` are not provided, the most recent klines are returned.

        The `timezone` parameter affects how kline intervals are interpreted,
        but does NOT affect `start_ts` and `end_ts`, which are always interpreted in UTC.

        Supported values for `timezone`:
            - Hours and minutes (e.g. "-1:00", "05:45")
            - Only hours (e.g. "0", "8", "-4")
            - Accepted range is strictly from "-12:00" to "+14:00" (inclusive)

        Args:
            symbol (Symbol): Trading symbol (e.g. BTC/USDT).
            interval (TimeInterval): Kline interval (e.g. 1m, 5m, 1h).
            limit (int, optional): Number of klines to return. Defaults to None.
            start_ts (datetime, optional): Start time in UTC. Defaults to None.
            end_ts (datetime, optional): End time in UTC. Defaults to None.
            timezone (str, optional): Timezone used to interpret kline intervals. Defaults to UTC.

        Raises:
            Exception: Raised when an unexpected error occurs.

        Returns:
            list: List of klines, where each kline is represented as:
                [
                    1499040000000, "0.01634790", "0.80000000",
                    "0.01575800", "0.01577100", "148976.11427815",
                    1499644799999, "2434.19055334", 308,
                    "1756.87402397", "28.46694368", "0"
                ]
        """
        klines: list[list[str | int]] = []

        params = {
            "symbol": symbol.symbol,
            "interval": interval.value,
        }

        if limit:
            original_limit = limit
            if limit < 0:
                logger.warning(
                    "limit parameter must be greater than zero, converting to positive",
                    extra={"original_limit": original_limit},
                )
                limit = abs(limit)
            if limit > 1000:
                logger.warning(
                    "limit parameter must be <= 1000, capping to 1000",
                    extra={"original_limit": original_limit},
                )
                limit = 1000
            params["limit"] = limit
        if start_ts:
            params["startTime"] = dt_to_ms(start_ts)
        if end_ts:
            params["endTime"] = dt_to_ms(end_ts)
        if timezone:
            params["timeZone"] = tz_to_offset(timezone)

        try:
            logger.debug("Requesting historical klines", extra={"params": params})
            res = await self._http_pub_client.get(
                url=rest_path.public.klines, params=params
            )
            res.raise_for_status()
            klines = orjson.loads(res.content)

        except httpx.HTTPStatusError as e:
            logger.error(
                "Couldn't get candles info",
                extra={
                    "status_code": e.response.status_code,
                    "response_text": e.response.text,
                    "symbol": symbol.symbol,
                    "interval": interval.value,
                    "exception_id": id(e),
                },
            )
        except httpx.TimeoutException as e:
            logger.error(
                "Timeout while fetching candles info",
                extra={
                    "symbol": symbol.symbol,
                    "interval": interval.value,
                    "exception_id": id(e),
                },
            )
        except Exception as e:
            logger.error(
                "Unexpected error fetching candles info",
                extra={
                    "symbol": symbol.symbol,
                    "interval": interval.value,
                    "exception_type": type(e).__name__,
                    "exception_id": id(e),
                },
            )
            raise

        return klines
