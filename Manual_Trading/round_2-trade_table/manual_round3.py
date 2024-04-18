import numpy as np

# Settings for the game
size = 5  # Size of the game board (5x5)
money_multi = [[24,70,41,21,60],
         [47,82,87,80,35],
         [73,89,100,90,17],
         [77,83,85,79,55],
         [12,27,52,15,30]]

money = np.array(money_multi) * 7500  # Convert to thousands  
hunters = np.array([[2,4,3,2,4],
           [3,5,5,5,3],
           [4,5,8,7,2],
           [5,5,5,5,4],
           [2,3,4,2,3]])

num_players = 2000  # Total number of players, including yourself
fee = 25000  # Fee C for second choice, 3C for third choice


# Function to estimate profit based on the choice index and current player distributions
def estimate_profit(row, col, players_distribution, num_choice):
    total_players = players_distribution[row, col] 
    if num_choice == 1:
        fee_cost = 0
    elif num_choice == 2:
        fee_cost = fee
    else:
        fee_cost = 3 * fee

    profit = (money[row, col] / (hunters[row, col] + total_players)) - fee_cost
    return profit

# Simulate player choices uniformly
def simulate_choices_uniform():
    players_distribution = np.zeros((size, size))
    # Simulate random choices for other players
    for _ in range(num_players - 1):
        choice_row = np.random.choice(size)
        choice_col = np.random.choice(size)
        players_distribution[choice_row, choice_col] += 1
    players_distribution = players_distribution/num_players*100
    return players_distribution


# Simulate player choices based on the ratio of money/hunters
def simulate_choices_ratio_random():
    ratio = np.divide(money, hunters)
    players_distribution = ratio / ratio.sum() * 100
    return players_distribution


def simulate_choices():
    players_distribution = np.zeros((size, size), dtype=float)
    
    # Calculate ratio of money to hunters
    ratio = np.divide(money, hunters)
    
    # Flatten the ratio array and get indices of sorted elements (highest to lowest)
    flat_indices = np.argsort(ratio.ravel())[::-1]  # Reverse to get descending order
    
    # Get row and column indices of the best and second best entries
    best_index = np.unravel_index(flat_indices[0], (size, size))
    second_best_index = np.unravel_index(flat_indices[1], (size, size))

    # Assume some players choose the best and second best based on their attractiveness
    players_distribution[best_index] = 0.3  # 30% of players choose the best
    players_distribution[second_best_index] = 0.2  # 20% choose the second best

    # Distribute the remaining 50% of players across other cells
    remaining_percentage = 0.5
    num_other_cells = size * size - 2  # Total cells minus the two already chosen
    other_cells_distribution = np.full((size, size), remaining_percentage / num_other_cells)
    
    # Ensure that the best and second best cells are not updated
    other_cells_distribution[best_index] = 0
    other_cells_distribution[second_best_index] = 0
    
    # Add the randomly distributed remaining percentage to the players_distribution
    players_distribution += other_cells_distribution

    return players_distribution

# Simulate player choices mixed
def simulate_choices_mixed():
    players_distribution1 = simulate_choices_uniform()
    players_distribution2 = simulate_choices_ratio_random()
    players_distribution = (players_distribution1*float(10/100) + players_distribution2*float(90/100)) 
    print(players_distribution1, players_distribution2, players_distribution)
    return players_distribution

# Calculate the best choices
def find_best_choices():

    # players_distribution = simulate_choices_uniform()
    # players_distribution = simulate_choices_ratio()
    players_distribution = simulate_choices()
    profit_results = np.zeros((size, size))
    
    for row in range(size):
        for col in range(size):
            profit_results[row, col] = estimate_profit(row, col, players_distribution, 1)
    
    # Select the best initial choice
    initial_choice = np.unravel_index(np.argmax(profit_results), profit_results.shape)
    initial_profit = profit_results[initial_choice]
    
    print(f"Best initial choice: {initial_choice} with estimated profit: {initial_profit}")

    # Update distribution with your choice
    players_distribution[initial_choice] += 1
    
    # Recalculate for potential second and third choices
    second_choice_profit = np.zeros((size, size))
    for row in range(size):
        for col in range(size):
            if (row, col) != initial_choice:
                second_choice_profit[row, col] = estimate_profit(row, col, players_distribution, 2)
    
    second_choice = np.unravel_index(np.argmax(second_choice_profit), second_choice_profit.shape)
    second_profit = second_choice_profit[second_choice]
    
    if second_profit > 0:
        print(f"Profitable second choice: {second_choice} with estimated profit: {second_profit}")
    else:
        print("No profitable second choice available.")

    # Third choice considerations
    third_choice_profit = np.zeros((size, size))
    for row in range(size):
        for col in range(size):
            if (row, col) != initial_choice and (row, col) != second_choice:
                third_choice_profit[row, col] = estimate_profit(row, col, players_distribution, 3)

    third_choice = np.unravel_index(np.argmax(third_choice_profit), third_choice_profit.shape)
    third_profit = third_choice_profit[third_choice]

    if third_profit > 0:
        print(f"Profitable third choice: {third_choice} with estimated profit: {third_profit}")
    else:
        print("No profitable third choice available.")

    total_profit = initial_profit + max(0,second_profit) + max(0,third_profit)

    print(f"Total estimated profit: {total_profit}")

# Run the function
find_best_choices()


# print(np.divide(money,hunters)-75000)


# print(simulate_choices_uniform())   


# ratio = np.divide(money,hunters)
# print(ratio/ratio.sum()*100)