import pandas as pd
import os
import matplotlib.pyplot as plt

import numpy as np

# import pyexcel as p

# # Specify the path to your ODS file
# ods_file_path = "C:/Users/laya7/Desktop/Prosperity/data.ods"

# # Specify the path for the output CSV file


# csv_file_path = 'C:/Users/laya7/Desktop/Prosperity/data.csv'

# # Read the ODS file
# records = p.get_records(file_name=ods_file_path)

# # Save the data to a CSV file
# p.save_as(records=records, dest_file_name=csv_file_path)



csv_file_path = 'C:/Users/laya7/Desktop/Prosperity/data.csv'
df = pd.read_csv(csv_file_path)

print(df.head(5))

# product_names = df['product'].unique()

# print(product_names[0])

# mid_price = df[df['product']==str(product_names[0])][['mid_price']]

# plt.plot(mid_price,'.')
# plt.show()


# Filter the DataFrame for each product

criteria = 'bid_price_1'
amethysts_df = df[df['product'] == 'AMETHYSTS'][['timestamp', criteria]].set_index('timestamp')
starfruit_df = df[df['product'] == 'STARFRUIT'][['timestamp', criteria]].set_index('timestamp')

# Merge the DataFrames on timestamp
merged_df = amethysts_df.merge(starfruit_df, on='timestamp', suffixes=('_amethysts', '_starfruit'))

# Calculate the Pearson correlation coefficient for bid_price_1 between the two products
correlation = merged_df.diff().corr().iloc[0, 1]
print(correlation)


# Calculate rolling mean (simple moving average) and volatility (standard deviation) for bid prices
rolling_window = 20  # Example window size for rolling calculations

# Calculate rolling statistics for AMETHYSTS
amethysts_df[f'{criteria}_sma'] = amethysts_df[criteria].rolling(window=rolling_window).mean()
amethysts_df[f'{criteria}_vol'] = amethysts_df[criteria].rolling(window=rolling_window).std()

# Calculate rolling statistics for STARFRUIT
starfruit_df[f'{criteria}_sma'] = starfruit_df[criteria].rolling(window=rolling_window).mean()
starfruit_df[f'{criteria}_vol'] = starfruit_df[criteria].rolling(window=rolling_window).std()

# Plotting the trends and volatility
fig, axs = plt.subplots(2, 2, figsize=(14, 10))

# Trends
axs[0, 0].plot(amethysts_df.index, amethysts_df[criteria], label='AMETHYSTS Bid Price')
axs[0, 0].plot(amethysts_df.index, amethysts_df[f'{criteria}_sma'], label='SMA', linestyle='--')
axs[0, 0].set_title('AMETHYSTS Bid Price Trend')
axs[0, 0].legend()

axs[0, 1].plot(starfruit_df.index, starfruit_df[criteria], label='STARFRUIT Bid Price')
axs[0, 1].plot(starfruit_df.index, starfruit_df[f'{criteria}_sma'], label='SMA', linestyle='--')
axs[0, 1].set_title('STARFRUIT Bid Price Trend')
axs[0, 1].legend()

# Volatility
axs[1, 0].plot(amethysts_df.index, amethysts_df[f'{criteria}_vol'], label='AMETHYSTS Bid Price Volatility')
axs[1, 0].set_title('AMETHYSTS Bid Price Volatility')
axs[1, 0].legend()

axs[1, 1].plot(starfruit_df.index, starfruit_df[f'{criteria}_vol'], label='STARFRUIT Bid Price Volatility')
axs[1, 1].set_title('STARFRUIT Bid Price Volatility')
axs[1, 1].legend()

plt.tight_layout()
plt.show()



# Calculate the 20-day SMA and standard deviation
amethysts_df['20d_sma'] = amethysts_df['bid_price_1'].rolling(window=20).mean()
amethysts_df['std_dev'] = amethysts_df['bid_price_1'].rolling(window=20).std()

print(amethysts_df['20d_sma'],amethysts_df['std_dev'])

# Determine entry signals
amethysts_df['buy_signal'] = np.where(amethysts_df['bid_price_1'] < (amethysts_df['20d_sma'] - 2 * amethysts_df['std_dev']), 1, 0)
amethysts_df['sell_signal'] = np.where(amethysts_df['bid_price_1'] > (amethysts_df['20d_sma'] + 2 * amethysts_df['std_dev']), 1, 0)

# Assuming exit strategy is when price returns to the mean
amethysts_df['exit_signal'] = np.where((amethysts_df['buy_signal'].shift(1) == 1) & (amethysts_df['bid_price_1'] > amethysts_df['20d_sma']), 'exit_buy', 
                             np.where((amethysts_df['sell_signal'].shift(1) == 1) & (amethysts_df['bid_price_1'] < amethysts_df['20d_sma']), 'exit_sell', np.nan))





