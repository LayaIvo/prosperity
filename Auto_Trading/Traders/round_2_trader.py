import jsonpickle as jp

import math

from datamodel import Order

products = ("AMETHYSTS", "STARFRUIT", "ORCHIDS")


class Parameters:
    def __init__(self, product):

        # default values
        self.product = product
        self.methods = ()
        self.orders = dict()
        self.mid_prices = list()
        self.std_mult = 0
        self.momentum_mult = 0

        if self.product == "AMETHYSTS":
            self.methods = ("mean_reversion", "market_making")
            self.position_limit = 20
            self.price = Fixed(10_000, 1)
            self.orders = {
                4: -100,
                -4: 100,
            }
        elif self.product == "STARFRUIT":
            self.methods = ("mean_reversion", "market_making")
            self.position_limit = 20
            self.price = RunningMean([10, 20], 5)
            self.std_mult = 0.2
            self.momentum_mult = 0.3  # TODO
            self.orders = {
                3: -100,
                -3: 100,
            }
        elif self.product == "ORCHIDS":
            self.methods = ("humidity_trading",)
            self.position_limit = 100
            self.sunlight = None
            self.humidity = None
            self.price = RunningMean([20, 40], 10)
            self.std_mult = 0.2
            self.momentum_mult = 0.3

        print(product)
        print(self)
        return

    def __str__(self):
        Od = ",".join(str(p) + ":" + str(abs(self.orders[p])) for p in sorted(self.orders.keys()))
        return f"{self.product[0]}S{self.std_mult}M{self.momentum_mult}Od{Od}"


class Trader:

    def __init__(self):
        self.std = None
        self.momentum = None
        self.buy_available = None
        self.sell_available = None
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
            obs = state.observations.conversionObservations.get(product, None)

            ask = min(order_book.sell_orders, default=None)
            bid = max(order_book.buy_orders, default=None)
            tD.price.update(mid_price(bid, ask))

            position = state.position.get(product, 0)
            self.buy_available = tD.position_limit - position
            self.sell_available = tD.position_limit + position

            self.std = math.sqrt(tD.price.var) * tD.std_mult
            self.momentum = tD.price.momentum * tD.momentum_mult

            orders = []

            if "mean_reversion" in tD.methods:
                orders += self.mean_reversion(tD, order_book)

            if "market_making" in tD.methods:
                orders += self.market_making(tD)

            if "humidity_trading" in tD.methods:
                orders += self.humidity_trading(tD, obs)

            result[product] = [Order(product, *o) for o in orders]

        return result, 0, jp.encode(traderData, keys=True)

    def mean_reversion(self, tD, order_book):
        orders = []
        for ask in sorted(order_book.sell_orders):
            if ask < tD.price.mean - self.std + self.momentum:
                ask_amount = -order_book.sell_orders[ask]
                buy_amount = min(ask_amount, self.buy_available)
                if buy_amount:
                    self.buy_available -= buy_amount
                    orders.append((ask, buy_amount))
        for bid in sorted(order_book.buy_orders, reverse=True):
            if bid > tD.price.mean + self.std + self.momentum:
                bid_amount = order_book.buy_orders[bid]
                sell_amount = min(bid_amount, self.sell_available)
                if sell_amount:
                    self.sell_available -= sell_amount
                    orders.append((bid, -sell_amount))
        return orders

    def market_making(self, tD):
        orders = []
        for std_mult in sorted(tD.orders.keys(), key=abs):
            amount = tD.orders[std_mult]
            price = round(tD.price.mean + std_mult * math.sqrt(tD.price.var) + self.momentum)
            if amount > 0:
                buy_amount = min(amount, self.buy_available)
                if buy_amount:
                    self.buy_available -= buy_amount
                    orders.append((price, buy_amount))
            else:
                sell_amount = min(-amount, self.sell_available)
                if sell_amount:
                    self.sell_available -= sell_amount
                    orders.append((price, -sell_amount))
        return orders

    def humidity_trading(self, tD, obs):
        orders = []

        if tD.humidity:
            humidity_diff = obs.humidity - tD.humidity
            if humidity_diff > 0.5 and 75 < obs.humidity < 85:
                buy_amount = self.buy_available
                if buy_amount:
                    self.buy_available -= buy_amount
                    orders.append((tD.price.mean, buy_amount))
            elif humidity_diff < -0.1 and obs.humidity > 85:
                sell_amount = self.sell_available
                if sell_amount:
                    self.sell_available -= sell_amount
                    orders.append((tD.price.mean, -sell_amount))
        tD.humidity = obs.humidity
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
            self.var = self.var + ((value - self.mean) ** 2 - self.var) / self.lag
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


def mid_price(bid, ask):
    if bid or ask:
        bid = bid if bid else ask
        ask = ask if ask else bid
        return (bid + ask) / 2
    return
