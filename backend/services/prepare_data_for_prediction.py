# import pandas as pd
# import numpy as np
# import pickle
# from datetime import datetime, timedelta
# import matplotlib.pyplot as plt
# import seaborn as sns


# import os

# MODEL_PATH = os.path.join(os.path.dirname(__file__), "linear_model.pkl")
# with open(MODEL_PATH, "rb") as f:
#     model_data = pickle.load(f)

# theta = model_data["theta"]
# feature_cols = model_data["feature_cols"]
# X_mean = model_data["mean_std"]["X_mean"]
# X_std = model_data["mean_std"]["X_std"]

# # Function to prepare new data for prediction
# def prepare_data_for_prediction(new_data):
#     """
#     Prepare new data in the same format as was used for training.

#     Args:
#         new_data (pd.DataFrame): DataFrame with the required columns

#     Returns:
#         np.ndarray: Prepared input for the model
#     """
#     # Create dummy variables for categorical columns
#     # Note: This creates the same categorical columns that were used during training
#     categorical_cols = ['ProductCategory', 'ProductName', 'Region', 'CustomerSegment']

#     # Only process columns that exist in new_data
#     cols_to_encode = [col for col in categorical_cols if col in new_data.columns]
#     if cols_to_encode:
#         encoded_df = pd.get_dummies(new_data, columns=cols_to_encode, drop_first=True)
#     else:
#         encoded_df = new_data.copy()

#     # Ensure all features used during training exist in the encoded DataFrame
#     for col in feature_cols:
#         if col not in encoded_df.columns:
#             encoded_df[col] = 0

#     # Select only the features used during training
#     X_new = encoded_df[feature_cols].values.astype(np.float64)

#     # Check if X_mean includes bias term
#     if len(X_mean) == len(feature_cols) + 1:
#         # X_mean includes bias term, so we use only the feature means/stds (excluding bias)
#         X_new_normalized = (X_new - X_mean[1:]) / X_std[1:]
#     else:
#         # X_mean matches X_new exactly
#         X_new_normalized = (X_new - X_mean) / X_std

#     # Add bias column
#     X_new_normalized = np.hstack([np.ones((X_new_normalized.shape[0], 1)), X_new_normalized])

#     return X_new_normalized

# # Function to predict sales
# def predict_sales(new_data):
#     """
#     Make sales predictions using the trained model.

#     Args:
#         new_data (pd.DataFrame): DataFrame with input features

#     Returns:
#         np.ndarray: Predicted revenue values
#     """
#     # Prepare data
#     X_new_normalized = prepare_data_for_prediction(new_data)

#     # Ensure theta is a column vector
#     theta_reshaped = theta.reshape(-1, 1) if len(theta.shape) == 1 else theta

#     # Make prediction
#     predictions = X_new_normalized @ theta_reshaped

#     return predictions.flatten()

# # Function to generate future dates
# def generate_future_dates(start_date, periods, freq='W'):
#     """
#     Generate a DataFrame with future dates.

#     Args:
#         start_date (str): Start date in format 'YYYY-MM-DD'
#         periods (int): Number of periods to generate
#         freq (str): Frequency ('W' for weekly, 'M' for monthly)

#     Returns:
#         pd.DataFrame: DataFrame with date columns
#     """
#     date_range = pd.date_range(start=start_date, periods=periods, freq=freq)

#     # Create DataFrame with date components
#     date_df = pd.DataFrame({
#         'OrderDate': date_range,
#         'Week': date_range.isocalendar().week,
#         'Month': date_range.month,
#         'Year': date_range.year
#     })

#     return date_df

# # Function to generate weekly forecast
# def forecast_weekly_sales(start_date, weeks, product_categories, product_names, regions, segments):
#     """
#     Generate weekly sales forecast.

#     Args:
#         start_date (str): Start date in format 'YYYY-MM-DD'
#         weeks (int): Number of weeks to forecast
#         product_categories (list): List of product categories
#         product_names (list): List of product names
#         regions (list): List of regions
#         segments (list): List of customer segments

#     Returns:
#         pd.DataFrame: Forecast results
#     """
#     # Generate future dates
#     future_dates = generate_future_dates(start_date, weeks, freq='W')

#     # Create combinations of all features
#     forecast_data = []

#     for _, date_row in future_dates.iterrows():
#         for cat in product_categories:
#             for prod in product_names:
#                 for reg in regions:
#                     for seg in segments:
#                         # Create a row with reasonable default values
#                         forecast_row = {
#                             'OrderDate': date_row['OrderDate'],
#                             'Week': date_row['Week'],
#                             'Month': date_row['Month'],
#                             'Year': date_row['Year'],
#                             'ProductCategory': cat,
#                             'ProductName': prod,
#                             'Region': reg,
#                             'CustomerSegment': seg,
#                             'UnitPrice': 100,  # Default values - adjust as needed
#                             'CostPerUnit': 50,
#                             'PromotionApplied': 0,
#                             'Temperature': 25,
#                             'FootTraffic': 500,
#                             # No need to include UnitsSold or Revenue as these will be predicted
#                         }
#                         forecast_data.append(forecast_row)

#     # Convert to DataFrame
#     forecast_df = pd.DataFrame(forecast_data)

#     # Make predictions
#     forecast_df['PredictedRevenue'] = predict_sales(forecast_df)

#     # Calculate additional metrics based on predictions
#     forecast_df['PredictedUnitsSold'] = forecast_df['PredictedRevenue'] / forecast_df['UnitPrice']
#     forecast_df['PredictedProfit'] = forecast_df['PredictedUnitsSold'] * (forecast_df['UnitPrice'] - forecast_df['CostPerUnit'])

#     return forecast_df

# # Function to generate monthly forecast
# def forecast_monthly_sales(start_date, months, product_categories, product_names, regions, segments):
#     """
#     Generate monthly sales forecast by aggregating weekly forecasts.

#     Args:
#         start_date (str): Start date in format 'YYYY-MM-DD'
#         months (int): Number of months to forecast
#         product_categories (list): List of product categories
#         product_names (list): List of product names
#         regions (list): List of regions
#         segments (list): List of customer segments

#     Returns:
#         pd.DataFrame: Monthly forecast results
#     """
#     # Generate weekly forecast for the period
#     # (we'll use 4 weeks per month as an approximation)
#     weeks = months * 4
#     weekly_forecast = forecast_weekly_sales(
#         start_date, weeks, product_categories, product_names, regions, segments
#     )

#     # Group by month and other dimensions to get monthly totals
#     monthly_forecast = weekly_forecast.groupby(
#         ['Year', 'Month', 'ProductCategory', 'ProductName', 'Region', 'CustomerSegment']
#     ).agg({
#         'PredictedRevenue': 'sum',
#         'PredictedUnitsSold': 'sum',
#         'PredictedProfit': 'sum'
#     }).reset_index()

#     return monthly_forecast

# # Function to visualize forecast
# def plot_forecast(forecast_df, time_period='week'):
#     """
#     Plot forecast results.

#     Args:
#         forecast_df (pd.DataFrame): Forecast DataFrame
#         time_period (str): 'week' or 'month'
#     """
#     plt.figure(figsize=(14, 8))

#     # Aggregate by time period
#     if time_period == 'week':
#         time_group = forecast_df.groupby(['Year', 'Week'])
#         time_label = 'Week'
#     else:
#         time_group = forecast_df.groupby(['Year', 'Month'])
#         time_label = 'Month'

#     # Calculate aggregates
#     agg_data = time_group.agg({
#         'PredictedRevenue': 'sum',
#         'PredictedProfit': 'sum'
#     }).reset_index()

#     # Create time period label
#     if time_period == 'week':
#         agg_data['Period'] = agg_data['Year'].astype(str) + '-W' + agg_data['Week'].astype(str)
#     else:
#         agg_data['Period'] = agg_data['Year'].astype(str) + '-' + agg_data['Month'].astype(str)

#     # Plot revenue and profit
#     plt.subplot(2, 1, 1)
#     plt.bar(agg_data['Period'], agg_data['PredictedRevenue'], color='blue')
#     plt.title(f'Predicted Revenue by {time_label}')
#     plt.xticks(rotation=45)
#     plt.ylabel('Revenue')

#     plt.subplot(2, 1, 2)
#     plt.bar(agg_data['Period'], agg_data['PredictedProfit'], color='green')
#     plt.title(f'Predicted Profit by {time_label}')
#     plt.xticks(rotation=45)
#     plt.ylabel('Profit')

#     plt.tight_layout()
#     plt.show()

#     return agg_data

# # Example usage:
# # 1. Define your product categories, names, regions, and segments
# # product_categories = ['Electronics', 'Furniture', 'Clothing']
# # product_names = ['TV', 'Chair', 'Shirt']
# # regions = ['North', 'South', 'West']
# # segments = ['Retail', 'Wholesale']

# # 2. Generate weekly forecast
# # weekly_forecast = forecast_weekly_sales(
# #     start_date='2025-04-21',  # Today's date
# #     weeks=8,  # Forecast for 8 weeks
# #     product_categories=product_categories,
# #     product_names=product_names,
# #     regions=regions,
# #     segments=segments
# # )

# # 3. Generate monthly forecast
# # monthly_forecast = forecast_monthly_sales(
# #     start_date='2025-04-21',  # Today's date
# #     months=3,  # Forecast for 3 months
# #     product_categories=product_categories,
# #     product_names=product_names,
# #     regions=regions,
# #     segments=segments
# # )

# # 4. Visualize weekly forecast
# # weekly_summary = plot_forecast(weekly_forecast, time_period='week')
# # print("Weekly Forecast Summary:")
# # print(weekly_summary)

# # # 5. Visualize monthly forecast
# # monthly_summary = plot_forecast(monthly_forecast, time_period='month')
# # print("Monthly Forecast Summary:")
# # print(monthly_summary)

# # # 6. Check detailed forecast by product category and region
# # product_region_forecast = monthly_forecast.groupby(['ProductCategory', 'Region']).agg({
# #     'PredictedRevenue': 'sum',
# #     'PredictedProfit': 'sum'
# # }).reset_index()

# # print("\nDetailed Monthly Forecast by Product Category and Region:")
# # print(product_region_forecast)