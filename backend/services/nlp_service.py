import requests
import json
from typing import List, Dict, Any, Generator
import re


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2"

def classify_intent(prompt: str, chat_history: List[Dict[str, str]] = None) -> Dict[str, str]:
    print(f"[DEBUG] Prompt from user: {prompt}")

    base_prompt = f"""
You are an AI that classifies data analysis queries into one of these intents: summary, trend, aggregation, forecast, filter, or query.
Respond with only one word representing the intent.
Do not include any other text.

Prompt: {prompt}
""".strip()

    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": MODEL_NAME, "prompt": base_prompt, "stream": False}
        )
        response.raise_for_status()
        
        response_json = response.json()
        model_response = response_json.get("response", "").strip().lower()
        print(f"[DEBUG] LLM response: {model_response}",flush=True)

        valid_intents = {"summary", "trend", "aggregation", "forecast", "filter", "query"}
        if model_response in valid_intents:
            return {"intent": model_response, "parameters": {}}
        else:
            print("[WARN] Invalid response from model. Falling back to regex.")

    except requests.exceptions.JSONDecodeError as e:
        print(f"[ERROR] JSON decoding error: {str(e)}")
    except Exception as e:
        print(f"[ERROR] Exception during classify_intent: {str(e)}")

    # Fallback: regex-based rule classification
    if re.search(r'summary|overview|describe|statistics', prompt, re.IGNORECASE):
        return {"intent": "summary", "parameters": {}}
    elif re.search(r'trend|over time|timeseries|time series', prompt, re.IGNORECASE):
        return {"intent": "trend", "parameters": {}}
    elif re.search(r'group|aggregate|sum|average|mean|by', prompt, re.IGNORECASE):
        return {"intent": "aggregation", "parameters": {}}
    elif re.search(r'forecast|predict|future|next', prompt, re.IGNORECASE):
        return {"intent": "forecast", "parameters": {}}
    elif re.search(r'filter|where|only|show', prompt, re.IGNORECASE):
        return {"intent": "filter", "parameters": {}}
    else:
        return {"intent": "query", "parameters": {}}
    
    
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


def generate_panda_code_from_prompt(prompt: str, df_columns: List[str]):
    """
    Generate a pandas code snippet based on the user's prompt.
    Sends prompt to LLM with proper instructions to use correct column names.
    """
    base_prompt = f"""
You are a helpful Python assistant that generates concise pandas DataFrame code based on a user query.

Here are the exact columns of the DataFrame: {df_columns}

Please write only the pandas code using the variable `df`, without imports, print statements, or variable assignments. Use the correct column names (case-sensitive) from the list above. If a column mentioned in the user's prompt is ambiguous or slightly different, choose the closest match from the list. 

Respond only with a single line of code (unless absolutely necessary), and make sure it can be executed as-is.

User prompt: {prompt}
"""

    response = requests.post(
        OLLAMA_URL,
        json={"model": MODEL_NAME, "prompt": base_prompt, "stream": False}
    )
    response.raise_for_status()
    
    response_json = response.json()
    model_response = response_json.get("response", "").strip()

    print(f"[DEBUG] LLM response: {model_response}", flush=True)
    return model_response



