import jsonpickle as jp

import statistics as stat
import math

from datamodel import Order

products = ("AMETHYSTS", "STARFRUIT")


class Parameters:
    def __init__(self, product):
        self.std_multiplier = 0.5 if product == "AMETHYSTS" else 0.6
        self.position_limit = 20
        self.observe = 10
        self.alpha = 0.1
        self.running_mean = None
        self.running_var = None
        self.mid_prices = list()
        self.target_inventory = 0 if product == "AMETHYSTS" else 5
        self.default_buy = 10
        self.default_sell = 10
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


   
            dynamic_spread = self.calculate_spread(product, state)             #TODO
            
            
            inventory_adjustment = (position - tD.target_inventory) * 0.05  # Adjust this factor as needed
            
            bid_price = round(tD.running_mean - (dynamic_spread / 2) - inventory_adjustment)
            ask_price = round(tD.running_mean + (dynamic_spread / 2) - inventory_adjustment)
            
            # Ensure orders respect position limits
            buy_amount = min(tD.default_buy, tD.position_limit - position)  # Simplified example
            sell_amount = min(tD.default_sell, tD.position_limit + position)  # Simplified example
            


            orders.append(Order(product, ask_price, buy_amount))
            orders.append(Order(product, bid_price, sell_amount))
    
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

    def calculate_spread(self, product, state):
        """
        Calculate the spread based on volatility, liquidity, and market depth.

        :param order_depth: An OrderDepth instance for the product.
        :param recent_prices: A list of recent prices for the product.
        :param recent_volumes: A list of recent trade volumes for the product.
        :return: A calculated spread value.
        """
        order_depth = state.order_depths[product]
        recent_prices = [trade.price for trade in state.market_trades[product]]
        recent_volumes = [trade.quantity for trade in state.market_trades[product]]



        # Calculate volatility as the standard deviation of the recent prices
        volatility = np.std(recent_prices)

        # Calculate liquidity based on the recent volumes (simplistic measure)
        liquidity = np.mean(recent_volumes)

        # Assess market depth imbalance
        total_buy_orders = sum(order_depth.buy_orders.values())
        total_sell_orders = sum(-amount for amount in order_depth.sell_orders.values())
        market_imbalance = abs(total_buy_orders - total_sell_orders) / (total_buy_orders + total_sell_orders)

        # Base spread - could start with a fixed minimum spread
        base_spread = 0.01  # 1% spread as an example

        # Adjust spread based on volatility (this factor could be tuned)
        volatility_factor = volatility * 0.05

        # Adjust spread based on liquidity (higher volumes lead to lower spread)
        liquidity_factor = 0.05 / liquidity if liquidity > 0 else 0.1  # Arbitrary example factors

        # Adjust spread for market depth imbalance
        imbalance_factor = market_imbalance * 0.05  # Arbitrary example factor

        # Calculate final spread
        spread = base_spread + volatility_factor + liquidity_factor + imbalance_factor

        return spread
