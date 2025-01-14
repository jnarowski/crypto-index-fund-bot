import click

import bot.utils
from bot import utils
from bot.data_types import MarketIndexStrategy, SupportedExchanges
from bot.user import user_from_env

# if you use `cod` it's helpful to disable while you are hacking on the CLI
# if you are on zsh:
#   `preexec_functions=(${preexec_functions#__cod_preexec_zsh})`


@click.group(help="Tool for building your own crypto index fund.")
# TODO this must be specified before the subcommand, which is a strange requirement. I wonder if there is a way around this.
@click.option("--verbose", "-v", is_flag=True, help="Enables verbose mode.")
def cli(verbose):
    if verbose:
        bot.utils.setLevel("INFO")


@cli.command(help="Analyize configured exchanges")
def analyze():
    import bot.exchanges as exchanges

    coinbase_available_coins = set([coin["base_currency"] for coin in exchanges.coinbase_exchange])
    binance_available_coins = set([coin["baseAsset"] for coin in exchanges.binance_all_symbol_info()])

    print("Available, regardless of purchasing currency:")
    print(f"coinbase:\t{len(coinbase_available_coins)}")
    print(f"binance:\t{len(binance_available_coins)}")

    user = user_from_env()

    coinbase_available_coins_in_purchasing_currency = set(
        [coin["base_currency"] for coin in exchanges.coinbase_exchange if coin["quote_currency"] == user.purchasing_currency]
    )
    binance_available_coins_in_purchasing_currency = set(
        [coin["baseAsset"] for coin in exchanges.binance_all_symbol_info() if coin["quoteAsset"] == user.purchasing_currency]
    )

    print("\nAvailable in purchasing currency:")
    print(f"coinbase:\t{len(coinbase_available_coins_in_purchasing_currency)}")
    print(f"binance:\t{len(binance_available_coins_in_purchasing_currency)}")


@cli.command(help="Print index by market cap")
@click.option(
    "-f",
    "--format",
    type=click.Choice(["md", "csv"]),
    default="md",
    show_default=True,
    help="Output format",
)
@click.option(
    "-s",
    "--strategy",
    type=click.Choice([choice.value for choice in MarketIndexStrategy]),
    default=MarketIndexStrategy.MARKET_CAP,
    show_default=True,
    help="Index strategy",
)
@click.option("-l", "--limit", type=int, help="Maximum size of index")
def index(format, limit, strategy):
    user = user_from_env()

    if strategy:
        user.index_strategy = strategy

    if limit:
        user.index_limit = limit

    import bot.market_cap

    coins_by_exchange = bot.market_cap.coins_with_market_cap(user)

    click.echo(utils.table_output_with_format(coins_by_exchange, format))


@cli.command(help="Print current portfolio with targets")
@click.option(
    "-f",
    "--format",
    type=click.Choice(["md", "csv"]),
    default="md",
    show_default=True,
    help="Output format",
)
def portfolio(format):
    from bot.commands import PortfolioCommand

    user = user_from_env()
    portfolio = PortfolioCommand.execute(user)

    click.echo(utils.table_output_with_format(portfolio, format))

    import bot.market_buy

    purchase_balance = bot.market_buy.purchasing_currency_in_portfolio(user, portfolio)
    click.echo(f"\nPurchasing Balance: {utils.currency_format(purchase_balance)}")

    purchase_total = sum([coin["usd_total"] for coin in portfolio])
    click.echo(f"Portfolio Total: {utils.currency_format(purchase_total)}")


# TODO this command needs to be cleaned up with some more options
@cli.command(short_help="Convert stablecoins to USD for purchasing")
def convert():
    import bot.convert_stablecoins as convert_stablecoins
    import bot.exchanges as exchanges

    user = user_from_env()
    portfolio = exchanges.portfolio(SupportedExchanges.BINANCE, user)
    convert_stablecoins.convert_stablecoins(user, SupportedExchanges.BINANCE, portfolio)


@cli.command(
    short_help="Buy additional tokens for your index",
    help="Buys additional tokens using purchasing currency in your exchange(s)",
)
@click.option(
    "-f",
    "--format",
    type=click.Choice(["md", "csv"]),
    default="md",
    show_default=True,
    help="Output format",
)
@click.option("-d", "--dry-run", is_flag=True, help="Dry run, do not buy coins")
@click.option(
    "-p",
    "--purchase-balance",
    type=float,
    help="Dry-run with a specific amount of purchasing currency",
)
@click.option(
    "-c",
    "--convert",
    is_flag=True,
    help="Convert all stablecoin equivilents to purchasing currency. Overrides user configuration.",
)
@click.option("--cancel-orders", is_flag=True, help="Cancel all stale orders")
def buy(format, dry_run, purchase_balance, convert, cancel_orders):
    from decimal import Decimal

    from bot.commands import BuyCommand

    if purchase_balance:
        purchase_balance = Decimal(purchase_balance)
        utils.log.info("dry run using fake purchase balance", purchase_balance=purchase_balance)
        dry_run = True

    user = user_from_env()

    # if user is in testmode, assume user wants dry run
    if not dry_run and not user.livemode:
        dry_run = True

    if dry_run:
        click.secho(f"Bot running in dry-run mode\n", fg="green")

    if convert:
        user.convert_stablecoins = True

    if cancel_orders:
        user.cancel_stale_orders = True

    if dry_run:
        user.convert_stablecoins = False
        user.cancel_stale_orders = False
        user.livemode = False

    purchase_balance, market_buys, completed_orders = BuyCommand.execute(user, purchase_balance)

    click.secho(f"Purchasing Balance: {utils.currency_format(purchase_balance)}", fg="green")

    click.echo(bot.utils.table_output_with_format(market_buys, format))

    if not market_buys:
        click.secho("\nNot enough purchasing currency to make any trades.", fg="red")
    else:
        purchased_token_list = ", ".join([order["symbol"] for order in completed_orders])
        click.secho(f"\nSuccessfully purchased: {purchased_token_list}", fg="green")


if __name__ == "__main__":
    cli()
