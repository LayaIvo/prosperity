#!/usr/bin/python

import random as rd

from Traders import round_0_trader

import datamodel as dm

import pandas as pd


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

    trader = round_0_trader.Trader()

    return

    td = ""
    for _ in range(50):
        ods = dict()
        for a in ["A", "B"]:
            OD = dm.OrderDepth()
            OD.buy_orders = {rd.randint(10, 20): rd.randint(1, 4)}
            OD.sell_orders = {rd.randint(5, 12): rd.randint(1, 3)}
            ods[a] = OD

        TS = dm.TradingState(
            td,
            _,
            {"A": [], "B": []},
            ods,
            {"A": [], "B": []},
            {"A": [], "B": []},
            {"A": 0, "B": 0},
            dict(),
        )
        orders, _, td = trader.run(TS)
    return


main()
