import jsonpickle as jp

import statistics as stat
import math

from datamodel import Order

products = ("AMETHYSTS", "STARFRUIT")


class Parameters:
    def __init__(self, product):
        P = product[0]
        self.product = product
        self.std_multiplier = 0.2
        self.position_limit = 20
        self.observe = 10
        self.alpha = dict(A=0.1, S=0.15)[P]
        self.running_mean = None
        self.running_var = None
        self.mid_prices = list()
        print(product)
        print(f"{self.alpha=} {self.std_multiplier=}")
        return

    def __str__(self):
        return f"{self.product[0]}A{self.alpha}SM{self.std_multiplier}"


class Trader:

    def __init__(self):
        return

    def run(self, state):
        if not state.traderData:
            traderData = {product: Parameters(product) for product in products}
        else:
            traderData = jp.decode(state.traderData, keys=True)

        result = dict()
        for product in products:
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
            std_factor = tD.std_multiplier * math.sqrt(tD.running_var)

            if ask and ask < tD.running_mean - std_factor:
                ask_amount = -order_book.sell_orders[ask]
                buy_amount = min(ask_amount, tD.position_limit - position)
                if buy_amount:
                    orders.append(Order(product, ask, buy_amount))

            if bid and bid > tD.running_mean + std_factor:
                bid_amount = order_book.buy_orders[bid]
                sell_amount = min(bid_amount, tD.position_limit + position)
                if sell_amount:
                    orders.append(Order(product, bid, -sell_amount))

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
            tD.running_mean = tD.alpha * mid_price + (1 - tD.alpha) * tD.running_mean
            tD.running_var = (
                tD.alpha * (mid_price - tD.running_mean) ** 2 + (1 - tD.alpha) * tD.running_var
            )
        return
