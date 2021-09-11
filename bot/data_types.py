import enum
import typing
from decimal import Decimal

# TODO right now it's not possib to mark specific fields as optional
# https://www.python.org/dev/peps/pep-0655/
CryptoBalance = typing.TypedDict(
    "CryptoBalance",
    {
        "symbol": str,
        # could be quantity?
        "amount": Decimal,
        "usd_price": Decimal,
        "usd_total": Decimal,
        "percentage": Decimal,
        "target_percentage": Decimal,
    },
)

CryptoData = typing.TypedDict(
    "CryptoData",
    {
        # symbol is not a pair
        "symbol": str,
        "market_cap": Decimal,
        # should really be 'market_cap_percentage'
        "percentage": Decimal,
        # day indicator at the end of the variable name since argument names cannot start with a number
        "change_7d": float,
        "change_30d": float,
    },
)

MarketBuy = typing.TypedDict(
    "MarketBuy",
    {
        "symbol": str,
        "amount": Decimal,
    },
)


class MarketBuyStrategy(str, enum.Enum):
    LIMIT = "limit"
    MARKET = "market"


# by subclassing str you can use == to compare strings to enums
class MarketIndexStrategy(str, enum.Enum):
    MARKET_CAP = "market_cap"
    SQRT_MARKET_CAP = "sqrt_market_cap"
    SMA = "sma"
