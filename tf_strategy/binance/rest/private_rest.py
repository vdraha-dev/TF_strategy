import logging
import time

import httpx
import orjson
from cryptography.hazmat.primitives.asymmetric.types import PrivateKeyTypes

from tf_strategy.common.tools import get_signed_payload

from .rest_paths import rest_path

logger = logging.getLogger(__name__)


class BinancePrivateREST:
    def __init__(self, url: str, api_key: str, private_key: PrivateKeyTypes):
        self._http_client = httpx.AsyncClient(
            base_url=url,
            headers={
                "X-MBX-APIKEY": api_key,
            },
        )

        self._private_key = private_key

    async def account_info(self) -> dict:
        """
        Get current account information.

        Returns:
            dict: return raw dict from Binance:
            {
                "makerCommission": 15,
                "takerCommission": 15,
                "buyerCommission": 0,
                "sellerCommission": 0,
                "commissionRates": {
                    "maker": "0.00150000",
                    "taker": "0.00150000",
                    "buyer": "0.00000000",
                    "seller": "0.00000000"
                },
                "canTrade": true,
                "canWithdraw": true,
                "canDeposit": true,
                "brokered": false,
                "requireSelfTradePrevention": false,
                "preventSor": false,
                "updateTime": 123456789,
                "accountType": "SPOT",
                "balances": [
                    {
                    "asset": "BTC",
                    "free": "4723846.89208129",
                    "locked": "0.00000000"
                    },
                    {
                    "asset": "LTC",
                    "free": "4763368.68006011",
                    "locked": "0.00000000"
                    }
                ],
                "permissions": [
                    "SPOT"
                ],
                "uid": 354937868
            }
        """
        res = await self._http_client.get(
            url=rest_path.private.account,
            params=get_signed_payload(
                self._private_key,
                {
                    "omitZeroBalances": "true",  # only non-zero balances
                    "timestamp": int(time.time() * 1000),
                },
            ),
        )

        res.raise_for_status()

        return orjson.loads(res.content)
