import unittest
from unittest.mock import patch

import binance.client
import pytest
from click.testing import CliRunner

import bot.user
import main
from bot.data_types import MarketBuyStrategy, MarketIndexStrategy


@pytest.mark.vcr
class TestCLI(unittest.TestCase):
    @patch.object(binance.client.Client, "order_market_buy", side_effect=pytest.helpers.mocked_order_result)
    @patch("bot.market_buy.purchasing_currency_in_portfolio", return_value=20)
    def test_market_buy(self, _purchasing_currency_mock, order_market_buy_mock):
        # user preconditions
        user = bot.user.user_from_env()
        user.buy_strategy = MarketBuyStrategy.MARKET

        assert True == user.livemode
        assert 10 == user.purchase_min
        assert MarketBuyStrategy.MARKET == user.buy_strategy
        assert MarketIndexStrategy.MARKET_CAP == user.index_strategy

        with patch("main.user_from_env", return_value=user):
            runner = CliRunner()
            result = runner.invoke(main.buy, [])

        # output is redirected to the result object, let's output for debugging
        print(result.output)

        self.assertIsNone(result.exception)
        assert result.exit_code == 0

        # 60 should be split into two orders
        assert order_market_buy_mock.call_count == 2
        assert {
            "symbol": "ADAUSD",
            "newOrderRespType": "FULL",
            "quoteOrderQty": "10.0000",
        } == order_market_buy_mock.mock_calls[0].kwargs
        assert {
            "symbol": "SOLUSD",
            "newOrderRespType": "FULL",
            "quoteOrderQty": "10.0000",
        } == order_market_buy_mock.mock_calls[1].kwargs

    def test_portfolio(self):
        runner = CliRunner()
        result = runner.invoke(main.portfolio, [])

        # output is redirected to the result object, let's output for debugging
        print(result.output)

        self.assertIsNone(result.exception)
        assert result.exit_code == 0

    def test_index(self):
        runner = CliRunner()
        result = runner.invoke(main.index, [])

        self.assertIsNone(result.exception)
        assert result.exit_code == 0

    def test_analyze(self):
        runner = CliRunner()
        result = runner.invoke(main.analyze, [])

        self.assertIsNone(result.exception)
        assert result.exit_code == 0
