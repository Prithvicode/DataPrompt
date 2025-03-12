from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import json
from services.nlp_service import process_file, query_ollama

app = FastAPI()

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Allow only the Next.js frontend
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"],  # Allow all headers
)

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "llama3.2"  # Replace with your model

class PromptRequest(BaseModel):
    prompt: str

@app.post("/chat")
def chat_with_ollama(request: PromptRequest):
    
    payload = {
        "model": MODEL_NAME,
        "messages": [{"role": "user", "content": request.prompt}]
    }
    
    response = requests.post(OLLAMA_URL, json=payload, stream=True)
    
    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    
    reply = ""
    for line in response.iter_lines(decode_unicode=True):
        if line:
            try:
                json_data = json.loads(line)
                if "message" in json_data and "content" in json_data["message"]:
                    reply += json_data["message"]["content"]
            except json.JSONDecodeError:
                continue
    
    return {"response": reply}
