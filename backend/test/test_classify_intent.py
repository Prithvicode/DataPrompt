import re
import requests
from typing import List, Dict

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2"

def classify_intent(prompt: str) -> Dict[str, str]:
    print(f"[DEBUG] Prompt from user: {prompt}")
    
    base_prompt = f"""
You are an AI that classifies data analysis queries into one of the following intents: summary, trend, aggregation, forecast, filter, or query.
Respond with only the intent name as a single word. Do not include explanations, formatting, or any extra text.

Prompt: {prompt}
Intent:
""".strip()

    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": MODEL_NAME, "prompt": base_prompt, "stream": False}
        )
        response.raise_for_status()

        # Print raw JSON before parsing
        response_json = response.json()
        print(f"[DEBUG] Raw JSON: {response_json}")

        model_response = response_json.get("response", "").strip().lower()
        print(f"[DEBUG] LLM response: {model_response}")
        
        valid_intents = {"summary", "trend", "aggregation", "forecast", "filter", "query"}
        if model_response in valid_intents:
            return {"intent": model_response, "parameters": {}}
        else:
            print("[WARN] Invalid LLM response. Using fallback.")
    except Exception as e:
        print(f"[ERROR] classify_intent failed: {str(e)}")

    # Fallback regex
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

# 🧪 Test examples
if __name__ == "__main__":
    test_prompts = [
        "Give me a summary of the dataset",
        "What are the trends in sales over the past year?",
        "Show the average sales per category",
        "Forecast the revenue for next month",
        "Only show rows where sales > 1000",
        "Top 10 products with most orders"
    ]

    for prompt in test_prompts:
        result = classify_intent(prompt)
        print(f"Prompt: {prompt}\n → Classified intent: {result['intent']}\n")
