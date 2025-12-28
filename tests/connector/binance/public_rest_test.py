import logging
from datetime import datetime

import pytest
import pytz

from tf_strategy.connector.binance.public_rest import BinancePublicREST
from tf_strategy.connector.binance.tools import dt_to_ms, ms_to_dt
from tf_strategy.connector.common.enums import TimeInterval


@pytest.mark.integration
class TestHistoricalKlinesIntegration:
    def setup_method(self):
        self._client = BinancePublicREST("https://api.binance.com")

    @pytest.mark.asyncio
    async def test_use_only_required_field(self, btc_usdc_symbol):
        res = await self._client.get_historical_candles(
            btc_usdc_symbol, TimeInterval._1m
        )

        assert len(res) == 500

    @pytest.mark.asyncio
    async def test_call_with_custom_limin(self, btc_usdc_symbol):
        custom_limit = 250

        res = await self._client.get_historical_candles(
            btc_usdc_symbol, TimeInterval._1m, limit=custom_limit
        )

        assert len(res) == custom_limit

    @pytest.mark.asyncio
    async def test_limit_is_negative_number(self, caplog, btc_usdc_symbol):
        custom_limit = -100

        caplog.set_level(logging.WARNING)

        res = await self._client.get_historical_candles(
            btc_usdc_symbol, TimeInterval._1m, limit=custom_limit
        )

        assert len(res) == abs(custom_limit)
        assert any(
            "limit parameter must be greater than zero" in record.message
            for record in caplog.records
        )

    @pytest.mark.asyncio
    async def test_limit_is_greater_than_1000(self, caplog, btc_usdc_symbol):
        custom_limit = 1500

        caplog.set_level(logging.WARNING)

        res = await self._client.get_historical_candles(
            btc_usdc_symbol, TimeInterval._1m, limit=custom_limit
        )

        assert len(res) == 1000
        assert any(
            "limit parameter must be <= 1000" in record.message
            for record in caplog.records
        )

    @pytest.mark.asyncio
    async def test_start_at(self, btc_usdc_symbol):
        start_time = datetime(
            year=2025, month=12, day=1, hour=12, minute=30, second=0, tzinfo=pytz.UTC
        )
        close_time = start_time.replace(second=59, microsecond=999 * 1000)

        res = await self._client.get_historical_candles(
            btc_usdc_symbol, TimeInterval._1m, start_ts=start_time
        )

        first_start = ms_to_dt(res[0].open_time)
        first_close = ms_to_dt(res[0].close_time)

        assert start_time == first_start
        assert close_time == first_close

    @pytest.mark.asyncio
    async def test_start_at_using_posix_timestamp(self, btc_usdc_symbol):
        start_time = dt_to_ms(
            datetime(
                year=2025,
                month=12,
                day=1,
                hour=12,
                minute=30,
                second=0,
                tzinfo=pytz.UTC,
            )
        )
        close_time = start_time + 59000 + 999

        res = await self._client.get_historical_candles(
            btc_usdc_symbol, TimeInterval._1m, start_ts=start_time
        )

        first_start = res[0].open_time
        first_close = res[0].close_time

        assert start_time == first_start
        assert close_time == first_close

    @pytest.mark.asyncio
    async def test_end_at(self, btc_usdc_symbol):
        end_time = datetime(
            year=2025, month=12, day=1, hour=12, minute=30, second=0, tzinfo=pytz.UTC
        )
        close_time = end_time.replace(second=59, microsecond=999 * 1000)

        res = await self._client.get_historical_candles(
            btc_usdc_symbol, TimeInterval._1m, end_ts=end_time
        )

        last_start = ms_to_dt(res[-1].open_time)
        last_close = ms_to_dt(res[-1].close_time)

        assert end_time == last_start
        assert close_time == last_close

    @pytest.mark.asyncio
    async def test_end_at_using_posix_timestamp(self, btc_usdc_symbol):
        end_time = dt_to_ms(
            datetime(
                year=2025,
                month=12,
                day=1,
                hour=12,
                minute=30,
                second=0,
                tzinfo=pytz.UTC,
            )
        )
        close_time = end_time + 59000 + 999

        res = await self._client.get_historical_candles(
            btc_usdc_symbol, TimeInterval._1m, end_ts=end_time
        )

        last_start = res[-1].open_time
        last_close = res[-1].close_time

        assert end_time == last_start
        assert close_time == last_close
