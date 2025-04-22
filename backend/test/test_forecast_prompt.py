import pandas as pd
import numpy as np
import pickle
from sklearn.preprocessing import StandardScaler

# Assuming you have a trained model stored as 'linear_model.pkl'
def predict_from_model(new_data_df, df_columns, model_file="linear_model.pkl"):
    """
    This function predicts data based on the user's prompt and forecast parameters.
    It takes the user input as DataFrame and columns, loads the pre-trained model, 
    and returns the forecast for the requested parameters.
    """

    # Load the pre-trained model (theta, feature_cols, scaler)
    with open(model_file, "rb") as f:
        model = pickle.load(f)

    theta = model['theta']
    feature_cols = model['feature_cols']
    scaler = model['scaler']

    # Ensure the input has all expected columns (even if zeros)
    for col in feature_cols:
        if col not in new_data_df.columns:
            new_data_df[col] = 0

    # Keep only required features and ensure correct order
    X = new_data_df[feature_cols].values.astype(np.float64)

    # Scale using saved scaler
    X_scaled = scaler.transform(X)

    # Add bias term
    X_scaled = np.hstack((np.ones((X_scaled.shape[0], 1)), X_scaled))

    # Predict
    predictions = X_scaled @ theta

    return predictions


def forecast_from_prompt(df, prompt, model_file="linear_model.pkl"):
    """
    Function to forecast data based on a user prompt.
    This will extract necessary details from the user's prompt (using predefined structure)
    and predict the requested forecast.

    Example prompt: "forecast revenue and profit for next 3 months"
    """
    # Define a helper function to extract parameters from the prompt (time range, target variables, filters)
    def extract_forecast_parameters(prompt, df_columns):
        base_prompt = f"""
        You are a Python assistant who helps generate forecasts based on user prompts.

        The user has provided a dataset with the following columns: {df_columns}.
        The user will ask for a forecast (e.g., revenue, profit) with additional details like time range, promotion applied, and region.

        Your task is to:
        1. Identify the time range (e.g., "2 months", "weekly", or specific date range). If not specified, use "1 month" as default.
        2. Identify the target variables the user is asking for (e.g., "Revenue", "Profit"). If not specified, use ["Revenue", "Profit"] as default.
        3. Identify if any other filters need to be applied, like promotion or region. If not mentioned, assume "No" for promotion and "All" for region.
        4. Provide the output in the following JSON format:

        {{
            "time_range": "2 months",  # e.g., "2 months", "weekly", or a specific date range (Default: "1 month")
            "target_variables": ["Revenue", "Profit"],  # Default: ["Revenue", "Profit"]
            "promotion": "No",  # Optional: if promotion is relevant, or "No" if not mentioned (Default: "No")
            "region": "All",  # Optional: region filter if mentioned, or "All" if not specified (Default: "All")
            "custom_parameters": {{  # Any other user-defined filters (e.g., customer segments, temperature)
                "CustomerSegment": "All"  # Default: "All"
            }}
        }}

        Here is the user's prompt: {prompt}
        """
        
        # Assuming you interact with the LLM API here, and parse the result
        response = {
            "time_range": "2 months",  # default time range
            "target_variables": ["Revenue", "Profit"],  # default variables
            "promotion": "No",  # default promotion status
            "region": "All",  # default region
            "custom_parameters": {
                "CustomerSegment": "All"
            }
        }

        # In a real implementation, the LLM would return a structured response, which would populate the following:
        # e.g., response = request_llm_api(prompt)

        return response

    # Step 1: Extract forecast parameters
    forecast_params = extract_forecast_parameters(prompt, df.columns.tolist())
    
    # Step 2: Filter the DataFrame based on the forecast parameters (e.g., promotion, region, customer segment)
    filtered_df = df.copy()
    
    if forecast_params["promotion"] != "No":
        filtered_df = filtered_df[filtered_df["PromotionApplied"] == forecast_params["promotion"]]
    
    if forecast_params["region"] != "All":
        filtered_df = filtered_df[filtered_df["Region"] == forecast_params["region"]]
    
    if forecast_params["custom_parameters"]["CustomerSegment"] != "All":
        filtered_df = filtered_df[filtered_df["CustomerSegment"] == forecast_params["custom_parameters"]["CustomerSegment"]]

    # Step 3: Predict based on the filtered data
    predictions = predict_from_model(filtered_df, df.columns.tolist(), model_file=model_file)
    
    # Step 4: Return the prediction result
    return predictions


# Example usage
if __name__ == "__main__":
    # Assuming `df` is your loaded dataset and it contains the same columns as your model was trained on
    df = pd.read_csv("your_data.csv")  # Load your dataset here
    
    # User's forecast request
    prompt = "forecast revenue and profit for next 3 months"
    
    forecast_result = forecast_from_prompt(df, prompt)
    print(f"Predictions: {forecast_result}")
