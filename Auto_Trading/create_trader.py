#!/usr/bin/python

import sys

from pathlib import Path

from Traders import (
    round_1_trader_market_making,
    round_1_trader_reversion,
    round_2_trader,
    round_3_trader,
)

# clear folder
if len(sys.argv) == 2 and sys.argv[1] == "clear":
    folder = Path("Traders/labeled")
    for file in folder.glob("*.py"):
        file.unlink()
else:
    product = "GIFT_BASKET"

    params = round_3_trader.Parameters(product)

    file = Path("Traders/round_3_trader.py")

    new_file = file.parent / "labeled" / (str(params) + ".py")

    new_file.write_text(file.read_text())
