import jsonpickle as jp

import math

from datamodel import Order


products = (
    "AMETHYSTS",
    "STARFRUIT",
    "ORCHIDS",
    "STRAWBERRIES",
    "CHOCOLATE",
    "ROSES",
    "GIFT_BASKET",
)


class Parameters:
    def __init__(self, product):

        # default values
        self.product = product
        self.methods = []
        self.orders = dict()
        self.std_mult = 0
        self.momentum_mult = 0.2

        self.price = RunningMean([8, 16], 4)

        if product == "AMETHYSTS":
            self.position_limit = 20
            self.methods = ["mean_reversion", "market_making"]
            self.price = Fixed(10_000, 1)
            self.std_mult = 0
            self.momentum_mult = 0
            self.orders = {4: -100, -4: 100}
        elif product == "STARFRUIT":
            self.position_limit = 20
            self.methods = ["mean_reversion", "market_making"]
            self.std_mult = 0.3
            self.momentum_mult = 0.3
            self.orders = {1: -100, -1: 100}
        elif product == "ORCHIDS":
            self.position_limit = 100
        elif product == "CHOCOLATE":
            self.position_limit = 250
        elif product == "ROSES":
            self.position_limit = 60
        elif product == "STRAWBERRIES":
            self.position_limit = 350
        elif product == "GIFT_BASKET":
            self.position_limit = 60
            # market_making_basket
            self.methods = ["mean_reversion_basket"]
            self.std_mult = 0.3
            self.orders = {1: -100, -1: 100}

        print(product)
        print(self)
        return

    def __str__(self):
        Od = ",".join(
            str(p) + ":" + str(abs(self.orders[p]))
            for p in sorted(self.orders.keys(), key=abs)[:2]
        )
        Od = "Od" + Od if Od else ""
        return f"{self.product[0]}{str(self.price)}S{self.std_mult}M{self.momentum_mult}{Od}"


class Trader:

    def __init__(self):
        self.std = dict()
        self.momentum = dict()
        self.buy_available = dict()
        self.sell_available = dict()

        return

    def run(self, state):
        if not state.traderData:
            traderData = {product: Parameters(product) for product in products}
        else:
            traderData = jp.decode(state.traderData, keys=True)

        for product in products:

            tD = traderData[product]
            order_book = state.order_depths[product]

            ask = min(order_book.sell_orders, default=None)
            bid = max(order_book.buy_orders, default=None)
            tD.price.update(mid_price(bid, ask))

            position = state.position.get(product, 0)
            self.buy_available[product] = tD.position_limit - position
            self.sell_available[product] = tD.position_limit + position

            self.std[product] = math.sqrt(tD.price.var) * tD.std_mult
            self.momentum[product] = tD.price.momentum * tD.momentum_mult

        result = dict()
        orders = []
        for product in products:
            result[product] = []
            tD = traderData[product]
            order_book = state.order_depths[product]
            for method in tD.methods:
                if method == "mean_reversion":
                    orders += self.mean_reversion(product, tD, order_book)
                elif method == "market_making":
                    orders += self.market_making(product, tD)
                elif method == "mean_reversion_basket":
                    orders += self.mean_reversion_basket(
                        product, traderData, order_book
                    )
                elif method == "market_making_basket":
                    orders += self.market_making_basket(product, traderData)

        for order in orders:
            result[order.symbol].append(order)

        return result, 0, jp.encode(traderData, keys=True)

    def mean_reversion(self, product, tD, order_book):
        orders = []
        for ask in sorted(order_book.sell_orders):
            bias = -self.std[product] + self.momentum[product]
            if ask < tD.price.mean + bias:
                ask_amount = -order_book.sell_orders[ask]
                buy_amount = min(ask_amount, self.buy_available[product])
                if buy_amount:
                    self.buy_available[product] -= buy_amount
                    orders.append(Order(product, ask, buy_amount))
        for bid in sorted(order_book.buy_orders, reverse=True):
            bias = self.std[product] + self.momentum[product]
            if bid > tD.price.mean + bias:
                bid_amount = order_book.buy_orders[bid]
                sell_amount = min(bid_amount, self.sell_available[product])
                if sell_amount:
                    self.sell_available[product] -= sell_amount
                    orders.append(Order(product, bid, -sell_amount))
        return orders

    def market_making(self, product, tD):
        orders = []
        for std_mult in sorted(tD.orders.keys(), key=abs):
            amount = tD.orders[std_mult]
            price = round(
                tD.price.mean
                + std_mult * math.sqrt(tD.price.var)
                + self.momentum[product]
            )
            if amount > 0:
                buy_amount = min(amount, self.buy_available[product])
                if buy_amount:
                    self.buy_available[product] -= buy_amount
                    orders.append(Order(product, price, buy_amount))
            else:
                sell_amount = min(-amount, self.sell_available[product])
                if sell_amount:
                    self.sell_available[product] -= sell_amount
                    orders.append(Order(product, price, -sell_amount))
        return orders

    def mean_reversion_basket(self, product, tD, order_book):

        weights = {
            "GIFT_BASKET": 1,
            "CHOCOLATE": -4,
            "STRAWBERRIES": -6,
            "ROSES": -1,
        }
        diff = sum(w * tD[p].price.mean for p, w in weights.items())
        diff -= 400

        w = weights[product]
        price = tD[product].price.mean
        compare_price = price - diff / w

        orders = []
        for ask in sorted(order_book.sell_orders):
            bias = -self.std[product] + self.momentum[product]
            if ask < compare_price + bias:
                ask_amount = -order_book.sell_orders[ask]
                buy_amount = min(ask_amount, self.buy_available[product])
                if buy_amount:
                    self.buy_available[product] -= buy_amount
                    orders.append(Order(product, ask, buy_amount))
        for bid in sorted(order_book.buy_orders, reverse=True):
            bias = self.std[product] + self.momentum[product]
            if bid > compare_price + bias:
                bid_amount = order_book.buy_orders[bid]
                sell_amount = min(bid_amount, self.sell_available[product])
                if sell_amount:
                    self.sell_available[product] -= sell_amount
                    orders.append(Order(product, bid, -sell_amount))
        return orders

    def market_making_basket(self, product, tD, trade_opposite=False):

        weights = {
            "GIFT_BASKET": 1,
            "CHOCOLATE": -4,
            "STRAWBERRIES": -6,
            "ROSES": -1,
        }
        diff = sum(w * tD[p].price.mean for p, w in weights.items())
        diff -= 400

        w = weights[product]
        price = tD[product].price.mean
        compare_price = price - diff / w

        orders = []
        for std_mult in sorted(tD[product].orders.keys(), key=abs):
            amount = tD[product].orders[std_mult]
            price = round(
                compare_price
                + std_mult * math.sqrt(tD[product].price.var)
                + self.momentum[product]
            )
            if amount > 0:
                buy_amount = min(amount, self.buy_available[product])
                if buy_amount:
                    self.buy_available[product] -= buy_amount
                    orders.append(Order(product, price, buy_amount))
                for alt in weights.keys():
                    if not trade_opposite or alt == "GIFT_BASKET":
                        continue
                    sell_amount = min(
                        -buy_amount * weights[alt], self.sell_available[alt]
                    )
                    price = round(
                        tD[alt].price.mean
                        - std_mult * math.sqrt(tD[alt].price.var)
                        + self.momentum[alt]
                    )
                    if sell_amount:
                        self.sell_available[alt] -= sell_amount
                        orders.append(Order(alt, price, -sell_amount))
            else:
                sell_amount = min(-amount, self.sell_available[product])
                if sell_amount:
                    self.sell_available[product] -= sell_amount
                    orders.append(Order(product, price, -sell_amount))
                for alt in weights.keys():
                    if not trade_opposite or alt == "GIFT_BASKET":
                        continue
                    buy_amount = min(
                        -sell_amount * weights[alt], self.buy_available[alt]
                    )
                    price = round(
                        tD[alt].price.mean
                        - std_mult * math.sqrt(tD[alt].price.var)
                        + self.momentum[alt]
                    )
                    if buy_amount:
                        self.buy_available[alt] -= buy_amount
                        orders.append(Order(alt, price, buy_amount))
        return orders


class Fixed:
    def __init__(self, mean, var):
        self.mean = mean
        self.var = var
        return

    @property
    def momentum(self):
        return 0

    def update(self, value):
        return

    def __str__(self):
        return f"Fx{self.mean}"


class Running:
    def __init__(self, lag, mean=None, var=None):
        self.lag = lag
        self.mean = mean
        self.var = var
        return

    def update(self, value):
        if self.mean is None:
            self.mean = value
            self.var = 0
        else:
            self.mean = self.mean + (value - self.mean) / self.lag
            self.var = (
                self.var + ((value - self.mean) ** 2 - self.var) / self.lag
            )
        return


class RunningMean:
    def __init__(self, lags, momentum):
        self.lags = [Running(lag) for lag in lags]
        self._momentum = Running(momentum)
        return

    @property
    def mean(self):
        return self.lags[0].mean

    @property
    def var(self):
        return self.lags[0].var

    @property
    def momentum(self):
        return self._momentum.mean

    def update(self, value):
        for lag in self.lags:
            lag.update(value)
        self._momentum.update(self.lags[0].mean - self.lags[1].mean)
        return

    def __str__(self):
        return f"L{self.lags[0].lag}ML{self._momentum.lag}"


def mid_price(bid, ask):
    if bid or ask:
        bid = bid if bid else ask
        ask = ask if ask else bid
        return (bid + ask) / 2
    return
