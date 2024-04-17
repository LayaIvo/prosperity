import jsonpickle as jp

import math

from datamodel import Order

products = ("AMETHYSTS", "STARFRUIT", "ORCHIDS")


class Parameters:
    def __init__(self, product):

        self.product = product
        self.methods = []

        if self.product == "AMETHYSTS":
            self.position_limit = 20
            self.price = Fixed(mean=10_000, var=1)
            self.methods = [
                MeanReversion(
                    quantity=100,
                    std_factor=0,
                    momentum_factor=0,
                ),
                MarketMaking(
                    orders={4: -100, -4: 100},
                    momentum_factor=0,
                ),
            ]
        elif self.product == "STARFRUIT":
            self.position_limit = 20
            self.price = MovingAverage(lags=[10, 20], momentum_lag=10)
            self.methods = [
                MeanReversion(
                    quantity=100,
                    std_factor=0.3,
                    momentum_factor=0.7,
                ),
                MarketMaking(
                    orders={2: -100, -2: 100},
                    momentum_factor=0.4,
                ),
            ]
        elif self.product == "ORCHIDS":
            self.position_limit = 100
            self.price = MovingAverage(lags=[10, 20], momentum_lag=10)
            self.methods = [
                MeanReversion(
                    quantity=5,
                    std_factor=0.4,
                    momentum_factor=0.4,
                ),
                MarketMaking(
                    orders={3: -5, -3: 5},
                    momentum_factor=0.4,
                ),
            ]
        return

    def __str__(self):
        ST = self.product[0]
        for method in self.methods:
            ST += f"{str(method)}"
        return ST


class Trader:

    def run(self, state):

        # Variable initialization
        self.order_book = state.order_depths
        self.obs = state.observations.conversionObservations
        self.buy_available = dict()
        self.sell_available = dict()
        # Load the saved data from the previous time step
        if not state.traderData:
            self.tD = {P: Parameters(P) for P in products}
        else:
            self.tD = jp.decode(state.traderData, keys=True)

        # Update the price and available quantities for each product
        for P in products:
            position = state.position.get(P, 0)
            self.buy_available[P] = self.tD[P].position_limit - position
            self.sell_available[P] = self.tD[P].position_limit + position

            bid = max(self.order_book[P].buy_orders, default=None)
            ask = min(self.order_book[P].sell_orders, default=None)
            self.tD[P].price.update(mid_price(bid, ask))

        # Execute the trading strategies
        result = dict()
        for P in products:
            orders = []
            for method in self.tD[P].methods:
                o, close = getattr(self, method.name)(P, method)
                orders += o
                if close:
                    break

            result[P] = orders

        return result, 0, jp.encode(self.tD, keys=True)

    # Mean reversion strategy
    def mean_reversion(self, product, params):
        order_book = self.order_book[product]
        tD = self.tD[product]
        orders = []
        limit = params.quantity
        for ask in sorted(order_book.sell_orders):
            if ask < buy(
                tD.price,
                params.std_factor,
                params.momentum_factor,
            ):
                ask_amount = -order_book.sell_orders[ask]
                buy_amount = min(limit, ask_amount, self.buy_available[product])
                if buy_amount:
                    self.buy_available[product] -= buy_amount
                    limit -= buy_amount
                    orders.append(Order(product, ask, buy_amount))
        for bid in sorted(order_book.buy_orders, reverse=True):
            if bid > sell(
                tD.price,
                params.std_factor,
                params.momentum_factor,
            ):
                bid_amount = order_book.buy_orders[bid]
                sell_amount = min(
                    limit, bid_amount, self.sell_available[product]
                )
                if sell_amount:
                    self.sell_available[product] -= sell_amount
                    limit -= sell_amount
                    orders.append(Order(product, bid, -sell_amount))
        return orders, False

    # Market making strategy
    def market_making(self, product, params):
        tD = self.tD[product]
        orders = []
        for std_mult in sorted(params.orders.keys(), key=abs):
            amount = params.orders[std_mult]
            price = sell(tD.price, std_mult, params.momentum_factor)
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
        return orders, False


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
        elif value is not None:
            self.mean = self.mean + (value - self.mean) / self.lag
            self.var = (
                self.var + ((value - self.mean) ** 2 - self.var) / self.lag
            )
        return


class MovingAverage:
    def __init__(self, lags, momentum_lag):
        self.lags = [Running(lag) for lag in lags]
        self._momentum = Running(momentum_lag)
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


def buy(price, std, mom):
    return round(price.mean - math.sqrt(price.var) * std + price.momentum * mom)


def sell(price, std, mom):
    return round(price.mean + math.sqrt(price.var) * std + price.momentum * mom)


def mid_price(bid, ask):
    if bid or ask:
        bid = bid if bid else ask
        ask = ask if ask else bid
        return (bid + ask) / 2
    return


class MeanReversion:
    def __init__(self, quantity, std_factor, momentum_factor):
        self.name = "mean_reversion"
        self.quantity = quantity
        self.std_factor = std_factor
        self.momentum_factor = momentum_factor
        return

    def __str__(self):
        return f"MR{self.quantity}S{self.std_factor}M{self.momentum_factor}"


class MarketMaking:
    def __init__(self, orders, momentum_factor):
        self.name = "market_making"
        self.orders = orders
        self.momentum_factor = momentum_factor
        return

    def __str__(self):
        orders = ",".join(
            f"{std}:{self.orders[std]}" for std in sorted(self.orders)
        )
        return f"MM{orders}M{self.momentum_factor}"
