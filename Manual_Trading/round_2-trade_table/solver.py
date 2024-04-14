#!/usr/bin/python

from itertools import product

currencies = ("Pizza", "Wasabi", "Snow", "Shell")

Table = [
    [1, 0.48, 1.52, 0.71],
    [2.05, 1, 3.26, 1.56],
    [0.64, 0.3, 1, 0.46],
    [1.41, 0.61, 2.08, 1],
]

max_val = 0
max_currs = None
for currs in product(range(4), repeat=4):
    currs = [3] + list(currs) + [3]
    val = 1
    for i in range(len(currs) - 1):
        val *= Table[currs[i]][currs[i + 1]]
    if val > max_val:
        max_val = val
        max_currs = currs

profit = 2_000_000 * (max_val - 1)
print(f"{round(profit)=:}", [currencies[i] for i in max_currs])
