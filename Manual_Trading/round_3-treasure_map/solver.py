#!/usr/bin/python

import math
import numpy as np
from tabulate import tabulate
from itertools import combinations


_lambda = 2


def main():
    # basket_ranking()
    run(greedy, recency_bias=0.05, noise=0.01)
    run(exponential, recency_bias=0.05, noise=0.01)
    run(softmax)
    run(square)
    run(proportional)
    run(uniform)
    return


def basket_ranking():
    basket_size = 2
    value, hunters = data()
    basket, cost, K = get_baskets(value, hunters, basket_size)

    rBasket0 = K.T @ (value / hunters) - cost

    best_inds = np.argsort(-rBasket0)
    print("Best baskets:")
    for i in range(200):
        print(f"{i+1} - {basket[best_inds[i]]} - {rBasket0[best_inds[i]]}")
    return


def run(method, D=100, recency_bias=0.5, noise=0.05):

    basket_size = 3
    value, hunters = data()
    basket, cost, K = get_baskets(value, hunters, basket_size)
    L = len(basket)

    rBasket0 = K.T @ (value / hunters) - cost

    base_return_inds = np.argsort(np.argsort(-rBasket0)) + 1

    def get_return(pBasket):
        proportion = K @ pBasket
        population = hunters + 100 * proportion
        return (value / population) @ K - cost

    def iterate_distribution(pBasket, rBasket):
        dist = method(rBasket) * recency_bias + pBasket * (1 - recency_bias)
        dist += noise * np.random.randn(L) * np.std(dist)
        dist = np.abs(dist)
        dist /= np.sum(dist)
        return dist

    # initial distribution
    pBasket = abs(np.random.randn(L))
    pBasket /= np.sum(pBasket)

    for _ in range(D):
        rBasket = get_return(pBasket)
        _pBasket = iterate_distribution(pBasket, rBasket)
        diff = np.linalg.norm(pBasket - _pBasket)
        pBasket = _pBasket

    print(f"\n{method.__name__}\nDiff: {diff:.4f}")

    # order_ind = np.arange(L)
    order_ind = np.argsort(-rBasket)

    dic = [
        ("Distribution", pBasket),
        ("Basket", basket),
        ("", base_return_inds),
        ("Ini R", rBasket0),
        ("Fin R", rBasket),
    ]

    vec = [x[1][order_ind][:25] for x in dic]
    vec = [k for k in zip(*vec)]
    headers = [x[0] for x in dic]
    print(tabulate(vec, headers=headers))
    return


def greedy(weights):
    max_index = np.argmax(weights)
    dist = np.zeros_like(weights)
    dist[max_index] = 1
    return dist


def proportional(weights):
    return weights / np.sum(weights)


def square(weights):
    dist = weights**2
    return dist / np.sum(dist)


def softmax(weights):
    dist = np.exp(_lambda * weights)
    return dist / np.sum(dist)


def exponential(weights):
    inds = np.argsort(-weights)
    dist = np.zeros_like(weights)
    dist[inds] = np.exp(-_lambda * np.arange(len(weights)))
    return dist / np.sum(dist)


def uniform(weights):
    return np.ones_like(weights) / len(weights)


def get_baskets(value, hunters, basket_size=3):
    costs = {
        1: 0,
        2: 25000 / 7500,
        3: 75000 / 7500,
    }

    n_items = len(value)
    n_combs = sum(math.comb(n_items, n) for n in range(1, basket_size + 1))

    basket = np.full(n_combs, "", dtype="object")
    cost = np.zeros(n_combs, dtype=np.float32)
    K = np.zeros((n_items, n_combs), dtype=np.uint8)

    items = np.arange(n_items)
    c = 0
    for n in range(1, basket_size + 1):
        for comb in combinations(items, n):
            cost[c] = costs[n]
            basket[c] = ",".join([f"{value[i]}:{hunters[i]}" for i in comb])
            for i in comb:
                K[i, c] = 1
            c += 1

    return basket, cost, K


def data():
    hunters = np.array(
        [
            2,
            4,
            3,
            2,
            4,
            3,
            5,
            5,
            5,
            3,
            4,
            5,
            8,
            7,
            2,
            5,
            5,
            5,
            5,
            4,
            2,
            3,
            4,
            2,
            3,
        ],
        dtype=np.uint8,
    )
    value = np.array(
        [
            24,
            70,
            41,
            21,
            60,
            47,
            82,
            87,
            80,
            35,
            73,
            89,
            100,
            90,
            17,
            77,
            83,
            85,
            79,
            55,
            12,
            27,
            52,
            15,
            30,
        ],
        dtype=np.uint8,
    )
    return value, hunters


main()
