import pandas as pd
import numpy as np
import pickle
import os
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from sklearn.metrics import r2_score
from sklearn.linear_model import LinearRegression
import re
import json
import ast

# Import model and set global variables
MODEL_PATH = os.path.join(os.path.dirname(__file__), "linear_model.pkl")
with open(MODEL_PATH, "rb") as f:
    model_data    = pickle.load(f)
    theta         = model_data['theta']
    feature_cols  = model_data['feature_cols']
    scaler        = model_data['scaler']

current_df = None
baseline   = None

def process_and_predict(df):
    print("[Debug] Processing and predicting...")
    new_data = df.copy()

    # Step 1: Encode categorical variables
    new_data_encoded = pd.get_dummies(new_data, columns=['ProductCategory', 'ProductName', 'Region', 'CustomerSegment'], drop_first=True)

    # Step 2: Add missing columns and reorder
    missing_cols = set(feature_cols) - set(new_data_encoded.columns)
    for col in missing_cols:
        new_data_encoded[col] = 0
    new_data_encoded = new_data_encoded[feature_cols]

    # Step 3: Fill missing values
    new_data_encoded = new_data_encoded.fillna(new_data_encoded.mean(numeric_only=True))

    # Step 4: Scale data
    X_new_scaled = scaler.transform(new_data_encoded)

    # Step 5: Add bias term
    X_new_scaled = np.hstack((np.ones((X_new_scaled.shape[0], 1)), X_new_scaled))

    # Step 6: Predict revenue
    predicted_revenue = X_new_scaled @ theta

    # Step 7: Combine predictions with original data
    new_data_with_predictions = new_data.copy()
    new_data_with_predictions['PredictedRevenue'] = predicted_revenue

    mae = None
    r2 = None
    visualization = None

    # Step 8: Compare with actual revenue if available
    if 'Revenue' in new_data.columns:
        new_data_with_predictions['ActualRevenue'] = new_data['Revenue']
        new_data_with_predictions['PredictionError'] = new_data_with_predictions['PredictedRevenue'] - new_data_with_predictions['ActualRevenue']
        new_data_with_predictions['AbsoluteError'] = np.abs(new_data_with_predictions['PredictionError'])

        # Metrics
        mae = new_data_with_predictions['AbsoluteError'].mean()
        r2 = r2_score(new_data_with_predictions['ActualRevenue'], new_data_with_predictions['PredictedRevenue'])

        print(new_data_with_predictions[['ActualRevenue', 'PredictedRevenue', 'PredictionError', 'AbsoluteError']].head())
        print(f"\n📊 Mean Absolute Error on new data: {mae:.2f}")
        print(f"📈 R² Score on new data: {r2:.4f}")

        # Step 9: Build visualization data
        if 'OrderID' not in new_data_with_predictions.columns:
            new_data_with_predictions['OrderID'] = new_data_with_predictions.index.astype(str)

        visualization = {
            "type": "line",  # or "bar"
            "data": [
                {
                    "OrderID": row["OrderID"],
                    "ActualRevenue": row["ActualRevenue"],
                    "PredictedRevenue": row["PredictedRevenue"]
                }
                for _, row in new_data_with_predictions.iterrows()
            ],
            "x": "OrderID", 
            "y": ["ActualRevenue", "PredictedRevenue"],
            "title": "Predicted vs Actual Revenue",
            "xLabel": "Order ID",
            "yLabel": "Revenue"
        }
    else:
        print("⚠️ The new data does not contain the 'Revenue' column for comparison.")

    return new_data_with_predictions, mae, r2, visualization


def process_whatif(custom_input):
    if isinstance(custom_input, str):
        custom_input = ast.literal_eval(custom_input)  # Safely parse string to dict

    df = pd.DataFrame([custom_input])
    print(f"[DEBUG] Custom input DataFrame in process_whatif:\n{df}")

    sample_encoded = pd.get_dummies(df, columns=['ProductCategory', 'ProductName', 'Region', 'CustomerSegment'])

    for col in feature_cols:
        if col not in sample_encoded.columns:
            sample_encoded[col] = 0

    sample_encoded = sample_encoded[feature_cols]

    sample_scaled = scaler.transform(sample_encoded)
    sample_scaled = np.hstack((np.ones((sample_scaled.shape[0], 1)), sample_scaled))

    predicted_revenue = sample_scaled @ theta
    print(f"💰 Predicted Revenue: {predicted_revenue[0][0]:.2f}")

    return predicted_revenue[0][0]

def process_forecast(df, forecast_periods=3):
    print("[DEBUG] Processing forecast...")
    print(f"[DEBUG] Initial DataFrame:\n{df}")
    print(f"[DEBUG] Forecast periods: {forecast_periods}")

    forecast_periods = max(1, forecast_periods)
    df['Date'] = pd.to_datetime(df[['Year', 'Month']].assign(DAY=1))

    # Sort chronologically
    df.sort_values('Date', inplace=True)
    df.reset_index(drop=True, inplace=True)

    # Create a time index
    df['TimeIndex'] = np.arange(len(df))

    # Define features and target
    X = df[['TimeIndex']]
    y = df['Revenue']

    model = LinearRegression()
    model.fit(X, y)

    # Forecast future time steps
    last_index = df['TimeIndex'].iloc[-1]
    future_index = np.arange(last_index + 1, last_index + forecast_periods + 1).reshape(-1, 1)

    # Predict future values
    future_revenues = model.predict(future_index)

    # Generate future dates
    last_date = df['Date'].iloc[-1]
    # Fix: start forecast from the next month after the last date in the dataset
    future_dates = pd.date_range(last_date + pd.DateOffset(months=1), periods=forecast_periods, freq='MS')

    # Historical result: return actuals with prediction column
    historical_df = df[['Date', 'Revenue']].copy()
    historical_df.rename(columns={'Revenue': 'PredictedRevenue'}, inplace=True)
    historical_df['type'] = 'historical'

    # Forecast result
    forecast_df = pd.DataFrame({
        'Date': future_dates,
        'PredictedRevenue': future_revenues,
        'type': 'forecast'
    })

    combined_df = pd.concat([historical_df, forecast_df], ignore_index=True)

    print(f"[DEBUG] Combined DataFrame:\n{combined_df}")

    return combined_df.to_dict(orient="records")




if __name__ == "__main__":
    user_prompt = """
    {
    'UnitsSold': 10,
    'UnitPrice': 425.48,
    'CostPerUnit': 219.56,
    'Profit': 2059.2,
    'PromotionApplied': 0,  
    'Holiday': 0, 
    'Temperature': 18.2, 
    'FootTraffic': 100,  
    'ProfitPerUnit': 205.92,  
    'ProfitMargin': (2059.2 / 4254.8), 
    'ProductCategory': 'Grocery',  
    'ProductName': 'Cereal',  
    'Region': 'East',  
    'CustomerSegment': 'Online' 
    }
    """
    # parsed_input = json.loads(user_prompt)
    # predicted = process_whatif(parsed_input)
    # print(predicted)
        # Sample historical data for testing
    data = {
        'Year': [2023, 2023, 2023, 2023, 2024],
        'Month': [10, 11, 12, 1, 2],
        'Revenue': [10000, 12000, 13000, 12500, 13500]
    }
    df = pd.DataFrame(data)

    historical_data, forecasted_data = process_forecast(df, forecast_periods=3)
    combined_data = historical_data + forecasted_data
    print(f"[DEBUG] Forecast DataFrame:\n{combined_data} ")
 

