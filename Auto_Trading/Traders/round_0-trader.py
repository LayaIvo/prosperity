import jsonpickle as jp

import statistics as stat
import math

from datamodel import Order


class Trader:
    def run(self, state):
        print(state.timestamp, end=" ")
        if not state.traderData:
            tD = {
                prod: dict(
                    std_multiplier=0.5,
                    position_limit=20,
                    gather_data=10,
                    alpha=0.1,
                    run_mean=None,
                    run_var=None,
                    run_std=None,
                    mid_price=list(),
                )
                for prod in state.order_depths
            }
            # tD["AMETHYSTS"]["alpha"] = 0.1
            # tD["AMETHYSTS"]["std_multiplier"] = 0.5
            # tD["STARFRUIT"]["alpha"] = 0.1
            # tD["STARFRUIT"]["std_multiplier"] = 0.5
        else:
            tD = jp.decode(state.traderData, keys=True)

        result = dict()
        for P in state.order_depths:

            orders = []
            order_depth = state.order_depths[P]

            if tD[P]["gather_data"]:
                print("Gathering Data", end=" ")
                if order_depth.sell_orders and order_depth.buy_orders:
                    ask = min(order_depth.sell_orders)
                    bid = max(order_depth.buy_orders)
                    mid_price = (ask + bid) / 2
                    tD[P]["mid_price"].append(mid_price)
                    tD[P]["gather_data"] -= 1
                if not tD[P]["gather_data"]:
                    tD[P]["run_mean"] = stat.mean(tD[P]["mid_price"])
                    tD[P]["run_var"] = stat.variance(
                        tD[P]["mid_price"], tD[P]["run_mean"]
                    )
                    tD[P]["run_std"] = math.sqrt(tD[P]["run_var"])
                    print("Finished Gathering", end=" ")
                    print(
                        "Mean:",
                        tD[P]["run_mean"],
                        "+-",
                        tD[P]["run_std"],
                        end=" ",
                    )
                continue

            position_limit = tD[P]["position_limit"]
            position = state.position.get(P, 0)
            std_mult = tD[P]["std_multiplier"]

            if order_depth.sell_orders:
                ask = min(order_depth.sell_orders)
                ask_amount = -order_depth.sell_orders[ask]
                buy_amount = min(ask_amount, position_limit - position)
                if (
                    buy_amount
                    and ask < tD[P]["run_mean"] - std_mult * tD[P]["run_std"]
                ):
                    orders.append(Order(P, ask, buy_amount))
                    print("BUY", P, ask, buy_amount, end=" ")

            if order_depth.buy_orders:
                bid = max(order_depth.buy_orders)
                bid_amount = order_depth.buy_orders[bid]
                sell_amount = min(bid_amount, position_limit + position)
                if (
                    sell_amount
                    and bid > tD[P]["run_mean"] + std_mult * tD[P]["run_std"]
                ):
                    orders.append(Order(P, bid, -sell_amount))
                    print("SELL", P, bid, sell_amount, end=" ")

            if order_depth.buy_orders or order_depth.sell_orders:
                ask = ask if order_depth.sell_orders else tD[P]["run_mean"]
                bid = bid if order_depth.buy_orders else tD[P]["run_mean"]
                mid_price = (ask + bid) / 2
                alpha = tD[P]["alpha"]
                tD[P]["run_mean"] = (
                    alpha * mid_price + (1 - alpha) * tD[P]["run_mean"]
                )
                tD[P]["run_var"] = (
                    alpha * (mid_price - tD[P]["run_mean"]) ** 2
                    + (1 - alpha) * tD[P]["run_var"]
                )
                tD[P]["run_std"] = math.sqrt(tD[P]["run_var"])
                print("Mean:", tD[P]["run_mean"], "+-", tD[P]["run_std"])
            result[P] = orders

        return result, 0, jp.encode(tD, keys=True)
