import jsonpickle as jp

import math

from datamodel import Order

products = ("AMETHYSTS", "STARFRUIT", "ORCHIDS","STRAWBERRIES","CHOCOLATE","ROSES","GIFT_BASKET")


class Parameters:
    def __init__(self, product):
        self.product = product
        self.methods = []

        if self.product == "AMETHYSTS":
            self.position_limit = 20
            self.price = Fixed(mean=10_000, var=1)
            self.methods = [
                # MeanReversion(
                #     quantity=100,
                #     std_factor=0,
                #     momentum_factor=0,
                # ),
                # MarketMaking(
                #     orders={4: -100, -4: 100},
                #     momentum_factor=0,
                # ),
            ]
        elif self.product == "STARFRUIT":
            self.position_limit = 20
            self.price = MovingAverage(lags=[8, 20], momentum_lag=3)
            self.methods = [
                # MeanReversion(
                #     quantity=100,
                #     std_factor=0.2,
                #     momentum_factor=0.6,
                # ),
                # MarketMaking(
                #     orders={2: -100, -2: 100},
                #     momentum_factor=0.4,
                # ),
            ]
        elif self.product == "ORCHIDS":
            self.position_limit = 100
            self.price = MovingAverage(lags=[10, 20], momentum_lag=10)
            # self.methods = [
            #     MeanReversion(
            #         quantity=5,
            #         std_factor=0.4,
            #         momentum_factor=0.4,
            #     ),
            #     MarketMaking(
            #         orders={3: -5, -3: 5},
            #         momentum_factor=0.4,
            #     ),
            # ]
        elif self.product == "CHOCOLATE":
            # self.methods = ("mean_reversion", "market_making")
            self.position_limit = 250
            self.price = RunningMean([10, 20], 5)
            self.std_mult = 0.2
            self.momentum_mult = 0.3
            self.orders = {
                3: -100,
                -3: 100,
            }
            self.str = f"S{self.std_mult}M{self.momentum_mult}"
        elif self.product == "STRAWBERRIES":
            # self.methods = ("mean_reversion", "market_making")
            self.position_limit = 250
            self.price = RunningMean([10, 20], 5)
            self.std_mult = 0.2
            self.momentum_mult = 0.3
            self.orders = {
                3: -100,
                -3: 100,
            }
            self.str = f"S{self.std_mult}M{self.momentum_mult}"
        elif self.product == "ROSES":
            # self.methods = ("mean_reversion", "market_making")
            self.position_limit = 250
            self.price = RunningMean([10, 20], 5)
            self.std_mult = 0.2
            self.momentum_mult = 0.3
            self.orders = {
                3: -100,
                -3: 100,
            }
            self.str = f"S{self.std_mult}M{self.momentum_mult}"
        elif self.product == "GIFT_BASKET":
            self.methods = ("mean_reversion_basket")
            self.position_limit = 250
            self.price = RunningMean([10, 20], 5)
            self.std_mult = 0.2
            self.momentum_mult = 0.3
            self.orders = {
                3: -100,
                -3: 100,
            }
            self.str = f"S{self.std_mult}M{self.momentum_mult}"
        return

    def __str__(self):
        ST = self.product[0]
        ST += str(self.price)
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

    def mean_reversion_basket(self, product, params):
        orders = []
        tD_gift = self.tD["GIFT_BASKET"]
        tD_St = self.tD["STRAWBERRIES"]
        tD_Ch = self.tD["CHOCOLATE"]
        tD_Ro = self.tD["ROSES"]
        
        weighted_sum = (tD_Ch.price.mean * 4 + tD_St.price.mean * 6 + tD_Ro.price.mean * 1)

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
    

    def arbitrage(self, traderData, order_book):
        orders = []
        tD_gift = traderData["GIFT_BASKET"]
        tD_St = traderData["STRAWBERRIES"]
        tD_Ch = traderData["CHOCOLATE"]
        tD_Ro = traderData["ROSES"]
        
        weighted_sum = (tD_Ch.price.mean * 4 + tD_St.price.mean * 6 + tD_Ro.price.mean * 1)

        for ask in sorted(order_book.sell_orders):
            if ask < weighted_sum - self.std + self.momentum:
                ask_amount = -order_book.sell_orders[ask]
                buy_amount = min(ask_amount, self.buy_available)
                if buy_amount:
                    self.buy_available -= buy_amount
                    orders.append((ask, buy_amount))
        for bid in sorted(order_book.buy_orders, reverse=True):
            if bid > weighted_sum + self.std + self.momentum:
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
