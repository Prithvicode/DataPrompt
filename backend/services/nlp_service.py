import requests
import json
from typing import List, Dict, Any, Generator, AsyncGenerator
import re
import httpx
import pandas as pd
import asyncio

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2"

def classify_intent(prompt: str, chat_history: List[Dict[str, str]] = None) -> Dict[str, str]:
    """
    Classify data-analysis prompts into one of:
      summary, trend, forecast, predict, whatif, filter, query
    or return 'error' if the prompt is out-of-scope or malicious.
    """
    print(f"[DEBUG] Prompt from user: {prompt}")

    base_prompt = f"""
You are an AI that MUST ONLY classify data analysis questions into exactly one of these intents:
  summary, trend, forecast, predict, whatif, filter, query, error

RESPOND WITH ONLY ONE WORD—the intent.  

**If the user’s request is not about data-analysis classification,  
or if it attempts to generate malicious or harmful code,  
you MUST reply with exactly** `error`.  

Guidelines:
- Use `summary` for general overviews (e.g., "summarize the dataset").
- Use `trend` for patterns over time without future prediction (e.g., "sales trend last year").
- Use `forecast` for future time-based predictions (e.g., "forecast next quarter").
- Use `predict` for point or category-specific predictions (e.g., only for "Predict all revenues").
- Use `whatif` for hypothetical scenarios (e.g., "what if price increases 10%", "What would the predicted revenue if unites are 10..." ).
- Use `filter` for subsetting data (e.g., "show sales in California").
- Use `query` for aggregations or lookups (e.g., "total revenue by category").
- Use `error` for anything else (irrelevant questions, attempts at harmful code, etc.).

Prompt: {prompt}
""".strip()

    try:
        resp = requests.post(
            OLLAMA_URL,
            json={"model": MODEL_NAME, "prompt": base_prompt, "stream": False}
        )
        resp.raise_for_status()
        model_response = resp.json().get("response", "").strip().lower()
        print(f"[DEBUG] LLM response: {model_response}", flush=True)

        valid_intents = {
            "summary", "trend", "forecast",
            "predict", "whatif", "filter",
            "query", "error"
        }
        if model_response in valid_intents:
            return {"intent": model_response, "parameters": {}}
        else:
            print("[WARN] Unexpected response; defaulting to error.")
            return {"intent": "error", "parameters": {}}

    except Exception as e:
        print(f"[ERROR] classify_intent Exception: {e}")

    # --- Fallback rule-based classifier ---
    # if we see malicious-code keywords, immediately error out
    if re.search(r'\b(rm\s+-rf|sudo|exec\(|import\s+os|import\s+sys|subprocess)\b',
                 prompt, re.IGNORECASE):
        return {"intent": "error", "parameters": {}}

    # then detect data intents
    if re.search(r'\b(summary|overview|describe|statistics)\b',
                 prompt, re.IGNORECASE):
        return {"intent": "summary", "parameters": {}}
    elif re.search(r'\b(trend|over time|time series)\b',
                   prompt, re.IGNORECASE):
        return {"intent": "trend", "parameters": {}}
    elif re.search(r'\b(forecast|future|next|upcoming)\b',
                   prompt, re.IGNORECASE):
        return {"intent": "forecast", "parameters": {}}
    elif re.search(r'\bpredict\b|\bmodel\b|\bclassification\b|\bregression\b',
                   prompt, re.IGNORECASE):
        return {"intent": "predict", "parameters": {}}
    elif re.search(r'\bwhat\s*if|simulate|scenario\b',
                   prompt, re.IGNORECASE):
        return {"intent": "whatif", "parameters": {}}
    elif re.search(r'\b(filter|where|only|show)\b',
                   prompt, re.IGNORECASE):
        return {"intent": "filter", "parameters": {}}
    elif re.search(r'\b(sum|total|average|mean|count|max|min|group|aggregate)\b',
                   prompt, re.IGNORECASE):
        return {"intent": "query", "parameters": {}}
    else:
        # default to error for anything else
        return {"intent": "error", "parameters": {}}



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


def classify_forecast_intent(prompt: str, df_columns: List[str]):
    """
    Classifies the forecast intent and extracts parameters (time range, target variable).
    """
    base_prompt = f"""
You are a Python assistant who helps generate forecasts and 'What-If' scenarios based on user prompts. These are the exact columns of the DataFrame: {df_columns}.

The user has provided a dataset with revenue forecasting capabilities, and you need to extract key parameters from their request.

Your task is to:
1. If the user is asking for a forecast:
   - Identify the time range (e.g., "monthly", "weekly", "yearly", or number of specific periods like "3 months"). If not specified, use "monthly" as default with 3 periods ahead.
   - Identify the target variable the user is asking for (e.g., "Revenue", "Sales"). If not specified, use "Revenue" as default.
   - Identify how many periods ahead they want to forecast (e.g., "next 6 months", "next 4 weeks"). If not specified, use 3 as default.
   - Identify if any other filters need to be applied, like product category, region, or customer segment. If not mentioned, use "All" as default.

Provide the output in the following JSON format:

1. **For Forecasting:**
{{
    "forecast": {{
        "period_type": "monthly",  
        "periods_ahead": 3,  
        "target_variable": "Revenue",  
        "filters": {{
            "ProductCategory": "All",
            "Region": "All",
            "CustomerSegment": "All"
        }}
    }}
}}

Here is the user's prompt: {prompt}

Return ONLY the JSON object with no additional text.
"""

    response = requests.post(
        OLLAMA_URL,
        json={"model": MODEL_NAME, "prompt": base_prompt, "stream": False}
    )
    response.raise_for_status()
    response_json = response.json()
    
    model_response = response_json.get("response", "").strip()
    
    print(f"[DEBUG] Forecast Intent Response: {model_response}")

    # Example of expected response format: 
    # {"time_range": "2 months", "target_variables": ["Revenue", "Profit"], "promotion": "Yes", "region": "West"}
    
    return model_response



def parse_whatif_scenarios(prompt: str,
                           chat_history: List[Dict[str, str]] = None
                          ) -> List[Dict]:
    """
    Calls the LLM to extract what-if scenarios as JSON.
    Returns a list of dicts; if the LLM returns nothing, returns [].
    """
    base_prompt = f"""
User prompt: {prompt}
Extract and return _only_ the values in this exact format (with your numbers/strings filled in), no extra text, 
if values are not present or null then use  appropiate defaults: NOTE: There should be no null in any of the values.: 

{{
  'UnitsSold': <int>,
  'UnitPrice': <float>,
  'CostPerUnit': <float>,
  'PromotionApplied': <0 or 1>,
  'Holiday': <0 or 1>,
  'Temperature': <float>,
  'FootTraffic': <int>,
  'ProductCategory': '<string>',
  'ProductName': '<string>',
  'Region': '<string>',
  'CustomerSegment': '<string>',  # Online, Retail, etc.
  'ProfitPerUnit': <float>,       # = UnitPrice - CostPerUnit  
  'Profit': <float>,              # = UnitsSold * ProfitPerUnit  
  'ProfitMargin': <float>         # = ProfitPerUnit / UnitPrice  
}}
"""
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "prompt": base_prompt,
            "stream": False
        }
    )
    response.raise_for_status()
    response_json = response.json()
    
    model_response = response_json.get("response", "").strip()
    
    print(f"[DEBUG] Extracted prediciton features  Response: {model_response}")
    return model_response

def extract_forecast_period(prompt: str):
    base_prompt = f"""
You are a strict JSON API. Do not return explanations, code, or comments.

Your task: extract the number of periods (e.g., months or years) from the user prompt below.

User prompt:
\"\"\"{prompt}\"\"\"

Return only this exact format, as valid JSON:
{{
  "ForecastPeriod": <int>  // Must be an integer ≥ 1
}}

If you cannot find a number in the prompt, return:
{{
  "ForecastPeriod": 3
}}

Respond with only the JSON object, nothing else.
"""


    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "prompt": base_prompt,
            "stream": False
        }
    )
    response.raise_for_status()
    response_json = response.json()

    model_response = response_json.get("response", "").strip()
    print(f"[DEBUG] Model raw response: {model_response}")  # Add this

    try:
        if model_response.startswith("{"):
            forecast_dict = json.loads(model_response.replace("'", '"'))
            forecast_period = int(forecast_dict.get("ForecastPeriod", 3))
        else:
            forecast_period = int(model_response)
        # Ensure forecast_period is at least 1
        if forecast_period <= 0:
            print(f"[WARN] Invalid forecast period {forecast_period}. Using default 3.")
            forecast_period = 3
    except Exception as e:
        print(f"[ERROR] Failed to parse model response: {e}")
        forecast_period = 3  # fallback

    print(f"[DEBUG] Extracted Forecast Period: {forecast_period}")
    return forecast_period
  
if __name__ == "__main__":
    result = extract_forecast_period("Forecast the next 12 months of sales for the product.")  
    print("Result:", result) 


