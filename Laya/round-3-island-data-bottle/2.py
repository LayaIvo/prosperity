import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Load the data

file_path = 'C:/Users/ghodrati/Documents/GitHub/prosperity/Laya/round-3-island-data-bottle/trades_round_3_day_0_nn.csv'


data = pd.read_csv(file_path)
data = data['timestamp;buyer;seller;symbol;currency;price;quantity'].str.split(';', expand=True)
data.columns = ['timestamp', 'buyer', 'seller', 'symbol', 'currency', 'price', 'quantity']
data.drop(columns=['buyer', 'seller'], inplace=True)
data['timestamp'] = pd.to_numeric(data['timestamp'])
data['price'] = pd.to_numeric(data['price'])
data['quantity'] = pd.to_numeric(data['quantity'])

# Filter data for the components and the gift basket
component_data = data[data['symbol'].isin(['CHOCOLATE', 'STRAWBERRIES', 'ROSES'])]
gift_basket_data = data[data['symbol'] == 'GIFT_BASKET'][['timestamp', 'price']].rename(columns={'price': 'gift_basket_price'})

# Calculate the weighted price for the components
weights = {'CHOCOLATE': 4, 'STRAWBERRIES': 6, 'ROSES': 1}
component_data['weighted_price'] = component_data.apply(lambda row: row['price'] * weights[row['symbol']], axis=1)

# Sum up the weighted prices at each timestamp
weighted_prices = component_data.groupby('timestamp')['weighted_price'].sum().reset_index()

# Merge the weighted prices with the gift basket prices
merged_prices = pd.merge(weighted_prices, gift_basket_data, on='timestamp', how='outer')
merged_prices.sort_values('timestamp', inplace=True)
merged_prices.fillna(method='ffill', inplace=True)  # Forward fill to handle NaN values

# Plotting
plt.figure(figsize=(14, 7))
plt.plot(merged_prices['timestamp'], merged_prices['gift_basket_price'], label='Gift Basket Price', color='blue')
plt.plot(merged_prices['timestamp'], merged_prices['weighted_price'], label='Weighted Components Price', color='red')
plt.title('Price Comparison: GIFT_BASKET vs. Weighted Components')
plt.xlabel('Timestamp')
plt.ylabel('Price')
plt.legend()
plt.grid(True)
plt.show()
