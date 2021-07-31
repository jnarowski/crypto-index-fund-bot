import requests

from utils import log
from user import User, user_from_env

from typing import List
from data_types import CryptoData

def coinmarketcap_data():
  import os
  coinmarketcap_api_key = os.getenv('COINMARKETCAP_API_KEY')
  coinbase_endpoint = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest?limit=1000&sort=market_cap"

  # TODO should we cache or at minimum memoize this?
  return requests.get(coinbase_endpoint, headers={
    "X-CMC_PRO_API_KEY": coinmarketcap_api_key
  }).json()

# for debugging / testing only
def coinmarketcap_tags():
  from functools import reduce
  import operator

  all_data = coinmarketcap_data()
  all_tags = [data['tags'] for data in all_data['data']]
  all_tags = reduce(operator.concat, all_tags)
  return set(all_tags)

# for debugging / testing only
def coinmarketcap_data_for_symbol(symbol):
  all_data = coinmarketcap_data()
  return next(data for data in all_data['data'] if data['symbol'] == symbol)

# TODO should indicate that this is married to coinmarketcap data a bit more
# market_data is pulled from coinmarketcap
def filtered_coins_by_market_cap(
    market_data,
    purchasing_currency: str,
    exchanges: List[str],
    exclude_tags=[],
    exclude_coins=[],
    limit=-1
  ):

  from exchanges import can_buy_in_exchange

  exclude_tags = set(exclude_tags)
  coins = []

  for coin in market_data['data']:
    symbol = coin['symbol']

    # was the coin included in a list of skipped coins?
    offending_tags = set.intersection(set(coin['tags']), exclude_tags)
    if len(offending_tags) > 0:
      log.debug("skipping, includes excluded tag", symbol=symbol, offending_tags=offending_tags)
      continue

    # was the coin manually excluded?
    if symbol in exclude_coins:
      log.debug("coin symbol excluded", symbol=symbol)
      continue

    # is the coin available on supported exchanges
    if not any(can_buy_in_exchange(exchange, symbol, purchasing_currency) for exchange in exchanges):
      log.debug("coin cannot be purchased in exchange", symbol=symbol, exchanges=exchanges)
      continue

    coins.append(coin)

    if limit != -1:
      limit -= 1
      if limit == 0:
        break

  log.info("filtered coin list, used for index", coin_count=len(coins))

  return coins

# TODO hardcoded against USD quotes right now, support different purchase currencies in the future
# `coins` is data from coinmarketcap
def calculate_market_cap_from_coin_list(purchasing_currency: str, coins) -> List[CryptoData]:
  total_market_cap = sum([coin['quote'][purchasing_currency]['market_cap'] for coin in coins])
  coins_with_market_cap = []

  log.info("total market cap", total_market_cap=total_market_cap)

  for coin in coins:
    market_cap = coin['quote'][purchasing_currency]['market_cap']

    coins_with_market_cap.append({
      "symbol": coin['symbol'],
      "market_cap": market_cap,

      # TODO we probably need safer FPA calculations
      # represents % of total market cap of the portfolio
      "percentage": market_cap / total_market_cap * 100,

      # include percent changes for purchase priority decisions
      "7d_change": coin['quote'][purchasing_currency]['percent_change_7d'],
      "30d_change": coin['quote'][purchasing_currency]['percent_change_30d']

      # TODO why not just add the USD price here? Any benefit to pulling the price from the exchange?
    })

  return coins_with_market_cap

def coins_with_market_cap(user: User, limit: int) -> List[CryptoData]:
  market_data = coinmarketcap_data()

  filtered_coins = filtered_coins_by_market_cap(
    market_data,
    user.purchasing_currency(),

    exchanges=user.exchanges(),
    exclude_tags=user.excluded_tags(),
    limit=limit,

    # TODO if multiple exchanges exclude coins included in a previous index?
    # exclude_coins=
  )

  return calculate_market_cap_from_coin_list(user.purchasing_currency(), filtered_coins)
