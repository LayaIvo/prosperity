import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score

# Load the data from the provided files
file_day_minus_1 = "/mnt/data/prices_round_2_day_-1.csv"
file_day_0 = "/mnt/data/prices_round_2_day_0.csv"
file_day_1 = "/mnt/data/prices_round_2_day_1.csv"

data_day_minus_1 = pd.read_csv(file_day_minus_1)
data_day_0 = pd.read_csv(file_day_0)
data_day_1 = pd.read_csv(file_day_1)

# Display the first few rows of each dataframe to understand their structure
data_day_minus_1.head(), data_day_0.head(), data_day_1.head()




# Parse the data with correct delimiter
data_day_minus_1 = pd.read_csv(file_day_minus_1, delimiter=';')
data_day_0 = pd.read_csv(file_day_0, delimiter=';')
data_day_1 = pd.read_csv(file_day_1, delimiter=';')

# Combine the data
combined_data = pd.concat([data_day_minus_1, data_day_0, data_day_1], ignore_index=True)

# Display the combined dataframe's info and the first few rows to verify
combined_data.info(), combined_data.head()



# Prepare features by creating a lagged price column and other relevant features
combined_data['lagged_price'] = combined_data['ORCHIDS'].shift(1)  # lagged price as a feature

# Drop the first row since it now contains NaN due to the lagging operation
combined_data.dropna(inplace=True)

# Split data into training and testing based on the days
train_data = combined_data[(combined_data['DAY'] == -1) | (combined_data['DAY'] == 0)]
test_data = combined_data[combined_data['DAY'] == 1]

# Define the features and target variable
features = ['lagged_price', 'TRANSPORT_FEES', 'EXPORT_TARIFF', 'IMPORT_TARIFF', 'SUNLIGHT', 'HUMIDITY']
X_train = train_data[features]
y_train = train_data['ORCHIDS']
X_test = test_data[features]
y_test = test_data['ORCHIDS']

# Create and train the linear regression model
model = LinearRegression()
model.fit(X_train, y_train)

# Predict on the test set
predictions = model.predict(X_test)

# Calculate and print the model's performance metrics
mse = mean_squared_error(y_test, predictions)
r2 = r2_score(y_test, predictions)

mse, r2
