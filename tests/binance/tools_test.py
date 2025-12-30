from datetime import datetime

import pytest

from tf_strategy.binance.tools import tz_to_offset


class TestTzToOffset:
    def test_kyiv_offset_winter(self):
        dt = datetime(2025, 12, 28, 12, 0, 0)
        offset = tz_to_offset("Europe/Kyiv", dt)
        assert offset == "+02:00"

    def test_kyiv_offset_summer(self):
        dt = datetime(2025, 6, 28, 12, 0, 0)
        offset = tz_to_offset("Europe/Kyiv", dt)
        assert offset == "+03:00"

    def test_new_york_offset_summer(self):
        dt = datetime(2025, 6, 1, 12, 0, 0)
        offset = tz_to_offset("America/New_York", dt)
        assert offset == "-04:00"

    def test_offset_format_now(self):
        offset = tz_to_offset("Europe/London")
        assert isinstance(offset, str)
        assert offset.startswith(("+", "-"))
        assert len(offset) == 6  # ±HH:MM

    @pytest.mark.parametrize(
        "tz_name, expected_offset, dt",
        [
            ("Etc/GMT+12", "-12:00", datetime(2025, 1, 1)),
            ("Etc/GMT-14", "+14:00", datetime(2025, 1, 1)),
            ("Etc/UTC", "+00:00", datetime(2025, 1, 1)),
        ],
    )
    def test_boundary_offsets(self, tz_name, expected_offset, dt):
        offset = tz_to_offset(tz_name, dt)
        assert offset == expected_offset
