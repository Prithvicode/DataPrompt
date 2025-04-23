import pandas as pd
import numpy as np
import pickle
import os
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from sklearn.metrics import r2_score
import re

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

# 1) Helper to build your baseline table from any DataFrame
# def build_baseline(df: pd.DataFrame) -> pd.DataFrame:
#     group_keys = ['ProductCategory','ProductName','Region','CustomerSegment']
#     return (
#         df
#         .groupby(group_keys)
#         .agg({
#             'UnitsSold':   'mean',
#             'UnitPrice':   'mean',
#             'CostPerUnit': 'mean',
#         })
#         .round(2)
#         .reset_index()
#     )

# # 2) Load your dataset and compute baseline
# def load_dataset(df: pd.DataFrame):
#     global current_df, baseline
#     current_df = df.copy()
#     baseline   = build_baseline(current_df)

# # 3) Lookup baseline defaults
# def lookup_baseline(user_input: dict):
#     if baseline is None:
#         raise RuntimeError("No baseline available — call load_dataset(df) first!")
#     mask = (
#         (baseline.ProductCategory == user_input.get('ProductCategory')) &
#         (baseline.ProductName     == user_input.get('ProductName'))     &
#         (baseline.Region          == user_input.get('Region'))          &
#         (baseline.CustomerSegment == user_input.get('CustomerSegment'))
#     )
#     row = baseline[mask]
#     if row.empty:
#         raise ValueError("No baseline for this category combo")
#     row = row.iloc[0]
#     return {
#         'UnitsSold':   row.UnitsSold,
#         'UnitPrice':   row.UnitPrice,
#         'CostPerUnit': row.CostPerUnit
#     }

# # 4) Prepare input (fill defaults, recalc derived)
# def prepare_input(user_input: dict):
#     core_defaults = {}
#     for f in ['UnitsSold','UnitPrice','CostPerUnit']:
#         if f not in user_input:
#             core_defaults = lookup_baseline(user_input)
#             break

#     merged = {**core_defaults, **user_input}
#     merged['ProfitPerUnit'] = round(merged['UnitPrice'] - merged['CostPerUnit'], 2)
#     merged['ProfitMargin']  = round(merged['ProfitPerUnit'] / merged['UnitPrice'], 4)
#     merged['Profit']        = round(merged['UnitsSold'] * merged['ProfitPerUnit'], 2)
#     return merged

# # 5a) Apply percent change (what-if)
# def apply_percent_change(base_input: dict, field: str, pct: float):
#     out = base_input.copy()
#     if field in out:
#         out[field] = round(out[field] * (1 + pct/100), 2)
#     return prepare_input(out)

# # 5b) Apply absolute change (fixed value adjust)
# def apply_absolute_change(base_input: dict, field: str, abs_val: float):
#     out = base_input.copy()
#     if field in out:
#         out[field] = round(out[field] + abs_val, 2)
#     return prepare_input(out)

# # 6) Revenue prediction
# def predict_revenue(custom_input: dict):
#     df_enc = pd.get_dummies(pd.DataFrame([custom_input]),
#                              columns=['ProductCategory','ProductName','Region','CustomerSegment'])
#     for col in feature_cols:
#         if col not in df_enc:
#             df_enc[col] = 0
#     X = df_enc[feature_cols].astype(np.float64)
#     X_scaled = scaler.transform(X)
#     X_scaled = np.hstack((np.ones((X_scaled.shape[0],1)), X_scaled))
#     pred = X_scaled @ theta
#     return round(float(pred[0][0]), 2)

# # 7) Full what-if pipeline supporting both percent and fixed changes
# def what_if_predict(user_input: dict,
#                     change_field: str=None,
#                     pct_change: float=0,
#                     abs_change: float=0):
#     # fill in missing fields from baseline
#     base = prepare_input(user_input)

#     # apply fixed absolute change first
#     if change_field and abs_change:
#         base = apply_absolute_change(base, change_field, abs_change)
#     # then apply percent change
#     if change_field and pct_change:
#         base = apply_percent_change(base, change_field, pct_change)

#     return predict_revenue(base)



# # 8) Bulk process & compare
# def process_and_predict(df: pd.DataFrame):
#     new_data = df.copy()
#     new_data_encoded = pd.get_dummies(new_data, columns=['ProductCategory','ProductName','Region','CustomerSegment'], drop_first=True)
#     missing_cols = set(feature_cols) - set(new_data_encoded.columns)
#     for col in missing_cols:
#         new_data_encoded[col] = 0
#     new_data_encoded = new_data_encoded[feature_cols]
#     new_data_encoded = new_data_encoded.fillna(new_data_encoded.mean(numeric_only=True))
#     X_new_scaled = scaler.transform(new_data_encoded)
#     X_new_scaled = np.hstack((np.ones((X_new_scaled.shape[0], 1)), X_new_scaled))
#     predicted = X_new_scaled @ theta
#     new_data['PredictedRevenue'] = predicted
#     if 'Revenue' in new_data:
#         new_data['ActualRevenue'] = new_data['Revenue']
#         new_data['PredictionError'] = new_data['PredictedRevenue'] - new_data['ActualRevenue']
#         new_data['AbsoluteError'] = np.abs(new_data['PredictionError'])
#         mae = new_data['AbsoluteError'].mean()
#         r2  = r2_score(new_data['ActualRevenue'], new_data['PredictedRevenue'])
#     else:
#         mae = None
#         r2  = None
#     return new_data, mae, r2

# 9) Static test harness
# if __name__ == "__main__":
#     # Create a static test DataFrame
#     test_data = pd.DataFrame([
#         {
#             'OrderID': 1,
#             'ProductCategory':'Electronics','ProductName':'Smartphone',
#             'Region':'North','CustomerSegment':'Retail',
#             'UnitsSold': 100,'UnitPrice': 300,'CostPerUnit': 200,
#             'PromotionApplied':1,'Holiday':0,'Temperature':25,'FootTraffic':400,
#             'Revenue': 100 * 300
#         },
#         {
#             'OrderID': 2,
#             'ProductCategory':'Electronics','ProductName':'Laptop',
#             'Region':'South','CustomerSegment':'Wholesale',
#             'UnitsSold': 50,'UnitPrice': 800,'CostPerUnit': 600,
#             'PromotionApplied':0,'Holiday':1,'Temperature':30,'FootTraffic':300,
#             'Revenue': 50 * 800
#         }
#     ])

#     # Load dataset and build baselines
#     load_dataset(test_data)

#     # Examples:
#     row1 = test_data.iloc[0].to_dict()
#     print("Baseline revenue (row1):", what_if_predict(row1))
#     print("After +10% UnitsSold (row1):", what_if_predict(row1, 'UnitsSold', pct_change=10))
#     print("After +20 abs change in UnitPrice (row1):", what_if_predict(row1, 'UnitPrice', abs_change=20))
#     print("After +5 abs & +10% UnitsSold:", what_if_predict(row1, 'UnitsSold', pct_change=10, abs_change=5))

#     # Bulk processing
#     results, mae, r2 = process_and_predict(test_data)
#     print(results)
#     if mae is not None:
#         print(f"MAE: {mae:.2f}, R²: {r2:.4f}")
