import requests
import json
import os
from fastapi import FastAPI, UploadFile, File, Form

app = FastAPI()

OLLAMA_URL = "http://localhost:8000/api/chat"
MODEL_NAME = "llama3.2"  # Replace with the actual model name you're using

@app.post('/process-prompt')
def query_ollama(prompt: str):
    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": prompt}]
    }
    response = requests.post(OLLAMA_URL, json=payload, stream=True)
    
    if response.status_code == 200:
        output = ""
        for line in response.iter_lines(decode_unicode=True):
            if line:
                try:
                    json_data = json.loads(line)
                    if "message" in json_data and "content" in json_data["message"]:
                        output += json_data["message"]["content"]
                except json.JSONDecodeError:
                    print(f"Failed to parse line: {line}")
        return output
    else:
        return f"Error: {response.status_code} - {response.text}"

@app.post("/process-file")
def process_file(prompt: str = Form(...), file: UploadFile = File(...)):
    temp_file_path = f"temp/{file.filename}"
    os.makedirs("temp", exist_ok=True)
    
    with open(temp_file_path, "wb") as out_file:
        out_file.write(file.file.read())
    
    with open(temp_file_path, "r", encoding="utf-8") as f:
        file_content = f.read()
    
    os.remove(temp_file_path)
    
    return {"response": query_ollama(prompt + "\n" + file_content)}
