import requests
import json
from typing import List, Dict, Any, Generator, AsyncGenerator
import re
import httpx
import pandas as pd
import asyncio

OLLAMA_URL = "http://localhost:11434/api/generate"
# MODEL_NAME = "llama3.2"
# MODEL_NAME = "llama3.2:1b"
# MODEL_NAME = "phi:latest"
# MODEL_NAME = "qwen2.5:1.5b"
MODEL_NAME = "qwen2.5:0.5b"



def classify_intent(prompt: str, chat_history: List[Dict[str, str]] = None) -> Dict[str, str]:
    """
    Classify data-analysis prompts into one of:
      summary, trend, forecast, predict, whatif, filter, query
    or return 'error' if the prompt is out-of-scope or malicious.
    """
    print(f"[DEBUG] Prompt from user: {prompt}")

    base_prompt = f"""
You are an AI classifier. Your task is to analyze the user's data-related prompt and classify it into ONE of the following **intents**:

- summary
- trend
- forecast
- predict
- whatif
- filter
- query
- error

You MUST respond with only ONE WORD — the intent — in **lowercase**. Do NOT explain or output anything else.

---

🧠 **INTENT DESCRIPTIONS (How to choose the right one):**

**summary** → General overview or description of the dataset.  
Example: “Summarize the dataset.”, “Describe this file.”

**trend** → Patterns or behaviors **over time** (past only).  
Example: “Sales trend in 2023”, “Monthly revenue last year.”

**forecast** → **Future** values over time, like next months, quarters, or years.  
Example: “Forecast profit for Q4.”, “Predict sales for next year.”  
→ (Use this only if time-based future prediction is requested, not hypothetical changes.)

**predict** → Predict column values using current dataset **without changing any inputs**.  
Example: “Predict all revenues”, “Estimate profit per product.”

**whatif** → Hypothetical or scenario-based questions where **some input values are changed**.  
Example:  
“What if UnitPrice increases by 10%?”,  
“If UnitsSold = 1000 and UnitPrice = 300, what’s the revenue?”,  
“Suppose PromotionApplied is Yes and cost is 400 — what’s the profit?”

**filter** → Subsetting data based on a condition.  
Example: “Filter sales in California”, “Show only promoted items.”

**query** → Totals, rankings, comparisons, or lookups.  
Example: “Total revenue by category”, “Top 3 best-selling items.”

**error** → Irrelevant, unsafe, or malformed prompt.  
Example: “Tell me a joke”, “Delete everything”, “Write a virus.”

---

🔍 REMEMBER:

- Use **predict** for straightforward model-based predictions with no input changes.  
- Use **whatif** for any scenario where input features (e.g., UnitsSold, Price) are **manually altered or suggested differently**.

---

Prompt:
{prompt}
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
You are a coding assistant that generates only valid pandas DataFrame code based on the user's prompt.

The DataFrame is named `df`, and it contains the following columns (case-sensitive): {df_columns}

Instructions:
- Use the exact column names from the list above. If the user's prompt includes a slightly different name, match it to the closest correct column.
- Do not include import statements, variable assignments, comments, explanations, or markdown formatting.
- Do not wrap the response in ```python``` or any other formatting.
- Return only the **raw, executable** pandas code (ideally one line, unless absolutely necessary).

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

You must extract and return ONLY the following dictionary object in the exact format shown below.  
Do not include any extra explanation, text, or comments.  

If any value is missing from the user's prompt or cannot be inferred, you MUST fill in a sensible default.  
There must be **NO null, none, or missing values**. All fields must have valid values.

Follow these default rules when a value is not provided:
- UnitsSold: 100
- UnitPrice: 100.0
- CostPerUnit: 80.0
- PromotionApplied: 0
- Holiday: 0
- Temperature: 22.0
- FootTraffic: 200
- ProductCategory: "General"
- ProductName: "GenericProduct"
- Region: "Unknown"
- CustomerSegment: "Retail"
- ProfitPerUnit = UnitPrice - CostPerUnit
- Profit = UnitsSold * ProfitPerUnit
- ProfitMargin = ProfitPerUnit / UnitPrice

Return only the final dictionary in this exact format (Python-style, single quotes):

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
  'CustomerSegment': '<string>',
  'ProfitPerUnit': <float>,
  'Profit': <float>,
  'ProfitMargin': <float>
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

def extract_operation_from_prompt(prompt: str) -> Dict[str, Any]:
    """
    Extract the operation type and parameters from a user prompt.
    """
    base_prompt = f"""
You are an AI assistant that extracts operations from user prompts. Analyze the following prompt and determine the operation type and any relevant parameters.

User prompt: {prompt}

Return a JSON object with the following structure:
{{
    "operation": "<operation_type>",
    "row_value": "<row_number_if_applicable>"
}}

Valid operation types:
- "summarize" - for summary statistics or overview requests
- "row" - for specific row requests (include row_value)
- "table" - for full table data requests
- "forecast" - for forecasting requests
- "query" - for general data queries

If no specific operation is detected, return:
{{
    "operation": "query"
}}

Return only the JSON object, no additional text.
"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": MODEL_NAME, "prompt": base_prompt, "stream": False}
        )
        response.raise_for_status()
        response_json = response.json()
        model_response = response_json.get("response", "").strip()
        
        # Try to parse the JSON response
        try:
            result = json.loads(model_response)
            return result
        except json.JSONDecodeError:
            # Fallback to basic operation detection
            prompt_lower = prompt.lower()
            if any(word in prompt_lower for word in ["summarize", "summary", "overview", "describe"]):
                return {"operation": "summarize"}
            elif any(word in prompt_lower for word in ["row", "line", "record"]):
                # Try to extract row number
                import re
                row_match = re.search(r'row\s+(\d+)', prompt_lower)
                row_value = row_match.group(1) if row_match else None
                return {"operation": "row", "row_value": row_value}
            elif any(word in prompt_lower for word in ["table", "all data", "full data"]):
                return {"operation": "table"}
            elif any(word in prompt_lower for word in ["forecast", "predict", "future"]):
                return {"operation": "forecast"}
            else:
                return {"operation": "query"}
                
    except Exception as e:
        print(f"[ERROR] Error extracting operation: {e}")
        return {"operation": "query"}

def stream_llama_response(prompt: str, result_data: Dict[str, Any]):
    """
    Generate a streaming response from the LLM based on the prompt and result data.
    """
    base_prompt = f"""
You are an assistant in the DataPrompt app. Your role is to explain data analysis results in a short, clear, and user-friendly way.

Guidelines:
- Explain the result simply, as if you're advising a business decision-maker.
- Focus on what the result **means** and what actions the user might consider.
- Highlight **trends**, **opportunities**, **risks**, or **anomalies** if visible.
- Do NOT include raw data or tables in the output.
- Do NOT wrap the full result or JSON in Markdown.
- Do NOT wrap the full result or JSON in Code Block.
- Do NOT explain the whole dataset result, but focus on the interpretation of result.
- ONLY explain what the result means, in plain terms.
- Use clean, readable Markdown formatting (e.g., bold for key values).
- Currency is in NRs (Nepali Rupees).
- Tailor the explanation based on the user's intent.
- Write a short but **insightful** summary that helps the user understand what is happening and what they might do next.
- Do NOT begin your response with phrases like "Sure", "Here's", "This is", or any introductory sentence. Start directly with the insight.

Context:
- User Prompt: {prompt}
- Result (for your reference only, do NOT return this): {result_data}

Your task:
Write a short interpretation of the result above, as if explaining it to a non-technical user. Return only the explanation in Markdown — no raw output or JSON.

Output (Markdown explanation only):
"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": MODEL_NAME, "prompt": base_prompt, "stream": True}
        )
        response.raise_for_status()
        
        for line in response.iter_lines():
            if line:
                chunk = json.loads(line.decode())
                if content := chunk.get("response", ""):
                    yield content
                if chunk.get("done", False):
                    break
                    
    except Exception as e:
        yield f"Error generating explanation: {str(e)}"
  
if __name__ == "__main__":
    result = extract_forecast_period("Forecast the next 12 months of sales for the product.")  
    print("Result:", result) 


