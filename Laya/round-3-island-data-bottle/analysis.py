import pandas as pd
import os
import matplotlib.pyplot as plt
from statsmodels.tsa.stattools import adfuller
import numpy as np
import statsmodels.api as sm
from statsmodels.tsa.stattools import coint



file_path = 'C:/Users/ghodrati/Documents/GitHub/prosperity/Laya/round-3-island-data-bottle/trades_round_3_day_0_nn.csv'


# Load the data
data = pd.read_csv(file_path)
data = data['timestamp;buyer;seller;symbol;currency;price;quantity'].str.split(';', expand=True)
data.columns = ['timestamp', 'buyer', 'seller', 'symbol', 'currency', 'price', 'quantity']
data.drop(columns=['buyer', 'seller'], inplace=True)
data['timestamp'] = pd.to_numeric(data['timestamp'])
data['price'] = pd.to_numeric(data['price'])
data['quantity'] = pd.to_numeric(data['quantity'])


# Calculate EMAs for each symbol
alpha = 0.2
data['ema'] = data.groupby('symbol')['price'].transform(lambda x: x.ewm(alpha=alpha, adjust=False).mean())

# chocolate_emas = data[data['symbol'] == 'CHOCOLATE'][['timestamp', 'ema', 'price']]
# rose_emas = data[data['symbol'] == 'ROSES'][['timestamp', 'ema', 'price']]
# strawberry_emas = data[data['symbol'] == 'STRAWBERRIES'][['timestamp', 'ema', 'price']]
# gift_basket_emas = data[data['symbol'] == 'GIFT_BASKET'][['timestamp', 'ema', 'price']]


# Define weights and pivot data
weights = {'CHOCOLATE': 4, 'STRAWBERRIES': 6, 'ROSES': 1}
pivot_data = data.pivot_table(index='timestamp', columns='symbol', values='ema', aggfunc='last')
pivot_data.fillna(method='ffill', inplace=True)  # Forward fill to handle NaN values

# Calculate the weighted sum of the component EMAs
pivot_data['weighted_sum'] = (pivot_data['CHOCOLATE'] * weights['CHOCOLATE'] +
                              pivot_data['STRAWBERRIES'] * weights['STRAWBERRIES'] +
                              pivot_data['ROSES'] * weights['ROSES'])

# Calculate the EMA of the weighted sum
pivot_data['weighted_ema'] = pivot_data['weighted_sum'].ewm(alpha=alpha, adjust=False).mean()

# Filter and calculate the EMA for GIFT_BASKET
gift_basket_ema = data[data['symbol'] == 'GIFT_BASKET'][['timestamp', 'ema']]
gift_basket_ema.set_index('timestamp', inplace=True)
gift_basket_ema = gift_basket_ema['ema'].ewm(alpha=alpha, adjust=False).mean().reset_index()

# Merge the EMAs on timestamp
merged_emas = pd.merge(gift_basket_ema, pivot_data.reset_index(), on='timestamp', how='outer')
merged_emas.sort_values('timestamp', inplace=True)
merged_emas.fillna(method='ffill', inplace=True)  # Forward fill to handle NaN values

# Calculate the difference
merged_emas['difference'] = merged_emas['ema'] - merged_emas['weighted_ema']

# # Plotting
# plt.figure(figsize=(14, 7))
# plt.plot(merged_emas['timestamp'], merged_emas['ema'], label='GIFT_BASKET EMA', color='blue')
# plt.plot(merged_emas['timestamp'], merged_emas['weighted_ema'], label='Weighted Components EMA', color='red')
# plt.title('EMA Comparison: GIFT_BASKET vs. Weighted Components')
# plt.xlabel('Timestamp')
# plt.ylabel('Exponential Moving Average Price')
# plt.legend()
# plt.grid(True)
# plt.show()



# Augmented Dickey-Fuller test

# Calculate the difference
merged_emas['difference'] = merged_emas['ema'] - merged_emas['weighted_ema']

# Augmented Dickey-Fuller test
adf_result = adfuller(merged_emas['difference'].dropna())

# Display ADF test results
print('ADF Statistic:', adf_result[0])
print('p-value:', adf_result[1])
print('Critical Values:', adf_result[4])



# Calculate correlations
correlations = pivot_data[['CHOCOLATE', 'ROSES', 'STRAWBERRIES']].corr()
print("Correlation Matrix:\n", correlations)

# Check for cointegration
cointegration_results = {}
products = ['CHOCOLATE', 'ROSES', 'STRAWBERRIES']

for i in range(len(products)):
    for j in range(i+1, len(products)):
        score, p_value, _ = coint(pivot_data[products[i]], pivot_data[products[j]])
        cointegration_results[f'{products[i]} and {products[j]}'] = {'score': score, 'p-value': p_value}

print("Cointegration Test Results:")
for pair, results in cointegration_results.items():
    print(f"{pair}: Score = {results['score']}, p-value = {results['p-value']}")