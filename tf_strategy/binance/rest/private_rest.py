import logging
import time
from collections.abc import Generator

import httpx
import orjson
from cryptography.hazmat.primitives.asymmetric.types import PrivateKeyTypes

from tf_strategy.binance.schemas import CancelOrder, Order, OrderReport, Symbol, Wallet
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

    async def account_info(self) -> dict | None:
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
        try:
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
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to retrieve account information: {str(e)}")
            return None

        return orjson.loads(res.content)

    async def wallet(self) -> Wallet:
        """
        Retrieve the current wallet state for the account.

        This method fetches account information from the exchange and converts
        the balances data into a `Wallet` object, where each asset is mapped
        to a `BalanceForAsset` instance containing free and locked amounts.

        Returns:
            Wallet: A wallet object containing balances for all non-zero assets.
        """
        account_info = (await self.account_info()) or {}

        return Wallet(balance=account_info.get("balances", []))

    async def send_order(self, order: Order) -> OrderReport | None:
        """
        Send a trading order to the exchange.

        This method signs and sends an order request to the private REST API.
        If the request is successful, the response is validated and converted
        into an `OrderReport` model. In case of an HTTP error, the error is
        logged and `None` is returned.

        Args:
            order (Order):
                The order object containing all required order parameters.

        Returns:
            (OrderReport | None):
                The validated order report if the request succeeds,
                otherwise `None` if an error occurs.
        """
        try:
            resp = await self._http_client.post(
                url=rest_path.private.order,
                params=get_signed_payload(
                    self._private_key,
                    {
                        **Order.create_order_payload(order),
                        "timestamp": int(time.time() * 1000),
                    },
                ),
            )

            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to send order: {str(e)}")
            return None

        raw = orjson.loads(resp.content)
        report = OrderReport.model_validate(raw)
        return report

    async def get_open_orders(
        self, symbol: Symbol | None = None
    ) -> Generator[None, None, OrderReport]:
        """If the symbol is not sent, orders for all symbols will be returned in an array."""
        payload = {}
        if symbol:
            payload['symbol'] = symbol.symbol

        try:
            res = await self._http_client.get(
                url=rest_path.private.open_orders,
                params=get_signed_payload(
                    self._private_key, {**payload, "timestamp": int(time.time() * 1000)}
                ),
            )

            res.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to get open orders: {str(e)}")
            return None

        return (OrderReport.model_validate(i) for i in orjson.loads(res.content))

    async def cancel_order(self, order: CancelOrder) -> OrderReport | None:
        """
        Cancel an existing order on the exchange.
        
        This method signs and sends an order request to the private REST API.
        If the request is successful, the response is validated and converted
        into an `OrderReport` model. In case of an HTTP error, the error is
        logged and `None` is returned.

        Args:
            order (CancelOrder):
                The order object containing all required order parameters.

        Returns:
            (OrderReport | None):
                The validated order report if the request succeeds,
                otherwise `None` if an error occurs.
        """
        try:
            res = await self._http_client.delete(
                url=rest_path.private.order,
                params=get_signed_payload(
                    self._private_key,
                    {
                        **CancelOrder.create_cancel_payload(order),
                        "timestamp": int(time.time() * 1000),
                    },
                ),
            )

            res.raise_for_status()

        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to cancel order: {str(e)}")
            return None

        return OrderReport.model_validate(orjson.loads(res.content))
