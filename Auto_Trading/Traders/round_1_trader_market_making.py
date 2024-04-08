import jsonpickle as jp

import statistics as stat
import numpy as np

import math

from datamodel import Order

products = ("AMETHYSTS", "STARFRUIT")


class Parameters:
    def __init__(self, product):
        self.position_limit = 20
        self.observe = 10
        self.alpha = 0.1
        self.default_buy_amount = 10 if product == "AMETHYSTS" else 1
        self.default_sell_amount = 10 if product == "AMETHYSTS" else 1
        self.target_inventory = 0 if product == "AMETHYSTS" else 0
        self.inventory_factor = 0.05 if product == "AMETHYSTS" else 0.05
        self.spread_factors = dict(
            base=0,
            deviation=0.25,
            volatility=0.5,
            liquidity=0.05,
            imbalance=0.05,
        )
        self.running_mean = None
        self.running_var = None
        self.mid_prices = list()
        return


class Trader:

    def __init__(self):
        return

    def run(self, state):
        if not state.traderData:
            traderData = {
                product: Parameters(product) for product in products
            }
        else:
            traderData = jp.decode(state.traderData, keys=True)

        result = dict()
        for product in ["AMETHYSTS"]:
            orders = []

            tD = traderData[product]
            order_book = state.order_depths[product]

            ask = min(order_book.sell_orders, default=None)
            bid = max(order_book.buy_orders, default=None)

            # gather data if we are still in the observation phase
            if tD.observe:
                self.gather_data(tD, ask, bid)
                continue

            position = state.position.get(product, 0)

            dynamic_spread = self.calculate_spread(
                tD,
                order_book,
                state.market_trades.get(product, []),
                state.own_trades.get(product, []),
            )
            print(f"{dynamic_spread=}")

            # Adjust this factor as needed
            inventory_adjustment = (position - tD.target_inventory) * tD.inventory_factor

            bid_price = round(tD.running_mean - (dynamic_spread / 2) - inventory_adjustment)
            ask_price = round(tD.running_mean + (dynamic_spread / 2) - inventory_adjustment)

            # Ensure orders respect position limits
            buy_amount = min(tD.default_buy_amount, tD.position_limit - position)  # Simplified example
            sell_amount = min(tD.default_sell_amount, tD.position_limit + position)  # Simplified example

            orders.append(Order(product, ask_price, buy_amount))
            orders.append(Order(product, bid_price, -sell_amount))

            # update running mean and variance
            self.update_running_mean_var(tD, ask, bid)
            result[product] = orders

        return result, 0, jp.encode(traderData, keys=True)

    def gather_data(self, tD, ask, bid):
        # only gather data if both ask and bid are present in order book
        if ask and bid:
            mid_price = (ask + bid) / 2
            tD.mid_prices.append(mid_price)
            tD.observe -= 1
            # calculate mean and variance now that we have enough data
            if not tD.observe:
                tD.running_mean = stat.mean(tD.mid_prices)
                tD.running_var = stat.variance(tD.mid_prices, tD.running_mean)
        return

    def update_running_mean_var(self, tD, ask, bid):
        if ask or bid:
            ask = ask if ask else tD.running_mean
            bid = bid if bid else tD.running_mean
            mid_price = (ask + bid) / 2
            tD.running_mean = (
                tD.alpha * mid_price + (1 - tD.alpha) * tD.running_mean
            )
            tD.running_var = (
                tD.alpha * (mid_price - tD.running_mean) ** 2
                + (1 - tD.alpha) * tD.running_var
            )
        return

    def calculate_spread(self, tD, order_book, market_trades, own_trades):
        recent_prices = [trade.price for trade in market_trades + own_trades]
        recent_volumes = [
            trade.quantity for trade in market_trades + own_trades
        ]

        deviation = math.sqrt(tD.running_var)

        # Calculate volatility as the standard deviation of the recent prices
        volatility = np.std(recent_prices)

        # Calculate liquidity based on the recent volumes (simplistic measure)
        liquidity = np.mean(recent_volumes)

        # Assess market depth imbalance
        total_buy_orders = sum(order_book.buy_orders.values())
        total_sell_orders = sum(
            -amount for amount in order_book.sell_orders.values()
        )

        market_imbalance = abs(total_buy_orders - total_sell_orders) / (
            total_buy_orders + total_sell_orders
        )

        # Calculate final spread
        spread = (
            tD.spread_factors["base"]
            + deviation * tD.spread_factors["deviation"]
            + volatility * tD.spread_factors["volatility"]
            + liquidity * tD.spread_factors["liquidity"]
            + market_imbalance * tD.spread_factors["imbalance"]
        )

        return spread
