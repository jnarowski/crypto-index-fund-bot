import typing as t
import functools
from decimal import Decimal

from binance.client import Client as BinanceClient

from ..data_types import CryptoBalance, ExchangeOrder, SupportedExchanges
from ..user import User

# https://algotrading101.com/learn/binance-python-api-guide/
# https://github.com/timggraf/crypto-index-bot seems to have details about binance errors. Need to handle more error types


# initializing a new client actually hits the `ping` endpoint on the API
# which is on of the reasons we want to cache it
@functools.cache
def public_binance_client() -> BinanceClient:
    return BinanceClient("", "", tld="us")


def binance_purchase_minimum() -> Decimal:
    return Decimal(10)


def binance_portfolio(user: User) -> t.List[CryptoBalance]:
    account = user.binance_client().get_account()

    # TODO return an incomplete CryptoBalance that will be augmented with additional fields later on
    return [
        CryptoBalance(
            symbol=balance["asset"],
            amount=Decimal(balance["free"]),
            # to satisify typer; hopefully there is a better way to do this in the future
            usd_price=Decimal(0),
            usd_total=Decimal(0),
            percentage=Decimal(0),
            target_percentage=Decimal(0),
        )
        for balance in account["balances"]
        if float(balance["free"]) > 0
    ]


def binance_open_orders(user: User) -> t.List[ExchangeOrder]:
    """
        [
        {
            'symbol': 'HNTUSD',
            'orderId': 123123123,
            'orderListId': -1,
            'clientOrderId': 'web_123longsha123',
            'price': '45.0000',
            'origQty': '10.00000000',
            'executedQty': '0.00000000',
            'cummulativeQuoteQty': '0.0000',
            'status': 'NEW',
            'timeInForce': 'GTC',
            'type': 'LIMIT',
            'side': 'SELL',
            'stopPrice': '0.0000',
            'icebergQty': '0.00000000',
            'time': 1629643256714,
            'updateTime': 1629643256714,
            'isWorking': True,
            'origQuoteOrderQty': '0.0000'
        }
    ]
    """

    return [
        ExchangeOrder(
            # TODO PURCHASING_CURRENCY should make this dynamic for different purchasing currencies
            # cut off the 'USD' at the end of the symbol
            symbol=order["symbol"][:-3],
            quantity=Decimal(order["origQty"]),
            price=Decimal(order["price"]),
            # binance represents time in milliseconds
            created_at=int(Decimal(order["time"]) / 1000),
            time_in_force=order["timeInForce"],
            type=order["side"],
            id=order["orderId"],
            exchange=SupportedExchanges.BINANCE,
        )
        for order in user.binance_client().get_open_orders()
        if order["side"] == BinanceClient.SIDE_BUY
    ]
