#!/usr/bin/python

from pathlib import Path

from Traders import round_1_trader_market_making, round_1_trader_reversion, round_2_trader

product = "AMETHYSTS"

params = round_2_trader.Parameters(product)

file = Path("Traders/round_2_trader.py")

new_file = file.parent / "labeled" / (str(params) + ".py")

new_file.write_text(file.read_text())
