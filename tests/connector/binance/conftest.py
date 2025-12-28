import pytest

from tf_strategy.connector.binance.schemas import Symbol


@pytest.fixture(scope="session")
def public_base_url():
    return "https://api.binance.com"


@pytest.fixture(scope="session")
def btc_usdc_symbol():
    return Symbol(first="BTC", second="USDC")


@pytest.fixture(scope="session")
def btc_eth_symbol():
    return Symbol(first="BTC", second="ETH")


@pytest.fixture(scope="session")
def eth_usdc_symbol():
    return Symbol(first="ETH", second="USDC")
