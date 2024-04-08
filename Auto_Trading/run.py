#!/usr/bin/python

import random as rd

import Traders

import datamodel as dm


trader = Traders.round_0_trader.Trader()

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
