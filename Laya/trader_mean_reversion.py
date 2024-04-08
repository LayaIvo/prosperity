from datamodel import OrderDepth, UserId, TradingState, Order
from typing import List
import numpy as np
import string

class Trader:

    def run(self, state: TradingState):
        print("traderData: " + state.traderData)
        print("Observations: " + str(state.observations))

        result = {}
        position_limit = 20  # Maximum position limit for any product


        for product in state.order_depths:
            mean_price = self.calculate_mean_price(product,state.traderData)
            sd_price = self.calculate_sd_price(product,state.traderData)
            deviation_threshold = 0.05 * mean_price  # Example threshold: 5% of mean price
            
            current_position = state.position[product]
            order_depth: OrderDepth = state.order_depths[product]
            orders: List[Order] = []

            print(f"Mean price for {product}: {mean_price}")
            print("Buy Order depth : " + str(len(order_depth.buy_orders)) + ", Sell order depth : " + str(len(order_depth.sell_orders)))
    
            if len(order_depth.sell_orders) != 0:
                best_ask, best_ask_amount = list(order_depth.sell_orders.items())[0]
                if int(best_ask) < (mean_price - deviation_threshold):
                    buy_amount = min(-best_ask_amount,position_limit-current_position)
                    print("BUY", str(buy_amount) + "x", best_ask)
                    orders.append(Order(product, best_ask, buy_amount))
    
            if len(order_depth.buy_orders) != 0:
                best_bid, best_bid_amount = list(order_depth.buy_orders.items())[0]
                if int(best_bid) > (mean_price + deviation_threshold):
                    sell_amount = -1*min(best_bid_amount,position_limit+current_position)
                    print("SELL", str(sell_amount) + "x", best_bid)
                    orders.append(Order(product, best_bid, sell_amount))
            
            result[product] = orders
    
        traderData = "SAMPLE"
        conversions = 1
        return result, conversions, traderData
