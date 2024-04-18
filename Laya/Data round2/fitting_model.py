import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score,mean_absolute_error
from statsmodels.tsa.arima.model import ARIMA


# Load the data from the provided files
file_day_minus_1 = "C:/Users/laya7/Documents/GitHub/prosperity/Laya/Data_round2/prices_round_2_day_-1.csv"
file_day_0 = "C:/Users/laya7/Documents/GitHub/prosperity/Laya/Data_round2/prices_round_2_day_0.csv"
file_day_1 = "C:/Users/laya7/Documents/GitHub/prosperity/Laya/Data_round2/prices_round_2_day_1.csv"

data_day_minus_1 = pd.read_csv(file_day_minus_1,sep=';')
data_day_0 = pd.read_csv(file_day_0,sep=';')
data_day_1 = pd.read_csv(file_day_1,sep=';')

# Display the first few rows of each dataframe to understand their structure
data_day_minus_1.head(), data_day_0.head(), data_day_1.head()

print(data_day_minus_1.head())

print(data_day_minus_1.columns)

# Prepare the data for each day
humidity_day_minus_1 = data_day_minus_1['HUMIDITY']
sunlight_day_minus_1 = data_day_minus_1['SUNLIGHT']
humidity_day_0 = data_day_0['HUMIDITY']
sunlight_day_0 = data_day_0['SUNLIGHT']
humidity_day_1 = data_day_1['HUMIDITY']
sunlight_day_1 = data_day_1['SUNLIGHT']

# Fit ARIMA models with sunlight as an exogenous variable for each day
model_day_minus_1 = ARIMA(humidity_day_minus_1, order=(1, 0, 1), exog=sunlight_day_minus_1)
results_day_minus_1 = model_day_minus_1.fit()

def evaluate_model(model_results, humidity, sunlight):
    fitted_values = model_results.predict(start=0, end=len(humidity)-1, exog=sunlight)  # Predict using the fitted model
    mae = mean_absolute_error(humidity, fitted_values)
    mse = mean_squared_error(humidity, fitted_values)
    return mae, mse

# Evaluate the model fitted on Day -1 on Day 0 and Day 1 data
mae_day_0, mse_day_0 = evaluate_model(results_day_minus_1, humidity_day_0, sunlight_day_0)
mae_day_1, mse_day_1 = evaluate_model(results_day_minus_1, humidity_day_1, sunlight_day_1)

# Print the results
print("Evaluation on Day 0 - MAE:", mae_day_0, "MSE:", mse_day_0)
print("Evaluation on Day 1 - MAE:", mae_day_1, "MSE:", mse_day_1)




import matplotlib.pyplot as plt

# Generate predictions for Day 0 and Day 1 using the model fitted on Day -1
predicted_humidity_day_0 = results_day_minus_1.predict(start=0, end=len(humidity_day_0)-1, exog=sunlight_day_0)
predicted_humidity_day_1 = results_day_minus_1.predict(start=0, end=len(humidity_day_1)-1, exog=sunlight_day_1)

# Plot actual vs predicted humidity for Day 0
plt.figure(figsize=(14, 7))
plt.subplot(1, 2, 1)
plt.plot(humidity_day_0.index, humidity_day_0, label='Actual Humidity', color='blue')
plt.plot(humidity_day_0.index, predicted_humidity_day_0, label='Predicted Humidity', color='red', linestyle='--')
plt.title('Day 0: Actual vs Predicted Humidity')
plt.xlabel('Time Steps')
plt.ylabel('Humidity')
plt.legend()

# Plot actual vs predicted humidity for Day 1
plt.subplot(1, 2, 2)
plt.plot(humidity_day_1.index, humidity_day_1, label='Actual Humidity', color='blue')
plt.plot(humidity_day_1.index, predicted_humidity_day_1, label='Predicted Humidity', color='red', linestyle='--')
plt.title('Day 1: Actual vs Predicted Humidity')
plt.xlabel('Time Steps')
plt.ylabel('Humidity')
plt.legend()

plt.tight_layout()
plt.show()
