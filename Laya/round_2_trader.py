import jsonpickle as jp

import math

from datamodel import Order


products = ("AMETHYSTS", "STARFRUIT", "ORCHIDS","STRAWBERRIES","CHOCOLATE","ROSES","GIFT_BASKET")



class Parameters:
    def __init__(self, product):

        # default values
        self.product = product
        self.methods = ()
        self.orders = dict()
        self.std_mult = 0
        self.momentum_mult = 0
        self.str = ""

        if self.product == "AMETHYSTS":
            # self.methods = ("mean_reversion", "market_making")
            self.position_limit = 20
            self.price = Fixed(10_000, 1)
            self.orders = {
                4: -100,
                -4: 100,
            }
        elif self.product == "STARFRUIT":
            # self.methods = ("mean_reversion", "market_making")
            self.position_limit = 20
            self.price = RunningMean([8, 16], 8)
            self.std_mult = 0.3
            self.momentum_mult = 0.3
            self.orders = {
                1: -100,
                -1: 100,
            }
        elif self.product == "ORCHIDS":
            self.time = 0
            # self.methods = ("mean_reversion", "market_making")
            self.position_limit = 100
            self.price = RunningMean([10, 20], 10)
            self.std_mult = 0.4
            self.momentum_mult = 0.4
            self.orders = {
                2.5: -5,
                -3: 5,
            }


        elif self.product == "CHOCOLATE":
            # self.methods = ("mean_reversion_basket",)
            self.position_limit = 250
            self.price = RunningMean([8, 16], 8)
            self.std_mult = 0.3
            self.momentum_mult = 0.3
            self.orders = {
                1: -100,
                -1: 100,
            }
        elif self.product == "ROSES":
            # self.methods = ("mean_reversion_basket",)
            self.position_limit = 60
            self.price = RunningMean([8, 16], 8)
            self.std_mult = 0.3
            self.momentum_mult = 0.3
            self.orders = {
                1: -100,
                -1: 100,
            }
        elif self.product == "STRAWBERRIES":
            # self.methods = ("mean_reversion_basket",)
            self.position_limit = 350
            self.price = RunningMean([8, 16], 8)
            self.std_mult = 0.3
            self.momentum_mult = 0.3
            self.orders = {
                1: -100,
                -1: 100,
            }
        elif self.product == "GIFT_BASKET":
            self.methods = ("mean_reversion_basket",)
            self.position_limit = 60
            self.price = RunningMean([8, 16], 8)
            self.std_mult = 0.3
            self.momentum_mult = 0.3
            self.orders = {
                1: -100,
                -1: 100,
            }
        print(product)
        print(self)
        return
    def __str__(self):
        Od = ",".join(str(p) + ":" + str(abs(self.orders[p])) for p in sorted(self.orders.keys()))
        Od = "Od" + Od if Od else ""
        return f"{self.product[0]}S{self.std_mult}M{self.momentum_mult}{self.str}{Od}"


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
            obs = state.observations.conversionObservations.get(product, None)

            ask = min(order_book.sell_orders, default=None)
            bid = max(order_book.buy_orders, default=None)
            tD.price.update(mid_price(bid, ask))

            position = state.position.get(product, 0)
            self.buy_available[product] = tD.position_limit - position
            self.sell_available[product] = tD.position_limit + position

            self.std[position] = math.sqrt(tD.price.var) * tD.std_mult
            self.momentum[position] = tD.price.momentum * tD.momentum_mult
        
        result = dict()
        for product in products:
            orders = []
            for method in tD.methods:
                if method == "mean_reversion":
                    orders += self.mean_reversion(tD, order_book)
                elif method == "market_making":
                    orders += self.market_making(tD)
                elif method == "mean_reversion_basket":
                    orders += self.mean_reversion_basket(traderData, order_book)

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


    
    def mean_reversion_basket(self, product, traderData, order_book):
        orders = []

        tD_gift = traderData["GIFT_BASKET"]
        tD_St = traderData["STRAWBERRIES"]
        tD_Ch = traderData["CHOCOLATE"]
        tD_Ro = traderData["ROSES"]
        
        weighted_sum = (tD_Ch.price.mean * 4 + tD_St.price.mean * 6 + tD_Ro.price.mean * 1)

        buy_available = self.buy_available[product]
        sell_available = self.sell_available[product]
        # diff = tD_gift.price.mean-weighted_sum


        for ask in sorted(order_book.sell_orders):
            if ask < weighted_sum+400 - self.std + self.momentum:
                ask_amount = -order_book.sell_orders[ask]
                buy_amount = min(ask_amount, self.buy_available)
                if buy_amount:
                    self.buy_available -= buy_amount
                    orders.append((ask, buy_amount))
        for bid in sorted(order_book.buy_orders, reverse=True):
            if bid > weighted_sum+400 + self.std + self.momentum:
                bid_amount = order_book.buy_orders[bid]
                sell_amount = min(bid_amount, self.sell_available)
                if sell_amount:
                    self.sell_available -= sell_amount
                    orders.append((bid, -sell_amount))
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
