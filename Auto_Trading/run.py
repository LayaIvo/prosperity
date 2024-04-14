#!/usr/bin/python

import random as rd

from Traders import round_0_trader, round_1_trader_market_making, round_2_trader

import datamodel as dm

import pandas as pd

import matplotlib.pyplot as plt


def main():
    days = (-1, 0, 1)
    Round = 2

    df = pd.concat(
        [pd.read_csv(f"Data/prices_round_{Round}_day_{day}.csv", sep=";") for day in days]
    )

    # dfs = {product: df for product, df in full_df.groupby("product")}

    product = "ORCHIDS"

    # trader = round_0_trader.Trader()
    # trader = round_1_trader_market_making.Trader()
    trader = round_2_trader.Trader()

    # profit = {product: [0] for product in products}
    profit = [0]
    pos = 0

    td = round_2_trader.Parameters(product)
    for i, row in df.iterrows():
        trader.buy_available = 100 - pos
        trader.sell_available = 100 + pos
        td.price.lags[0].mean = row["ORCHIDS"]
        obs = dm.ConversionObservation(*[0] * 5, row["SUNLIGHT"], row["HUMIDITY"])
        orders = trader.humidity_trading(td, obs)
        prof = profit[-1]
        q = 0
        for order in orders:
            q += order[1]
            prof -= order[0] * order[1]
        pos += q
        profit.append(prof)
        if q:
            print(i, profit[-1], pos)
    print(profit[-1], pos)
    plt.plot(profit)
    plt.savefig(f"Plots/round_{Round}.pdf")
    return


main()
