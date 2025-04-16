from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_squared_error, r2_score
import pickle
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64

def preprocess_data(df):
    """Preprocess the input dataframe for prediction"""
    data = df.copy()
    
    # Fill missing values
    for col in data.columns:
        if data[col].dtype in ['int64', 'float64']:
            data[col] = data[col].fillna(data[col].mean())
        else:
            data[col] = data[col].fillna(data[col].mode()[0])
    
    # Initialize LabelEncoder
    encoder = LabelEncoder()
    
    # Encode categorical columns
    categorical_columns = data.select_dtypes(include=['object']).columns
    for col in categorical_columns:
        data[col] = encoder.fit_transform(data[col])
    
    return data

def load_model():
    """Load the saved linear regression model"""
    try:
        with open('services/linear_regression_model (2).pkl', 'rb') as f:
            model = pickle.load(f)
        return model
    except Exception as e:
        raise Exception(f"Error loading model: {str(e)}")

def predict(X, theta):
    """Make predictions using the model coefficients"""
    return np.dot(X, theta)

def make_prediction(data):
    """Make predictions using the loaded model"""
    try:
        # Preprocess the data
        processed_data = preprocess_data(data)
        
        # Load the model coefficients
        theta = load_model()
        
        # Prepare features
        X = processed_data.values
        
        # Add bias term (column of ones)
        X = np.hstack([np.ones((X.shape[0], 1)), X])
        
        # Make predictions
        predictions = predict(X, theta)
        
        # Calculate metrics if target variable is available
        metrics = {}
        if 'Item_Outlet_Sales' in data.columns:
            metrics['mse'] = mean_squared_error(data['Item_Outlet_Sales'], predictions)
            metrics['r2'] = r2_score(data['Item_Outlet_Sales'], predictions)
        else:
            metrics['mse'] = None
            metrics['r2'] = None
        
        # Create visualization
        plt.figure(figsize=(10, 6))
        if 'Item_Outlet_Sales' in data.columns:
            plt.scatter(data['Item_Outlet_Sales'], predictions)
            plt.xlabel('Actual Sales')
            plt.ylabel('Predicted Sales')
        else:
            plt.plot(predictions)
            plt.xlabel('Data Points')
            plt.ylabel('Predicted Sales')
        plt.title('Sales Predictions')
        
        # Save plot to base64 string
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        plot_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return {
            'predictions': predictions.tolist(),
            'metrics': metrics,
            'plot': plot_base64
        }
    except Exception as e:
        raise Exception(f"Error making predictions: {str(e)}") 