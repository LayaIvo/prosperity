#!/usr/bin/python

from pathlib import Path

from Traders import round_1_trader_market_making

product = "STARFRUIT"

params = round_1_trader_market_making.Parameters(product)

file = Path("Traders/round_1_trader_market_making.py")

new_file = file.parent / "labeled" / (str(params) + ".py")

new_file.write_text(file.read_text())
