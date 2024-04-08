#!/usr/bin/python

import random as rd

from Traders import round_0_trader

import datamodel as dm

import pandas as pd

import matplotlib.pyplot as plt


def main():
    days = (-2, -1, 0)
    Round = 1

    full_df = pd.concat(
        [
            pd.read_csv(f"Data/prices_round_{Round}_day_{day}.csv", sep=";")
            for day in days
        ]
    )

    dfs = {product: df for product, df in full_df.groupby("product")}

    products = tuple(dfs.keys())

    trader = round_0_trader.Trader()

    profit = {product: [0] for product in products}

    td = ""
    for _ in range(50):
        ods = dict()
        for a in products:
            OD = dm.OrderDepth()
            OD.buy_orders = {rd.randint(10, 20): rd.randint(1, 4)}
            OD.sell_orders = {rd.randint(5, 12): -rd.randint(1, 3)}
            ods[a] = OD

        TS = dm.TradingState(
            td,
            _,
            {},
            ods,
            {},
            {},
            {},
            dict(),
        )
        orders, _, td = trader.run(TS)
        for product in orders:
            for order in orders[product]:
                profit[product].append(
                    profit[product][-1] - order.price * order.quantity
                )
    print(profit)
    for product in products:
        plt.plot(profit[product])
        plt.savefig(f"Data/round_{Round}_{product}.pdf")
    return


main()
