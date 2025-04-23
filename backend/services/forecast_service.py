import pandas as pd
import numpy as np
import pickle
import os
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from sklearn.metrics import r2_score
import re

# Import model and set global variables
global model_data, theta, feature_cols, scaler, current_df
MODEL_PATH = os.path.join(os.path.dirname(__file__), "linear_model.pkl")
with open(MODEL_PATH, "rb") as f:
    model_data = pickle.load(f)
    theta        = model_data['theta']
    feature_cols = model_data['feature_cols']
    scaler       = model_data['scaler']
current_df = None

# check
print(theta)
print(feature_cols)
print(scaler)

# PRedict all revenue with actual values
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



def predict_revenue(custom_input: dict):
    df = pd.DataFrame([custom_input])
    encoded = pd.get_dummies(df, columns=['ProductCategory', 'ProductName', 'Region', 'CustomerSegment'])

    # Ensure all expected columns are present
    for col in feature_cols:
        if col not in encoded.columns:
            encoded[col] = 0

    # Reorder columns to match training set
    encoded = encoded[feature_cols]

    # Scale input (avoid warning)
    scaled = scaler.transform(encoded.values.astype(np.float64))

    # Add bias term
    scaled = np.hstack((np.ones((scaled.shape[0], 1)), scaled))

    # Predict
    prediction = scaled @ theta
    return round(float(prediction[0][0]), 2)
  



#Test
print(
predict_revenue({
    'UnitsSold': 120,
    'UnitPrice': 30,
    'CostPerUnit': 20,
    'Profit': 10 * 120,
    'PromotionApplied': 1,
    'Holiday': 0,
    'Temperature': 25,
    'FootTraffic': 400,
    'ProfitPerUnit': 10,
    'ProfitMargin': 10 / 30,
    'ProductCategory': 'Electronics',
    'ProductName': 'Smartphone',
    'Region': 'North',
    'CustomerSegment': 'Retail'
}))




# def forecast_revenue( df, period_type='monthly', periods_ahead=3,):
#     global model_data, theta, feature_cols, scaler
#     """
#     Forecast revenue for future periods
    
#     Parameters:
#     - period_type: 'weekly', 'monthly', or 'yearly'
#     - periods_ahead: number of periods to forecast
#     - df_path: path to the original data file
    
#     Returns:
#     - DataFrame with forecasted values
#     """

#     MODEL_PATH = os.path.join(os.path.dirname(__file__), "linear_model.pkl")
#     with open(MODEL_PATH, "rb") as f:
#         model_data = pickle.load(f)
    
#     theta = model_data['theta']
#     feature_cols = model_data['feature_cols']
#     scaler = model_data['scaler']
    
#     # Load the dataset
#     # df = pd.read_csv(df_path)
    
#     # Group by the specified period to get the most recent data patterns
#     if period_type == 'weekly':
#         time_col = 'Week'
#         groupby_cols = ['Year', 'Week']
#     elif period_type == 'monthly':
#         time_col = 'Month'
#         groupby_cols = ['Year', 'Month']
#     elif period_type == 'yearly':
#         time_col = 'Year'
#         groupby_cols = ['Year']
#     else:
#         raise ValueError("period_type must be 'weekly', 'monthly', or 'yearly'")
    
#     # Get the latest features by averaging the most recent period's data
#     df_encoded = pd.get_dummies(df, columns=['ProductCategory', 'ProductName', 'Region', 'CustomerSegment'], drop_first=True)
    
#     # Drop non-numeric columns
#     for col in df_encoded.columns:
#         if df_encoded[col].dtype == 'object':
#             df_encoded = df_encoded.drop(columns=[col], errors='ignore')
    
#     df_encoded = df_encoded.fillna(df_encoded.mean(numeric_only=True))
    
#     # Get latest period data
#     if period_type == 'yearly':
#         latest_year = df_encoded['Year'].max()
#         latest_data = df_encoded[df_encoded['Year'] == latest_year]
#     elif period_type == 'monthly':
#         latest_year = df_encoded['Year'].max()
#         latest_month = df_encoded[df_encoded['Year'] == latest_year]['Month'].max()
#         latest_data = df_encoded[(df_encoded['Year'] == latest_year) & (df_encoded['Month'] == latest_month)]
#     else:  # weekly
#         latest_year = df_encoded['Year'].max()
#         latest_week = df_encoded[df_encoded['Year'] == latest_year]['Week'].max()
#         latest_data = df_encoded[(df_encoded['Year'] == latest_year) & (df_encoded['Week'] == latest_week)]
    
#     # Calculate the average feature values for the latest period
#     latest_features = latest_data[feature_cols].mean().values.reshape(1, -1)
    
#     # Scale the features
#     X_latest_scaled = scaler.transform(latest_features)
#     X_latest_scaled = np.hstack((np.ones((X_latest_scaled.shape[0], 1)), X_latest_scaled))
    
#     # Create forecasts
#     forecasts = []
#     current_period = {'Year': latest_year}
    
#     if period_type == 'monthly':
#         current_period['Month'] = latest_month
#     elif period_type == 'weekly':
#         current_period['Week'] = latest_week
    
#     for i in range(1, periods_ahead + 1):
#         # Update the period
#         if period_type == 'yearly':
#             current_period['Year'] += 1
#         elif period_type == 'monthly':
#             current_period['Month'] += 1
#             if current_period['Month'] > 12:
#                 current_period['Month'] = 1
#                 current_period['Year'] += 1
#         elif period_type == 'weekly':
#             current_period['Week'] += 1
#             if current_period['Week'] > 52:  # simplified; actual weeks per year may vary
#                 current_period['Week'] = 1
#                 current_period['Year'] += 1
        
#         # Make prediction
#         prediction = X_latest_scaled @ theta
        
#         forecast_data = current_period.copy()
#         forecast_data['Forecasted_Revenue'] = prediction[0][0]
#         forecasts.append(forecast_data)
    
#     # Create DataFrame with forecasts
#     forecast_df = pd.DataFrame(forecasts)
    
#     return forecast_df


# def forecast_revenue(df, period_type='monthly', periods_ahead=3):
#     """
#     Forecast revenue for future periods.
    
#     Parameters:
#     - df:            DataFrame with at least ['OrderDate','Revenue'] + your feature columns
#     - period_type:   'weekly', 'monthly', or 'yearly'
#     - periods_ahead: how many future periods to forecast
    
#     Returns:
#     - DataFrame with columns ['timestamp','Forecasted_Revenue']
#     """
#     # --- 1) load model metadata ---
#     MODEL_PATH = os.path.join(os.path.dirname(__file__), "linear_model.pkl")
#     with open(MODEL_PATH, "rb") as f:
#         model_data = pickle.load(f)
#     theta        = model_data['theta']
#     feature_cols = model_data['feature_cols']
#     scaler       = model_data['scaler']

#     # --- 2) prepare datetime index + encode cats up front ---
#     df = df.copy()
#     df['OrderDate'] = pd.to_datetime(df['OrderDate'])
#     df = df.set_index('OrderDate')

#     # one-hot encode *before* any resampling so no objects remain
#     cat_cols = ['ProductCategory','ProductName','Region','CustomerSegment']
#     df = pd.get_dummies(df, columns=cat_cols, drop_first=True)

#     # map to pandas freq codes
#     freq_map = {'weekly':'W','monthly':'M','yearly':'A'}
#     if period_type not in freq_map:
#         raise ValueError("period_type must be one of 'weekly','monthly','yearly'")
#     freq = freq_map[period_type]

#     # --- 3) resample & aggregate only numeric columns ---
#     # numeric_only=True ensures pandas will skip any remaining object dtypes
#     resampled = (
#         df
#         .resample(freq)
#         .mean(numeric_only=True)
#         .fillna(method='ffill')
#     )

#     # pull out the last row’s features
#     latest = resampled.iloc[-1]
#     X_latest = latest[feature_cols].values.reshape(1, -1)

#     # scale + add intercept
#     Xs = scaler.transform(X_latest)
#     Xs = np.hstack((np.ones((Xs.shape[0],1)), Xs))
#     point_pred = float((Xs @ theta).flatten()[0])

#     # --- 4) generate future timestamps & repeat the same prediction ---
#     last_period = resampled.index[-1].to_period(freq)
#     future_periods = [last_period + i for i in range(1, periods_ahead+1)]

#     forecast_df = pd.DataFrame([
#         {
#             "timestamp": p.to_timestamp(),
#             "Forecasted_Revenue": point_pred
#         }
#         for p in future_periods
#     ])
#     return forecast_df



# def preprocess_new_data(df, feature_cols):
#     """Preprocess new data to match the training data format"""
#     # Handle date column if present
#     if 'OrderDate' in df.columns:
#         try:
#             df['OrderDate'] = pd.to_datetime(df['OrderDate'])
#         except:
#             pass  # Keep as is if conversion fails
    
#     # Encode categoricals - same as training
#     categorical_cols = ['ProductCategory', 'ProductName', 'Region', 'CustomerSegment']
#     existing_cats = [col for col in categorical_cols if col in df.columns]
    
#     if existing_cats:
#         df_encoded = pd.get_dummies(df, columns=existing_cats, drop_first=True)
#     else:
#         df_encoded = df.copy()
    
#     # Drop non-numeric columns
#     for col in df_encoded.columns:
#         if df_encoded[col].dtype == 'object':
#             df_encoded = df_encoded.drop(columns=[col], errors='ignore')
    
#     df_encoded = df_encoded.fillna(df_encoded.mean(numeric_only=True))
    
#     # Create feature set that matches the training data
#     feature_set = pd.DataFrame()
#     for col in feature_cols:
#         if col in df_encoded.columns:
#             feature_set[col] = df_encoded[col]
#         else:
#             feature_set[col] = 0
    
#     X = feature_set.values.astype(np.float64)
    
#     return X, df_encoded

# def predict_revenue(X, theta, scaler):
#     """Make revenue predictions using the trained model"""
#     X_scaled = scaler.transform(X)
#     X_scaled = np.hstack((np.ones((X_scaled.shape[0], 1)), X_scaled))  # Add bias term
#     predictions = X_scaled @ theta
#     return predictions


# def forecast_next_months(df, num_months=3):
#     """Forecast revenue for the next n months"""
#     global theta, feature_cols, scaler
    
#     # Get the most recent date in the dataset
#     if 'OrderDate' in df.columns and pd.api.types.is_datetime64_any_dtype(df['OrderDate']):
#         last_date = df['OrderDate'].max()
#     elif 'OrderDate' in df.columns:
#         try:
#             df['OrderDate'] = pd.to_datetime(df['OrderDate'])
#             last_date = df['OrderDate'].max()
#         except:
#             last_date = datetime.now()
#     else:
#         # If no date column, use current date
#         last_date = datetime.now()
    
#     # Create forecast dataframe by replicating the most recent month's data
#     latest_data = df.iloc[-1:].copy()
#     forecast_frames = []
    
#     for i in range(1, num_months + 1):
#         next_period = latest_data.copy()
#         next_date = last_date + relativedelta(months=i)
        
#         # Update date information
#         if 'OrderDate' in next_period.columns:
#             next_period['OrderDate'] = next_date
#         if 'Month' in next_period.columns:
#             next_period['Month'] = next_date.month
#         if 'Year' in next_period.columns:
#             next_period['Year'] = next_date.year
#         if 'Week' in next_period.columns:
#             next_period['Week'] = next_date.isocalendar()[1]
        
#         forecast_frames.append(next_period)
    
#     forecast_df = pd.concat(forecast_frames, ignore_index=True)
    
#     # Preprocess and predict
#     X, processed_df = preprocess_new_data(forecast_df, feature_cols)
#     predictions = predict_revenue(X, theta, scaler)
    
#     # Add predictions to the forecast dataframe
#     forecast_df['Predicted_Revenue'] = predictions
    
#     return forecast_df


# def what_if_scenario(df, scenario_params):
#     """
#     Run what-if scenarios based on parameter changes
    
#     Args:
#         df: Input dataframe
#         scenario_params: Dictionary of parameters to change and their percentage changes
#                         e.g., {'UnitsSold': 1.10} for 10% increase in UnitsSold
    
#     Returns:
#         DataFrame with predictions based on the scenario
#     """
#     global theta, feature_cols, scaler
    
#     # Create a copy for the scenario
#     scenario_df = df.copy()
    
#     # Apply changes based on scenario parameters
#     for param, change_factor in scenario_params.items():
#         if param in scenario_df.columns:
#             scenario_df[param] = scenario_df[param] * change_factor
    
#     # Preprocess and predict
#     X, processed_df = preprocess_new_data(scenario_df, feature_cols)
#     predictions = predict_revenue(X, theta, scaler)
    
#     # Add predictions to the scenario dataframe
#     scenario_df['Predicted_Revenue'] = predictions
    
#     return scenario_df



# # For monthly forecasts (next 6 months)
# monthly_forecast = forecast_revenue(period_type='monthly', periods_ahead=6)
# print("Monthly Revenue Forecast:")
# print(monthly_forecast)

# # For weekly forecasts (next 8 weeks)
# weekly_forecast = forecast_revenue(period_type='weekly', periods_ahead=8)
# print("\nWeekly Revenue Forecast:")
# print(weekly_forecast)

# # For yearly forecasts (next 3 years)
# yearly_forecast = forecast_revenue(period_type='yearly', periods_ahead=3)
# print("\nYearly Revenue Forecast:")
# print(yearly_forecast)