import pytest

from tf_strategy.connector.common.schemas import Symbol


class TestSymbol:
    def test_uppercase_conversion(self):
        s = Symbol(first="btc", second="usdt")
        assert s.first == "BTC"
        assert s.second == "USDT"

    def test_default_symbol_format(self):
        s = Symbol(first="ETH", second="BTC")
        assert s.symbol == "ETH/BTC"  # default "{}/{}"
        assert s.r_symbol == "BTC/ETH"

    def test_custom_symbol_format(self):
        s = Symbol(first="XRP", second="USD")
        s.set_format("{}-{}")
        assert s.symbol == "XRP-USD"
        assert s.r_symbol == "USD-XRP"

        s.set_format("{}{}")
        assert s.symbol == "XRPUSD"
        assert s.r_symbol == "USDXRP"

    def test_invalid_format_raises(self):
        s = Symbol(first="LTC", second="BTC")
        with pytest.raises(ValueError):
            s.set_format("{}")  # only one placeholder

        with pytest.raises(ValueError):
            s.set_format("{}{}{}")  # three placeholders

    def test_set_format_does_not_change_uppercase(self):
        s = Symbol(first="bnb", second="usd")
        s.set_format("{}-{}")
        assert s.symbol == "BNB-USD"
        assert s.r_symbol == "USD-BNB"
