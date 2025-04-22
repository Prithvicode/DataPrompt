import pandas as pd
import numpy as np
import pickle
import os
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import re

# FILE_PATH = os.path.join(os.path.dirname(__file__), "cleaned_dataset.csv")
global model_data, theta, feature_cols, scaler, current_df
model_data = None
theta = None
feature_cols = None
scaler = None
current_df = None

def forecast_revenue( df, period_type='monthly', periods_ahead=3,):
    global model_data, theta, feature_cols, scaler
    """
    Forecast revenue for future periods
    
    Parameters:
    - period_type: 'weekly', 'monthly', or 'yearly'
    - periods_ahead: number of periods to forecast
    - df_path: path to the original data file
    
    Returns:
    - DataFrame with forecasted values
    """

    MODEL_PATH = os.path.join(os.path.dirname(__file__), "linear_model.pkl")
    with open(MODEL_PATH, "rb") as f:
        model_data = pickle.load(f)
    
    theta = model_data['theta']
    feature_cols = model_data['feature_cols']
    scaler = model_data['scaler']
    
    # Load the dataset
    # df = pd.read_csv(df_path)
    
    # Group by the specified period to get the most recent data patterns
    if period_type == 'weekly':
        time_col = 'Week'
        groupby_cols = ['Year', 'Week']
    elif period_type == 'monthly':
        time_col = 'Month'
        groupby_cols = ['Year', 'Month']
    elif period_type == 'yearly':
        time_col = 'Year'
        groupby_cols = ['Year']
    else:
        raise ValueError("period_type must be 'weekly', 'monthly', or 'yearly'")
    
    # Get the latest features by averaging the most recent period's data
    df_encoded = pd.get_dummies(df, columns=['ProductCategory', 'ProductName', 'Region', 'CustomerSegment'], drop_first=True)
    
    # Drop non-numeric columns
    for col in df_encoded.columns:
        if df_encoded[col].dtype == 'object':
            df_encoded = df_encoded.drop(columns=[col], errors='ignore')
    
    df_encoded = df_encoded.fillna(df_encoded.mean(numeric_only=True))
    
    # Get latest period data
    if period_type == 'yearly':
        latest_year = df_encoded['Year'].max()
        latest_data = df_encoded[df_encoded['Year'] == latest_year]
    elif period_type == 'monthly':
        latest_year = df_encoded['Year'].max()
        latest_month = df_encoded[df_encoded['Year'] == latest_year]['Month'].max()
        latest_data = df_encoded[(df_encoded['Year'] == latest_year) & (df_encoded['Month'] == latest_month)]
    else:  # weekly
        latest_year = df_encoded['Year'].max()
        latest_week = df_encoded[df_encoded['Year'] == latest_year]['Week'].max()
        latest_data = df_encoded[(df_encoded['Year'] == latest_year) & (df_encoded['Week'] == latest_week)]
    
    # Calculate the average feature values for the latest period
    latest_features = latest_data[feature_cols].mean().values.reshape(1, -1)
    
    # Scale the features
    X_latest_scaled = scaler.transform(latest_features)
    X_latest_scaled = np.hstack((np.ones((X_latest_scaled.shape[0], 1)), X_latest_scaled))
    
    # Create forecasts
    forecasts = []
    current_period = {'Year': latest_year}
    
    if period_type == 'monthly':
        current_period['Month'] = latest_month
    elif period_type == 'weekly':
        current_period['Week'] = latest_week
    
    for i in range(1, periods_ahead + 1):
        # Update the period
        if period_type == 'yearly':
            current_period['Year'] += 1
        elif period_type == 'monthly':
            current_period['Month'] += 1
            if current_period['Month'] > 12:
                current_period['Month'] = 1
                current_period['Year'] += 1
        elif period_type == 'weekly':
            current_period['Week'] += 1
            if current_period['Week'] > 52:  # simplified; actual weeks per year may vary
                current_period['Week'] = 1
                current_period['Year'] += 1
        
        # Make prediction
        prediction = X_latest_scaled @ theta
        
        forecast_data = current_period.copy()
        forecast_data['Forecasted_Revenue'] = prediction[0][0]
        forecasts.append(forecast_data)
    
    # Create DataFrame with forecasts
    forecast_df = pd.DataFrame(forecasts)
    
    return forecast_df




def preprocess_new_data(df, feature_cols):
    """Preprocess new data to match the training data format"""
    # Handle date column if present
    if 'OrderDate' in df.columns:
        try:
            df['OrderDate'] = pd.to_datetime(df['OrderDate'])
        except:
            pass  # Keep as is if conversion fails
    
    # Encode categoricals - same as training
    categorical_cols = ['ProductCategory', 'ProductName', 'Region', 'CustomerSegment']
    existing_cats = [col for col in categorical_cols if col in df.columns]
    
    if existing_cats:
        df_encoded = pd.get_dummies(df, columns=existing_cats, drop_first=True)
    else:
        df_encoded = df.copy()
    
    # Drop non-numeric columns
    for col in df_encoded.columns:
        if df_encoded[col].dtype == 'object':
            df_encoded = df_encoded.drop(columns=[col], errors='ignore')
    
    df_encoded = df_encoded.fillna(df_encoded.mean(numeric_only=True))
    
    # Create feature set that matches the training data
    feature_set = pd.DataFrame()
    for col in feature_cols:
        if col in df_encoded.columns:
            feature_set[col] = df_encoded[col]
        else:
            feature_set[col] = 0
    
    X = feature_set.values.astype(np.float64)
    
    return X, df_encoded

def predict_revenue(X, theta, scaler):
    """Make revenue predictions using the trained model"""
    X_scaled = scaler.transform(X)
    X_scaled = np.hstack((np.ones((X_scaled.shape[0], 1)), X_scaled))  # Add bias term
    predictions = X_scaled @ theta
    return predictions


def forecast_next_months(df, num_months=3):
    """Forecast revenue for the next n months"""
    global theta, feature_cols, scaler
    
    # Get the most recent date in the dataset
    if 'OrderDate' in df.columns and pd.api.types.is_datetime64_any_dtype(df['OrderDate']):
        last_date = df['OrderDate'].max()
    elif 'OrderDate' in df.columns:
        try:
            df['OrderDate'] = pd.to_datetime(df['OrderDate'])
            last_date = df['OrderDate'].max()
        except:
            last_date = datetime.now()
    else:
        # If no date column, use current date
        last_date = datetime.now()
    
    # Create forecast dataframe by replicating the most recent month's data
    latest_data = df.iloc[-1:].copy()
    forecast_frames = []
    
    for i in range(1, num_months + 1):
        next_period = latest_data.copy()
        next_date = last_date + relativedelta(months=i)
        
        # Update date information
        if 'OrderDate' in next_period.columns:
            next_period['OrderDate'] = next_date
        if 'Month' in next_period.columns:
            next_period['Month'] = next_date.month
        if 'Year' in next_period.columns:
            next_period['Year'] = next_date.year
        if 'Week' in next_period.columns:
            next_period['Week'] = next_date.isocalendar()[1]
        
        forecast_frames.append(next_period)
    
    forecast_df = pd.concat(forecast_frames, ignore_index=True)
    
    # Preprocess and predict
    X, processed_df = preprocess_new_data(forecast_df, feature_cols)
    predictions = predict_revenue(X, theta, scaler)
    
    # Add predictions to the forecast dataframe
    forecast_df['Predicted_Revenue'] = predictions
    
    return forecast_df


def what_if_scenario(df, scenario_params):
    """
    Run what-if scenarios based on parameter changes
    
    Args:
        df: Input dataframe
        scenario_params: Dictionary of parameters to change and their percentage changes
                        e.g., {'UnitsSold': 1.10} for 10% increase in UnitsSold
    
    Returns:
        DataFrame with predictions based on the scenario
    """
    global theta, feature_cols, scaler
    
    # Create a copy for the scenario
    scenario_df = df.copy()
    
    # Apply changes based on scenario parameters
    for param, change_factor in scenario_params.items():
        if param in scenario_df.columns:
            scenario_df[param] = scenario_df[param] * change_factor
    
    # Preprocess and predict
    X, processed_df = preprocess_new_data(scenario_df, feature_cols)
    predictions = predict_revenue(X, theta, scaler)
    
    # Add predictions to the scenario dataframe
    scenario_df['Predicted_Revenue'] = predictions
    
    return scenario_df

def process_user_query(df, query):
    """
    Process user query based on the DataFrame
    
    Args:
        df: DataFrame with sales data
        query: User query as a string
    
    Returns:
        Result dataframe, query type, and message
    """
    global theta, feature_cols, scaler

    print("[DEBUG] Processing user query:", query, flush=True)
    
    message = ""
    query_type = "general"
    
    # Determine query type and execute
    if "next" in query.lower() and "month" in query.lower():
        # Extract number of months (default to 3)
        num_months = 3
        for i in range(1, 13):
            if str(i) in query:
                num_months = i
                break
        
        message = f"Forecasting next {num_months} months revenue"
        query_type = "forecast"
        result_df = forecast_next_months(df, num_months)
        
    elif ("if" in query.lower() or "what if" in query.lower()) and ("increase" in query.lower() or "decrease" in query.lower()):
        # Extract parameter and percentage
        scenario_params = {}
        print(f"[DEBUG] Scenario params: {scenario_params}")
        # Check common parameters
        params = ["unitssold", "unitprice", "costperunit", "foottraffic"]
        for param in params:
            if param.lower() in query.lower():
                # Try to extract percentage
                percentage_matches = re.findall(r'(\d+)(?:\s*%)?\s*(?:increase|decrease)', query.lower())
                percentage = float(percentage_matches[0]) if percentage_matches else 10
                
                # Determine if increase or decrease
                change_factor = 1 + (percentage / 100) if "increase" in query.lower() else 1 - (percentage / 100)
                
                # Find the actual column name with proper case
                actual_param = next((col for col in df.columns if col.lower() == param.lower()), None)
                if actual_param:
                    scenario_params[actual_param] = change_factor
                    message = f"Running scenario: {actual_param} {'increased' if change_factor > 1 else 'decreased'} by {abs((change_factor-1)*100):.0f}%"
        
        query_type = "what-if"
        result_df = what_if_scenario(df, scenario_params)
        
    else:
        # Default to basic prediction
        message = "Making revenue predictions on the data"
        query_type = "predict"
        X, processed_df = preprocess_new_data(df, feature_cols)
        predictions = predict_revenue(X, theta, scaler)
        
        result_df = df.copy()
        result_df['Predicted_Revenue'] = predictions
    print("[DEBUG] Result DataFrame:", result_df.head(), flush=True)
    return result_df, query_type, message



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