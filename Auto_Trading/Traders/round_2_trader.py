import jsonpickle as jp

import statistics as stat
import math

from datamodel import Order

products = ("AMETHYSTS", "STARFRUIT")


class Parameters:
    def __init__(self, product):
        self.product = product
        if self.product == "AMETHYSTS":
            self.position_limit = 20
            self.observe = -1
            self.alpha = 0  # best
            self.std_multiplier = 0  # best
            self.running_mean = 10_000  # best
            self.running_var = 1
            self.orders = {
                4: -100,
                -4: 100,
            }  # best
        elif self.product == "STARFRUIT":
            self.position_limit = 20
            self.observe = 10
            self.alpha = 0.2
            self.std_multiplier = 0.15
            self.running_mean = None
            self.running_var = None
            self.orders = {
                3: -100,
                -3: 100,
            }

        self.mid_prices = list()
        print(product)
        print(self)
        return

    def __str__(self):
        Od = ",".join(str(p) + ":" + str(abs(self.orders[p])) for p in sorted(self.orders.keys()))
        return f"{self.product[0]}A{self.alpha}SM{self.std_multiplier}Od{Od}"


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

            ask = min(order_book.sell_orders, default=None)
            bid = max(order_book.buy_orders, default=None)

            if tD.observe:
                # Gather data if we are in observation phase
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
                    if buy_amount:
                        buy_available -= buy_amount
                        orders.append(Order(product, ask, buy_amount))

            for bid in sorted(order_book.buy_orders, reverse=True):
                if bid > tD.running_mean + std_factor:
                    bid_amount = order_book.buy_orders[bid]
                    sell_amount = min(bid_amount, sell_available)
                    if sell_amount:
                        sell_available -= sell_amount
                        orders.append(Order(product, bid, -sell_amount))

            for price in sorted(tD.orders.keys(), key=abs):
                amount = tD.orders[price]
                price = round(tD.running_mean + price * math.sqrt(tD.running_var))
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
                print(f"mean: {tD.running_mean}, var: {tD.running_var}")
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
            print(f"mean: {tD.running_mean}, var: {tD.running_var}")
        return
