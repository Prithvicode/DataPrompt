import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import matplotlib.pyplot as plt
import io
import base64

class ForecastService:
    """
    Service for generating forecasts from time series data.
    """
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.original_df = df.copy()
    
    def generate_forecast(
        self, 
        target_column: Optional[str] = None,
        time_column: Optional[str] = None,
        periods: int = 6
    ) -> Dict[str, Any]:
        """
        Generate a forecast for the target column.
        
        Args:
            target_column: Column to forecast
            time_column: Column containing time data
            periods: Number of periods to forecast
            
        Returns:
            Dictionary with forecast results
        """
        # Auto-detect columns if not provided
        if not target_column or not time_column:
            detected_columns = self._detect_time_series_columns()
            if not target_column and detected_columns["target_column"]:
                target_column = detected_columns["target_column"]
            if not time_column and detected_columns["time_column"]:
                time_column = detected_columns["time_column"]
        
        if not target_column or not time_column:
            return {
                "type": "error",
                "message": "Could not identify appropriate target and time columns for forecasting."
            }
        
        try:
            # Prepare the data
            df_copy = self.df.copy()
            
            # Convert time column to datetime if it's not already
            df_copy[time_column] = pd.to_datetime(df_copy[time_column], errors='coerce')
            
            # Drop rows with NaN in time or target columns
            df_copy = df_copy.dropna(subset=[time_column, target_column])
            
            # Sort by time
            df_copy = df_copy.sort_values(by=time_column)
            
            # Set time column as index
            df_copy = df_copy.set_index(time_column)
            
            # Resample to regular frequency
            # Determine appropriate frequency
            time_diff = df_copy.index.to_series().diff().median()
            
            if time_diff.days >= 28:
                freq = 'M'  # Monthly
            elif time_diff.days >= 7:
                freq = 'W'  # Weekly
            else:
                freq = 'D'  # Daily
            
            # Resample
            resampled = df_copy[target_column].resample(freq).mean()
            
            # Fill missing values
            resampled = resampled.interpolate()
            
            # Split data into train and test
            train_size = int(len(resampled) * 0.8)
            train, test = resampled[:train_size], resampled[train_size:]
            
            # Generate forecast
            forecast_data = []
            historical_data = []
            
            # Add historical data
            for date, value in resampled.items():
                historical_data.append({
                    "period": date.strftime('%Y-%m-%d'),
                    "value": float(value),
                    "is_forecast": False
                })
            
            # Try different models and use the best one
            best_model = None
            best_mse = float('inf')
            best_forecast = None
            
            # Try ARIMA
            try:
                model = ARIMA(train, order=(2,1,2))
                model_fit = model.fit()
                
                # Make predictions on test set
                predictions = model_fit.forecast(steps=len(test))
                
                # Calculate MSE
                mse = np.mean((predictions - test) ** 2)
                
                if mse < best_mse:
                    best_mse = mse
                    best_model = "ARIMA"
                    
                    # Generate forecast
                    forecast = model_fit.forecast(steps=periods)
                    best_forecast = forecast
            except:
                pass
            
            # Try Exponential Smoothing
            try:
                model = ExponentialSmoothing(train, trend='add', seasonal='add', seasonal_periods=4)
                model_fit = model.fit()
                
                # Make predictions on test set
                predictions = model_fit.forecast(len(test))
                
                # Calculate MSE
                mse = np.mean((predictions - test) ** 2)
                
                if mse < best_mse:
                    best_mse = mse
                    best_model = "Exponential Smoothing"
                    
                    # Generate forecast
                    forecast = model_fit.forecast(periods)
                    best_forecast = forecast
            except:
                pass
            
            # If no model worked, use a simple moving average
            if best_model is None:
                # Use simple moving average
                window = min(3, len(resampled))
                ma = resampled.rolling(window=window).mean()
                
                # Calculate MSE on test set
                ma_test = ma[train_size:]
                ma_test = ma_test.dropna()
                
                if len(ma_test) > 0 and len(test) > 0:
                    # Align indices
                    common_idx = ma_test.index.intersection(test.index)
                    if len(common_idx) > 0:
                        mse = np.mean((ma_test[common_idx] - test[common_idx]) ** 2)
                        best_mse = mse
                        best_model = "Moving Average"
                
                # Generate forecast
                last_value = resampled.iloc[-1]
                forecast = pd.Series([last_value] * periods)
                
                # Set index for forecast
                last_date = resampled.index[-1]
                if freq == 'M':
                    forecast.index = pd.date_range(start=last_date + pd.DateOffset(months=1), periods=periods, freq=freq)
                elif freq == 'W':
                    forecast.index = pd.date_range(start=last_date + pd.DateOffset(weeks=1), periods=periods, freq=freq)
                else:
                    forecast.index = pd.date_range(start=last_date + pd.DateOffset(days=1), periods=periods, freq=freq)
                
                best_forecast = forecast
            
            # Add forecast data
            if best_forecast is not None:
                for date, value in best_forecast.items():
                    forecast_data.append({
                        "period": date.strftime('%Y-%m-%d'),
                        "value": float(value),
                        "is_forecast": True
                    })
            
            # Calculate metrics
            metrics = {
                "mse": float(best_mse),
                "r2": max(0, 1 - best_mse / np.var(test)) if len(test) > 0 else 0
            }
            
            # Generate plot
            plt.figure(figsize=(10, 6))
            plt.plot(resampled.index, resampled.values, label='Historical')
            if best_forecast is not None:
                plt.plot(best_forecast.index, best_forecast.values, label='Forecast', linestyle='--')
            plt.title(f'Forecast for {target_column}')
            plt.xlabel('Date')
            plt.ylabel(target_column)
            plt.legend()
            plt.grid(True)
            
            # Save plot to base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png')
            buffer.seek(0)
            plot_data = base64.b64encode(buffer.read()).decode('utf-8')
            plt.close()
            
            # Calculate summary
            last_value = resampled.iloc[-1]
            forecast_end = best_forecast.iloc[-1] if best_forecast is not None else last_value
            percent_change = ((forecast_end - last_value) / last_value) * 100
            
            direction = "increase" if percent_change > 0 else "decrease"
            summary = f"{target_column} is forecasted to {direction} by {abs(percent_change):.1f}% over the next {periods} periods."
            
            return {
                "type": "forecast",
                "target_column": target_column,
                "time_column": time_column,
                "model": best_model,
                "periods": periods,
                "metrics": metrics,
                "summary": summary,
                "data": historical_data + forecast_data,
                "plot": plot_data
            }
        except Exception as e:
            return {
                "type": "error",
                "message": f"Error generating forecast: {str(e)}"
            }
    
    def _detect_time_series_columns(self) -> Dict[str, str]:
        """
        Auto-detect appropriate columns for time series analysis.
        
        Returns:
            Dictionary with time_column and target_column
        """
        time_column = None
        target_column = None
        
        # Look for date/time columns
        date_columns = []
        for col in self.df.columns:
            # Check if column name suggests a date
            if any(term in col.lower() for term in ['date', 'time', 'year', 'month', 'day']):
                date_columns.append(col)
                continue
            
            # Try to convert to datetime
            if self.df[col].dtype == 'object':
                try:
                    pd.to_datetime(self.df[col])
                    date_columns.append(col)
                except:
                    pass
        
        # If we found date columns, use the first one
        if date_columns:
            time_column = date_columns[0]
        
        # Look for numeric columns that might be targets
        numeric_columns = self.df.select_dtypes(include=['number']).columns.tolist()
        
        # Prioritize columns with certain keywords
        for col in numeric_columns:
            if any(term in col.lower() for term in ['sales', 'revenue', 'profit', 'price', 'cost', 'amount', 'value']):
                target_column = col
                break
        
        # If no target found, use the first numeric column
        if not target_column and numeric_columns:
            target_column = numeric_columns[0]
        
        return {
            "time_column": time_column,
            "target_column": target_column
        }


# from sklearn.preprocessing import LabelEncoder
# from sklearn.metrics import mean_squared_error, r2_score
# import pickle
# import numpy as np
# import pandas as pd
# import matplotlib.pyplot as plt
# import io
# import base64

# def preprocess_data(df):
#     """Preprocess the input dataframe for prediction"""
#     data = df.copy()
    
#     # Fill missing values
#     for col in data.columns:
#         if data[col].dtype in ['int64', 'float64']:
#             data[col] = data[col].fillna(data[col].mean())
#         else:
#             data[col] = data[col].fillna(data[col].mode()[0])
    
#     # Initialize LabelEncoder
#     encoder = LabelEncoder()
    
#     # Encode categorical columns
#     categorical_columns = data.select_dtypes(include=['object']).columns
#     for col in categorical_columns:
#         data[col] = encoder.fit_transform(data[col])
    
#     return data

# def load_model():
#     """Load the saved linear regression model"""
#     try:
#         with open('services/linear_regression_model (2).pkl', 'rb') as f:
#             model = pickle.load(f)
#         return model
#     except Exception as e:
#         raise Exception(f"Error loading model: {str(e)}")

# def predict(X, theta):
#     """Make predictions using the model coefficients"""
#     return np.dot(X, theta)

# def make_prediction(data):
#     """Make predictions using the loaded model"""
#     try:
#         # Preprocess the data
#         processed_data = preprocess_data(data)
        
#         # Load the model coefficients
#         theta = load_model()
        
#         # Prepare features
#         X = processed_data.values
        
#         # Add bias term (column of ones)
#         X = np.hstack([np.ones((X.shape[0], 1)), X])
        
#         # Make predictions
#         predictions = predict(X, theta)
        
#         # Calculate metrics if target variable is available
#         metrics = {}
#         if 'Item_Outlet_Sales' in data.columns:
#             metrics['mse'] = mean_squared_error(data['Item_Outlet_Sales'], predictions)
#             metrics['r2'] = r2_score(data['Item_Outlet_Sales'], predictions)
#         else:
#             metrics['mse'] = None
#             metrics['r2'] = None
        
#         # Create visualization
#         plt.figure(figsize=(10, 6))
#         if 'Item_Outlet_Sales' in data.columns:
#             plt.scatter(data['Item_Outlet_Sales'], predictions)
#             plt.xlabel('Actual Sales')
#             plt.ylabel('Predicted Sales')
#         else:
#             plt.plot(predictions)
#             plt.xlabel('Data Points')
#             plt.ylabel('Predicted Sales')
#         plt.title('Sales Predictions')
        
#         # Save plot to base64 string
#         buffer = io.BytesIO()
#         plt.savefig(buffer, format='png')
#         buffer.seek(0)
#         plot_base64 = base64.b64encode(buffer.getvalue()).decode()
#         plt.close()
        
#         return {
#             'predictions': predictions.tolist(),
#             'metrics': metrics,
#             'plot': plot_base64
#         }
#     except Exception as e:
#         raise Exception(f"Error making predictions: {str(e)}") 