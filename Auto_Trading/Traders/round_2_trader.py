import jsonpickle as jp

import statistics as stat
import math

from datamodel import Order

products = ("AMETHYSTS", "STARFRUIT")


class Parameters:
    def __init__(self, product):
        # best value A=652  S=
        # best alpha A=0.15 S=0.2
        # best std   A=0.2  S=0.15
        P = product[0]
        self.product = product
        self.position_limit = 20
        self.observe = dict(A=0, S=-1)[P]
        self.alpha = dict(A=0.15, S=0.2)[P]
        self.std_multiplier = dict(A=1, S=0.15)[P]
        self.update = dict(A=False, S=True)[P]
        self.running_mean = dict(A=10_000, S=None)[P]
        self.running_var = dict(A=1, S=None)[P]
        self.constant_orders = dict(
            A={
                10003: -20,
                10002: -8,
                10001: -2,
                9999: 2,
                9998: 8,
                9997: 20,
            },
            S=dict(),
        )[P]
        self.mid_prices = list()
        print(product)
        print(self)
        return

    def __str__(self):
        CO = ".".join(
            str(abs(self.constant_orders[p])) for p in sorted(self.constant_orders.keys())
        )
        return f"{self.product[0]}A{self.alpha}SM{self.std_multiplier}CO.{CO}"


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

            tD = traderData[product]
            order_book = state.order_depths[product]

            # Gather data if we are in observation phase

            ask = min(order_book.sell_orders, default=None)
            bid = max(order_book.buy_orders, default=None)

            if tD.observe:
                self.gather_data(tD, ask, bid)
                continue
            else:
                # update running mean and variance
                self.update_running_mean_var(tD, ask, bid)

            # Trading

            orders = []

            position = state.position.get(product, 0)
            std_factor = tD.std_multiplier * math.sqrt(tD.running_var)

            buy_available = tD.position_limit - position
            sell_available = tD.position_limit + position

            for ask in sorted(order_book.sell_orders):
                if ask < tD.running_mean - std_factor:
                    ask_amount = -order_book.sell_orders[ask]
                    buy_amount = min(ask_amount, buy_available)
                    buy_available -= buy_amount
                    if buy_amount:
                        orders.append(Order(product, ask, buy_amount))

            for bid in sorted(order_book.buy_orders, reverse=True):
                if bid > tD.running_mean + std_factor:
                    bid_amount = order_book.buy_orders[bid]
                    sell_amount = min(bid_amount, sell_available)
                    sell_available -= sell_amount
                    if sell_amount:
                        orders.append(Order(product, bid, -sell_amount))

            for price, amount in tD.constant_orders.items():
                if amount > 0:
                    buy_amount = min(amount, buy_available)
                    if buy_amount:
                        buy_available -= buy_amount
                        orders.append(Order(product, price, buy_amount))
                else:
                    sell_amount = min(-amount, sell_available)
                    if sell_amount:
                        sell_available -= sell_amount
                        orders.append(Order(product, price, -sell_amount))

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
        if tD.update and (ask or bid):
            ask = ask if ask else tD.running_mean
            bid = bid if bid else tD.running_mean
            mid_price = (ask + bid) / 2
            tD.running_mean = tD.alpha * mid_price + (1 - tD.alpha) * tD.running_mean
            tD.running_var = (
                tD.alpha * (mid_price - tD.running_mean) ** 2 + (1 - tD.alpha) * tD.running_var
            )
        return
