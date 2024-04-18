from collections import deque

def best_trading_sequence(exchange_rates, initial_units, max_trades):
    # Number of products (nodes)
    n = len(exchange_rates)
    
    # BFS queue, stores tuples of (current product, current units of product 4, number of trades, path)
    queue = deque([(4, initial_units, 0, [(4, initial_units)])])
    
    # To track the maximum amount of product 4 we can have and corresponding path
    max_product1 = initial_units
    best_path = [(4, initial_units)]
    
    while queue:
        current_product, current_units, trades_done, path = queue.popleft()
        
        # If max trades exceeded, stop processing this path
        if trades_done >= max_trades:
            continue
        
        # Explore trades to all other products including back to product 1
        for next_product in range(1, n + 1):
            if current_product != next_product:  # Can add condition to skip useless trades if necessary
                # Calculate the units after trading to next_product
                new_units = current_units * exchange_rates[current_product-1][next_product-1]
                new_path = path + [(next_product, new_units)]
                
                # If next_product is 1, potentially update max_product1 and best_path
                if next_product == 4 and new_units > max_product1:
                    max_product1 = new_units
                    best_path = new_path
                
                # Add the new state to the queue
                queue.append((next_product, new_units, trades_done + 1, new_path))
    
    return max_product1, best_path

exchange_rates = [
    [1, 0.48, 1.52, 0.71],  # rates from product 1 to others
    [2.05, 1, 3.26, 1.56],  # rates from product 2 to others
    [0.64, 0.3, 1, 0.46],   # rates from product 3 to others
    [1.41, 0.61, 2.08, 1]    # rates from product 4 to others
]


# Starting with 100 units of product 1, allowing 5 trades
max_units, trade_sequence = best_trading_sequence(exchange_rates, 2000000, 5)
print(f"Maximum units of product 1 after 5 trades: {max_units}")
print("Trade sequence:")
for product, units in trade_sequence:
    print(f"Product {product} with {units:.2f} units")
