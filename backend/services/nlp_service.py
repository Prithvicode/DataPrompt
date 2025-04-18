import requests
import json
from typing import List, Dict, Any, Generator
import re

# Update this to your Ollama API URL
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "llama3.2"  # Update to your preferred model

def classify_intent(prompt: str, chat_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
    print(f"Prompt from user: {prompt}")
    """
    Classify the intent of the user's prompt using LLaMA.
    
    Returns a dictionary with:
    - type: The type of operation (summary, trend, aggregation, forecast, filter, query)
    - Additional parameters specific to the intent
    """
    # Prepare the system prompt
    system_prompt = """
You are an AI assistant that classifies user queries about datasets into specific analysis intents and extracts required parameters.

You must classify the user's prompt into **one** of the following categories:

1. summary — The user wants a general overview or description of the dataset. Look for words like: "summarize", "overview", "basic stats", "describe", "columns", "missing values", "types", "distribution".
2. trend — The user is asking for trends or patterns over time. Look for: "trend", "change over time", "increasing", "monthly", "weekly", "compare this year to last".
3. aggregation — The user wants to group and aggregate data by one or more columns. Look for: "group by", "average per", "sum by", "total sales by category", etc.
4. forecast — The user wants to predict future values. Look for: "predict", "forecast", "future sales", "next quarter", "estimate", "project".
5. filter — The user wants to extract data that meets certain conditions. Look for: "only show", "filter by", "where", "sales > 1000", "products in category X".
6. query — General questions not fitting the above types. Includes specific lookups or questions like "top 10 products", "how many orders in January", etc.

---

💡 Examples:

- "Give me a summary of the dataset" → summary
- "What are the top-selling products by category?" → aggregation
- "Forecast sales for the next 6 months" → forecast
- "How did revenue change over the last year?" → trend
- "Show me rows where region is 'West'" → filter
- "Which product had the highest sales in March?" → query

---

For each category, extract the following parameters if present:

- trend: `time_column`, `value_column`
- aggregation: `group_by_columns`, `agg_column`, `agg_function`
- forecast: `target_column`, `time_column`, `periods`
- filter: `filter_conditions`

---

🎯 Output:
Respond **ONLY** with a JSON object like this:

```json
{
  "intent": "summary",
  "parameters": {}
}"""

    # Prepare the user prompt
    user_prompt = f"Classify this data analysis query: {prompt}"
    
    # Prepare the messages
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    # Add chat history for context if available
    if chat_history and len(chat_history) > 0:
        # Insert chat history before the current query
        messages = [messages[0]] + chat_history + [messages[1]]
    
    # Make the API call
    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": MODEL_NAME, "messages": messages}
        )
        response.raise_for_status()
        
        # Extract the JSON from the response
        response_text = response.json().get("message", {}).get("content", "")
        
        # Try to extract JSON from the response
        json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # If no JSON code block, try to find JSON directly
            json_match = re.search(r'(\{.*\})', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = response_text
        
        # Parse the JSON
        try:
            intent = json.loads(json_str)
        except json.JSONDecodeError:
            # If JSON parsing fails, use a simple regex-based approach
            intent = {"type": "query"}
            
            if re.search(r'summary|overview|statistics|describe', prompt, re.IGNORECASE):
                intent["type"] = "summary"
            elif re.search(r'trend|over time|timeseries|time series', prompt, re.IGNORECASE):
                intent["type"] = "trend"
                # Try to extract time column
                time_match = re.search(r'by\s+(\w+)', prompt, re.IGNORECASE)
                if time_match:
                    intent["time_column"] = time_match.group(1)
            elif re.search(r'group|aggregate|sum|average|mean', prompt, re.IGNORECASE):
                intent["type"] = "aggregation"
                # Try to extract group by column
                group_match = re.search(r'by\s+(\w+)', prompt, re.IGNORECASE)
                if group_match:
                    intent["group_by_columns"] = [group_match.group(1)]
            elif re.search(r'forecast|predict|future|next', prompt, re.IGNORECASE):
                intent["type"] = "forecast"
                # Try to extract periods
                period_match = re.search(r'next\s+(\d+)', prompt, re.IGNORECASE)
                if period_match:
                    intent["periods"] = int(period_match.group(1))
            elif re.search(r'filter|where|only|show', prompt, re.IGNORECASE):
                intent["type"] = "filter"
        
        return intent
    except Exception as e:
        print(f"Error classifying intent: {str(e)}")
        return {"type": "query"}

def stream_llama_response(
    prompt: str, 
    chat_history: List[Dict[str, str]] = None,
    result: Dict[str, Any] = None,
    intent: Dict[str, Any] = None
) -> Generator[str, None, None]:
    """
    Stream responses from the Llama model.
    Yields chunks of the response as they are generated.
    """
    # Prepare the system prompt
    system_prompt = """
    You are a helpful data analysis assistant. Your job is to explain data analysis results clearly and concisely.
    When given data analysis results, explain:
    1. What the results show
    2. Key insights or patterns
    3. Potential business implications
    
    Keep explanations clear, concise, and focused on the most important aspects of the data.
    Use simple language and avoid technical jargon when possible.
    """
    
    # Prepare the user prompt with context
    user_prompt = prompt
    if result and intent:
        # Add context based on the intent type
        if intent["type"] == "summary":
            user_prompt = f"""
            I've analyzed the data and here's a summary:
            {json.dumps(result, indent=2)}
            
            Based on this summary, please explain: {prompt}
            """
        elif intent["type"] == "trend":
            user_prompt = f"""
            I've analyzed the trends in the data:
            {json.dumps(result, indent=2)}
            
            Based on these trends, please explain: {prompt}
            """
        elif intent["type"] == "aggregation":
            user_prompt = f"""
            I've aggregated the data as requested:
            {json.dumps(result, indent=2)}
            
            Based on these aggregations, please explain: {prompt}
            """
        elif intent["type"] == "forecast":
            user_prompt = f"""
            I've generated a forecast:
            {json.dumps(result, indent=2)}
            
            Based on this forecast, please explain: {prompt}
            """
        elif intent["type"] == "filter":
            user_prompt = f"""
            I've filtered the data as requested:
            {json.dumps(result, indent=2)}
            
            Based on this filtered data, please explain: {prompt}
            """
        else:
            user_prompt = f"""
            I've analyzed the data based on your query:
            {json.dumps(result, indent=2)}
            
            Please explain: {prompt}
            """
    
    # Prepare the messages
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    # Add chat history for context if available
    if chat_history and len(chat_history) > 0:
        # Insert chat history before the current query
        messages = [messages[0]] + chat_history + [messages[1]]
    
    # Make the API call
    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": MODEL_NAME, "messages": messages, "stream": True},
            stream=True
        )
        response.raise_for_status()
        
        for line in response.iter_lines(decode_unicode=True):
            if line:
                try:
                    json_data = json.loads(line)
                    if "message" in json_data and "content" in json_data["message"]:
                        yield json_data["message"]["content"]
                except json.JSONDecodeError:
                    continue
    except Exception as e:
        yield f"Error: Failed to connect to Ollama API. {str(e)}"



















# import re
# import requests
# import json
# from typing import Generator, Dict, Any

# OLLAMA_URL = "http://localhost:11434/api/chat"  # URL of your Ollama API
# MODEL_NAME = "llama3.2"  # Replace with your preferred model

# def extract_operation_from_prompt(prompt: str) -> Dict[str, Any]:
#     """
#     Extract the operation from the user's prompt.
        
#     Returns a dictionary with:
#     - operation: The type of operation (summarize, table, row, forecast, query)
#     - row_value: The row number if operation is 'row'
#     - context: The original prompt for context
#     """
#     prompt_lower = prompt.lower()
    
#     # Check for 'summarize' or 'summary' in prompt
#     if any(word in prompt_lower for word in ["summarize", "summary", "sum up", "summarise"]):
#         return {"operation": "summarize", "context": prompt}
    
#     # Check for row query like "row 3" or "show row 3"
#     match = re.search(r"(?:row|show row)\s+(\d+)", prompt_lower)
#     if match:
#         return {"operation": "row", "row_value": match.group(1), "context": prompt}
    
#     # Check for 'table' or 'show table' in prompt
#     if any(phrase in prompt_lower for phrase in ["table", "show table", "display table"]):
#         return {"operation": "table", "context": prompt}
    
#     # Check for forecast-related keywords
#     if any(word in prompt_lower for word in ["forecast", "predict", "prediction", "forecasting"]):
#         return {"operation": "forecast", "context": prompt}
    
#     # If no specific operation is detected, treat it as a general query
#     return {"operation": "query", "context": prompt}

# def stream_llama_response(prompt: str, context: Dict[str, Any] = None) -> Generator[str, None, None]:
#     """
#     Stream responses from the Llama model.
#     Yields chunks of the response as they are generated.
#     """
#     # Construct the prompt with context if available
#     full_prompt = prompt
#     if context:
#         if context.get("operation") == "summarize":
#             full_prompt = f"""Based on the following data summary, provide a clear and concise explanation:
#             {json.dumps(context.get('data', ''), indent=2)}
            
#             User request: {prompt}
#             """
#         elif context.get("operation") == "table":
#             full_prompt = f"""Based on the following table data, provide a clear and concise explanation:
#             {json.dumps(context.get('data', ''), indent=2)}
            
#             User request: {prompt}
#             """
#         elif context.get("operation") == "row":
#             full_prompt = f"""Based on the following row data, provide a clear and concise explanation:
#             {json.dumps(context.get('data', ''), indent=2)}
            
#             User request: {prompt}
#             """
    
#     payload = {
#         "model": MODEL_NAME,
#         "messages": [{"role": "user", "content": full_prompt}],
#         "stream": True
#     }
    
#     try:
#         response = requests.post(OLLAMA_URL, json=payload, stream=True)
#         response.raise_for_status()
        
#         for line in response.iter_lines(decode_unicode=True):
#             if line:
#                 try:
#                     json_data = json.loads(line)
#                     if "message" in json_data and "content" in json_data["message"]:
#                         yield json_data["message"]["content"]
#                 except json.JSONDecodeError:
#                     continue
#     except requests.exceptions.RequestException as e:
#         yield f"Error: Failed to connect to Ollama API. {str(e)}"

# def generate_summary_with_llama(summary_stats):
#     """
#     Uses the Llama 3 model to generate a natural language explanation of the summary statistics.
#     """
#     summary_text = f"""
#     Provide a brief, super short what is going on in the data. In one line. 
#     {summary_stats}
#     """
    
#     payload = {
#         "model": MODEL_NAME,
#         "messages": [{"role": "user", "content": summary_text}]
#     }
    
#     response = requests.post(OLLAMA_URL, json=payload, stream=True)
    
#     if response.status_code != 200:
#         return "Error: Failed to connect to Ollama API."

#     reply = ""
#     for line in response.iter_lines(decode_unicode=True):
#         if line:
#             try:
#                 json_data = json.loads(line)
#                 if "message" in json_data and "content" in json_data["message"]:
#                     reply += json_data["message"]["content"]
#             except json.JSONDecodeError:
#                 continue
#     # 
#     return reply if reply else "Error generating summary."

# def generate_table_with_llama(table_data):
#     """
#     Uses the Llama 3 model to generate a natural language explanation of the table data.
#     """
#     table_text = f"""
#     Provide a brief, super short overview of the table data. In one line.
#     {json.dumps(table_data)}  # Optional: You can format the table better if needed.
#     """
    
#     payload = {
#         "model": MODEL_NAME,
#         "messages": [{"role": "user", "content": table_text}]
#     }
    
#     response = requests.post(OLLAMA_URL, json=payload, stream=True)
    
#     if response.status_code != 200:
#         return "Error: Failed to connect to Ollama API."

#     reply = ""
#     for line in response.iter_lines(decode_unicode=True):
#         if line:
#             try:
#                 json_data = json.loads(line)
#                 if "message" in json_data and "content" in json_data["message"]:
#                     reply += json_data["message"]["content"]
#             except json.JSONDecodeError:
#                 continue
    
#     return reply if reply else "Error generating table explanation."


#     # Add this new function to handle feature dimension mismatches
# def forecast_data(X_test, model):
#     """
#     Makes predictions with a model while handling feature dimension mismatches.
    
#     Args:
#         X_test: The feature matrix for prediction
#         model: The trained machine learning model
        
#     Returns:
#         Prediction results from the model
#     """
#     # Get expected input dimension from model
#     expected_features = None
    
#     # Try different ways to get the expected feature count based on model type
#     if hasattr(model, 'coef_') and hasattr(model.coef_, 'shape'):
#         if len(model.coef_.shape) > 1:
#             expected_features = model.coef_.shape[1]  # For multi-output models
#         else:
#             expected_features = model.coef_.shape[0]  # For single-output models
    
#     # If it's a sklearn model, we can check the expected input dimension
#     if hasattr(model, 'n_features_in_'):
#         expected_features = model.n_features_in_
    
#     # For the specific error you're getting, we know X_test has shape (31, 13)
#     # and model expects something with 11 features
#     if expected_features is None:
#         # If we couldn't detect it automatically, let's assume it's 11 based on your error
#         expected_features = 11
#         print("Warning: Could not automatically detect model's expected features. Assuming 11 based on error message.")
    
#     # Check and handle dimension mismatch
#     current_features = X_test.shape[1]
#     if current_features != expected_features:
#         print(f"Warning: Feature mismatch. Model expects {expected_features} features but got {current_features}.")
#         # Option 1: Truncate extra features if we have too many
#         if current_features > expected_features:
#             print(f"Truncating extra features to match model expectations ({current_features} -> {expected_features}).")
#             X_test = X_test[:, :expected_features]
#         # Option 2: If we have too few features, we can't proceed
#         else:
#             raise ValueError(f"Model requires {expected_features} features but only {current_features} provided.")
    
#     # Make prediction
#     return model.predict(X_test)

# def generate_llama_response(prompt: str, data: Dict[str, Any] = None) -> str:
#     """
#     Generate a response using the Llama model.
    
#     Args:
#         prompt: The user's prompt
#         data: Optional data to include in the prompt
    
#     Returns:
#         The model's response as a string
#     """
#     # Construct the prompt with context if available
#     full_prompt = prompt
#     if data:
#         if data.get("operation") == "summarize":
#             full_prompt = f"""Based on the following data summary, provide a clear and concise explanation:
#             {json.dumps(data.get('data', ''), indent=2)}
            
#             User request: {prompt}
#             """
#         elif data.get("operation") == "table":
#             full_prompt = f"""Based on the following table data, provide a clear and concise explanation:
#             {json.dumps(data.get('data', ''), indent=2)}
            
#             User request: {prompt}
#             """
#         elif data.get("operation") == "row":
#             full_prompt = f"""Based on the following row data, provide a clear and concise explanation:
#             {json.dumps(data.get('data', ''), indent=2)}
            
#             User request: {prompt}
#             """
#         elif data.get("operation") == "forecast":
#             forecast_data = data.get('data', {})
#             metrics = forecast_data.get('metrics', {})
#             full_prompt = f"""Based on the following forecast results, provide a clear and concise explanation:
            
#             Metrics:
#             - Mean Squared Error: {metrics.get('mse', 'N/A')}
#             - R-squared Score: {metrics.get('r2', 'N/A')}
            
#             The model has generated predictions for the sales data. Please explain the results and what they mean for the business.
            
#             User request: {prompt}
#             """
    
#     payload = {
#         "model": MODEL_NAME,
#         "messages": [{"role": "user", "content": full_prompt}]
#     }
    
#     try:
#         response = requests.post(OLLAMA_URL, json=payload)
#         response.raise_for_status()
        
#         if "response" in response.json():
#             return response.json()["response"]
#         return "No response from model"
#     except Exception as e:
#         return f"Error: {str(e)}"
