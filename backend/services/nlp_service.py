import re
import requests
import json

OLLAMA_URL = "http://localhost:11434/api/chat"  # URL of your Ollama API
MODEL_NAME = "llama3.2"  # Replace with the correct model name

def extract_operation_from_prompt(prompt: str) -> dict:
    """
    Extract the operation from the user's prompt.
    
    - If the prompt contains 'summarize', return {'operation': 'summarize'}.
    - If the prompt contains a row query (e.g., "row 3"), extract the row number.
    - If the prompt contains 'table', return {'operation': 'table'}.
    - Otherwise, return {'operation': 'unsupported'}.
    """
    prompt_lower = prompt.lower()
    
    # Check for 'summarize' or 'summary' in prompt
    if "summarize" in prompt_lower or "summary" in prompt_lower:
        return {"operation": "summarize"}
    
    # Check for row query like "row 3"
    match = re.search(r"row\s+(\d+)", prompt_lower)
    if match:
        return {"operation": "row", "row_value": match.group(1)}
    
    # Check for 'table' in prompt
    if "table" in prompt_lower:
        return {"operation": "table"}
    
    return {"operation": "unsupported"}

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
