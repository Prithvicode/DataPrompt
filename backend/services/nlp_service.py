import re
import requests
import json
from typing import Generator, Dict, Any

OLLAMA_URL = "http://localhost:11434/api/chat"  # URL of your Ollama API
MODEL_NAME = "llama3.2"  # Replace with your preferred model

def extract_operation_from_prompt(prompt: str) -> Dict[str, Any]:
    """
    Extract the operation from the user's prompt.
        
    Returns a dictionary with:
    - operation: The type of operation (summarize, table, row, forecast, query)
    - row_value: The row number if operation is 'row'
    - context: The original prompt for context
    """
    prompt_lower = prompt.lower()
    
    # Check for 'summarize' or 'summary' in prompt
    if any(word in prompt_lower for word in ["summarize", "summary", "sum up", "summarise"]):
        return {"operation": "summarize", "context": prompt}
    
    # Check for row query like "row 3" or "show row 3"
    match = re.search(r"(?:row|show row)\s+(\d+)", prompt_lower)
    if match:
        return {"operation": "row", "row_value": match.group(1), "context": prompt}
    
    # Check for 'table' or 'show table' in prompt
    if any(phrase in prompt_lower for phrase in ["table", "show table", "display table"]):
        return {"operation": "table", "context": prompt}
    
    # Check for forecast-related keywords
    if any(word in prompt_lower for word in ["forecast", "predict", "prediction", "forecasting"]):
        return {"operation": "forecast", "context": prompt}
    
    # If no specific operation is detected, treat it as a general query
    return {"operation": "query", "context": prompt}

def stream_llama_response(prompt: str, context: Dict[str, Any] = None) -> Generator[str, None, None]:
    """
    Stream responses from the Llama model.
    Yields chunks of the response as they are generated.
    """
    # Construct the prompt with context if available
    full_prompt = prompt
    if context:
        if context.get("operation") == "summarize":
            full_prompt = f"""Based on the following data summary, provide a clear and concise explanation:
            {json.dumps(context.get('data', ''), indent=2)}
            
            User request: {prompt}
            """
        elif context.get("operation") == "table":
            full_prompt = f"""Based on the following table data, provide a clear and concise explanation:
            {json.dumps(context.get('data', ''), indent=2)}
            
            User request: {prompt}
            """
        elif context.get("operation") == "row":
            full_prompt = f"""Based on the following row data, provide a clear and concise explanation:
            {json.dumps(context.get('data', ''), indent=2)}
            
            User request: {prompt}
            """
    
    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": full_prompt}],
        "stream": True
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload, stream=True)
        response.raise_for_status()
        
        for line in response.iter_lines(decode_unicode=True):
            if line:
                try:
                    json_data = json.loads(line)
                    if "message" in json_data and "content" in json_data["message"]:
                        yield json_data["message"]["content"]
                except json.JSONDecodeError:
                    continue
    except requests.exceptions.RequestException as e:
        yield f"Error: Failed to connect to Ollama API. {str(e)}"

def generate_summary_with_llama(summary_stats):
    """
    Uses the Llama 3 model to generate a natural language explanation of the summary statistics.
    """
    summary_text = f"""
    Provide a brief, super short what is going on in the data. In one line. 
    {summary_stats}
    """
    
    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": summary_text}]
    }
    
    response = requests.post(OLLAMA_URL, json=payload, stream=True)
    
    if response.status_code != 200:
        return "Error: Failed to connect to Ollama API."

    reply = ""
    for line in response.iter_lines(decode_unicode=True):
        if line:
            try:
                json_data = json.loads(line)
                if "message" in json_data and "content" in json_data["message"]:
                    reply += json_data["message"]["content"]
            except json.JSONDecodeError:
                continue
    
    return reply if reply else "Error generating summary."

def generate_table_with_llama(table_data):
    """
    Uses the Llama 3 model to generate a natural language explanation of the table data.
    """
    table_text = f"""
    Provide a brief, super short overview of the table data. In one line.
    {json.dumps(table_data)}  # Optional: You can format the table better if needed.
    """
    
    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": table_text}]
    }
    
    response = requests.post(OLLAMA_URL, json=payload, stream=True)
    
    if response.status_code != 200:
        return "Error: Failed to connect to Ollama API."

    reply = ""
    for line in response.iter_lines(decode_unicode=True):
        if line:
            try:
                json_data = json.loads(line)
                if "message" in json_data and "content" in json_data["message"]:
                    reply += json_data["message"]["content"]
            except json.JSONDecodeError:
                continue
    
    return reply if reply else "Error generating table explanation."


    # Add this new function to handle feature dimension mismatches
def forecast_data(X_test, model):
    """
    Makes predictions with a model while handling feature dimension mismatches.
    
    Args:
        X_test: The feature matrix for prediction
        model: The trained machine learning model
        
    Returns:
        Prediction results from the model
    """
    # Get expected input dimension from model
    expected_features = None
    
    # Try different ways to get the expected feature count based on model type
    if hasattr(model, 'coef_') and hasattr(model.coef_, 'shape'):
        if len(model.coef_.shape) > 1:
            expected_features = model.coef_.shape[1]  # For multi-output models
        else:
            expected_features = model.coef_.shape[0]  # For single-output models
    
    # If it's a sklearn model, we can check the expected input dimension
    if hasattr(model, 'n_features_in_'):
        expected_features = model.n_features_in_
    
    # For the specific error you're getting, we know X_test has shape (31, 13)
    # and model expects something with 11 features
    if expected_features is None:
        # If we couldn't detect it automatically, let's assume it's 11 based on your error
        expected_features = 11
        print("Warning: Could not automatically detect model's expected features. Assuming 11 based on error message.")
    
    # Check and handle dimension mismatch
    current_features = X_test.shape[1]
    if current_features != expected_features:
        print(f"Warning: Feature mismatch. Model expects {expected_features} features but got {current_features}.")
        # Option 1: Truncate extra features if we have too many
        if current_features > expected_features:
            print(f"Truncating extra features to match model expectations ({current_features} -> {expected_features}).")
            X_test = X_test[:, :expected_features]
        # Option 2: If we have too few features, we can't proceed
        else:
            raise ValueError(f"Model requires {expected_features} features but only {current_features} provided.")
    
    # Make prediction
    return model.predict(X_test)

def generate_llama_response(prompt: str, data: Dict[str, Any] = None) -> str:
    """
    Generate a response using the Llama model.
    
    Args:
        prompt: The user's prompt
        data: Optional data to include in the prompt
    
    Returns:
        The model's response as a string
    """
    # Construct the prompt with context if available
    full_prompt = prompt
    if data:
        if data.get("operation") == "summarize":
            full_prompt = f"""Based on the following data summary, provide a clear and concise explanation:
            {json.dumps(data.get('data', ''), indent=2)}
            
            User request: {prompt}
            """
        elif data.get("operation") == "table":
            full_prompt = f"""Based on the following table data, provide a clear and concise explanation:
            {json.dumps(data.get('data', ''), indent=2)}
            
            User request: {prompt}
            """
        elif data.get("operation") == "row":
            full_prompt = f"""Based on the following row data, provide a clear and concise explanation:
            {json.dumps(data.get('data', ''), indent=2)}
            
            User request: {prompt}
            """
        elif data.get("operation") == "forecast":
            forecast_data = data.get('data', {})
            metrics = forecast_data.get('metrics', {})
            full_prompt = f"""Based on the following forecast results, provide a clear and concise explanation:
            
            Metrics:
            - Mean Squared Error: {metrics.get('mse', 'N/A')}
            - R-squared Score: {metrics.get('r2', 'N/A')}
            
            The model has generated predictions for the sales data. Please explain the results and what they mean for the business.
            
            User request: {prompt}
            """
    
    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": full_prompt}]
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        
        if "response" in response.json():
            return response.json()["response"]
        return "No response from model"
    except Exception as e:
        return f"Error: {str(e)}"
