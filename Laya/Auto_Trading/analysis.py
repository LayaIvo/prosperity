

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

df = pd.read_csv("Data/prices_round_1_day_0.csv", sep=";")

products = df["product"].unique()
inds = {P: df["product"] == P for P in products}

vecs = []
for P in products:
    vecs.append(df["mid_price"][inds[P]])
    fig, ax = plt.subplots(1, 1)
    ax.plot(vecs[-1], ".")
    fig.savefig(f"Plots/{P}_mid_price.pdf")
    fig.show()


covariance = np.cov(*vecs)
correlation = covariance[0, 1] / np.sqrt(covariance[0, 0] * covariance[1, 1])

print(correlation)

for product in products:
    fig, ax = plt.subplots(1, 1)
    inds = df["product"] == product
    data = df["ask_price_1"][inds]-df["bid_price_1"][inds]
    ax.plot(data, ".")
    fig.savefig(f"Plots/{product}_spread.pdf")

vecs = []
fig, ax = plt.subplots(1, 1)
for product in products:
    inds = df["product"] == product
    data = np.diff(df["mid_price"][inds])
    vecs.append(data)
    ax.plot(vecs[-1], ".")
    fig.savefig("Plots/diff_mid_price.pdf")

covariance = np.cov(vecs[0], vecs[1])
correlation = covariance[0, 1] / np.sqrt(covariance[0, 0] * covariance[1, 1])

print(correlation)

vecs = []
for product in products:
    fig, ax = plt.subplots(1, 1)
    inds = df["product"] == product
    data = df["profit_and_loss"][inds]
    vecs.append(data)
    ax.plot(vecs[-1], ".")
    fig.savefig(f"Plots/{product}_return.pdf")
