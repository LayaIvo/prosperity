#!/usr/bin/python

shift = 900
L = 100

Max = 0
i1, i2 = 0, 0
for x1 in range(1, L + 1):
    for x2 in range(x1 + 1, L + 1):
        Px1 = x1**2 / L**2
        Px2 = x2**2 / L**2
        Val = (100 - x1) * Px1 + (100 - x2) * (Px2 - Px1)
        if Val > Max:
            Max = Val
            i1, i2 = x1, x2

print(f"x1={i1+shift} x2={i2+shift} Value={Max}")
