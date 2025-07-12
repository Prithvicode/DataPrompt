from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import pandas as pd
import io
import os
import uuid
from typing import Dict, Any, List, Optional
import json
from datetime import datetime
import asyncio
from pydantic import BaseModel
import numpy as np
# Import services
from services.file_service import save_file, get_dataset, list_datasets
from services.nlp_service import classify_intent
from services.data_service import DataAnalyzer
import aiohttp

import requests



# In-memory storage for datasets and analysis jobs
cached_datasets = {}
analysis_jobs = {}

app = FastAPI(title="DataPrompt API")

# Add CORS middleware to allow requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatMessage(BaseModel):
    role: str
    content: str

class AnalyzeRequest(BaseModel):
    prompt: str
    dataset_id: str
    chat_history: Optional[List[ChatMessage]] = None

class ChatRequest(BaseModel):
    prompt: str
    chat_history: Optional[List[ChatMessage]] = None
    job_id: Optional[str] = None


import math
import numpy as np
import pandas as pd
import json

def make_json_safe(data):
    """
    Recursively convert all NumPy and pandas types to Python native types,
    and sanitize non-JSON-compliant float values (NaN, inf).
    """
    if data is None:
        return None
    elif isinstance(data, dict):
        return {k: make_json_safe(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [make_json_safe(item) for item in data]
    elif isinstance(data, (np.integer, np.int64, np.int32, np.int16, np.int8)):
        return int(data)
    elif isinstance(data, (np.floating, float, np.float64, np.float32, np.float16)):
        # Catch NaN, inf, -inf
        if math.isnan(data) or math.isinf(data):
            return None
        return float(data)
    elif isinstance(data, (np.ndarray,)):
        return make_json_safe(data.tolist())
    elif isinstance(data, pd.Timestamp):
        return data.isoformat()
    elif isinstance(data, pd.Series):
        return make_json_safe(data.tolist())
    elif isinstance(data, pd.DataFrame):
        return make_json_safe(data.to_dict(orient='records'))
    elif isinstance(data, np.bool_):
        return bool(data)
    elif hasattr(data, 'to_json'):
        return json.loads(data.to_json())
    elif hasattr(data, '__dict__'):
        return make_json_safe(vars(data))
    else:
        return data

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a CSV file and return a dataset ID.
    """
    if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only CSV and Excel files are supported")
    
    try:
        # Read the file content
        contents = await file.read()
        
        # Create a BytesIO object from the contents
        file_obj = io.BytesIO(contents)
        
        # Determine file type and read with pandas
        if file.filename.endswith('.csv'):
            df = pd.read_csv(file_obj)
        else:  # Excel file
            df = pd.read_excel(file_obj)
        
        # Save the DataFrame to in-memory cache
        dataset_id = str(uuid.uuid4())
        cached_datasets[dataset_id] = {
            "df": df,
            "filename": file.filename,
            "upload_time": datetime.now().isoformat(),
            "columns": list(df.columns),
            "row_count": len(df)
        }
        
        return {
            "id": dataset_id,
            "filename": file.filename,
            "columns": list(df.columns),
            "row_count": len(df)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    finally:
        # Reset file pointer and close
        await file.seek(0)
        await file.close()
@app.get("/test")
async def test():
    return {"message": "Hello, World!"}

@app.get("/datasets")
async def list_datasets():
    """
    List all available datasets.
    """
    datasets = [
        {
            "id": dataset_id,
            "filename": info["filename"],
            "upload_time": info["upload_time"],
            "columns": info["columns"],
            "row_count": info["row_count"]
        }
        for dataset_id, info in cached_datasets.items()
    ]
    
    return {"datasets": datasets}

@app.get("/datasets/{dataset_id}")
async def get_dataset(dataset_id: str):
    """
    Get information about a specific dataset.
    """
    if dataset_id not in cached_datasets:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    info = cached_datasets[dataset_id]
    return {
        "id": dataset_id,
        "filename": info["filename"],
        "upload_time": info["upload_time"],
        "columns": info["columns"],
        "row_count": info["row_count"],
        "preview": info["df"].head(10).to_dict(orient='records')
    }


@app.post("/analyze")
async def analyze_data(request: AnalyzeRequest, background_tasks: BackgroundTasks):
    """
    Analyze data based on a prompt. Classify intent and handle accordingly.
    """
    if request.dataset_id not in cached_datasets:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    df = cached_datasets[request.dataset_id]["df"]
    analyzer = DataAnalyzer(df)

    # Create and store job
    job_id = str(uuid.uuid4())
    analysis_jobs[job_id] = {
        "status": "processing",
        "prompt": request.prompt,
        "dataset_id": request.dataset_id,
        "result": None
    }

    try:
        # Classify the intent of the user prompt
        intent_info = classify_intent(request.prompt)
        intent = intent_info.get("intent", "query")
        parameters = intent_info.get("parameters", {})

        print(f"[DEBUG] Classified intent: {intent}, Parameters: {parameters}")

        # Handle invalid intent early
        if intent == "error":
            error_message = (
                " Sorry, I couldn't understand your request. "
                "It seems unrelated to the dataset or may include unsupported or unsafe instructions.\n\n"
                " Try asking about your data like:\n"
                "- 'Give me a summary of the dataset'\n"
                "- 'Filter sales data for Product Category Grocery only'"
            )
            
            analysis_jobs[job_id]["status"] = "completed"
            analysis_jobs[job_id]["intent"] = "error"  # explicitly set intent
            analysis_jobs[job_id]["result"] = {"message": error_message}

            return {
                "job_id": job_id,
                "result": make_json_safe({"message": error_message})
            }

        # Handle valid intents
        if intent == "summary":
            # result = analyzer.generate_summary()
            result = analyzer.generate_user_friendly_summary()

        elif intent == "query":
            result = analyzer.execute_query(request.prompt, df.columns.tolist())

        elif intent == "trend":
            result = analyzer.analyze_trend(request.prompt, **parameters)

        elif intent == "forecast":
            result = analyzer.forecast(request.prompt, **parameters)

        elif intent == "predict":
            result = analyzer.predict(request.prompt, **parameters)

        elif intent == "whatif":
            print("heelo")
            result = analyzer.what_if_analysis(request.prompt, **parameters)

        elif intent == "aggregation":
            result = analyzer.aggregate(request.prompt, df.columns.tolist())

        elif intent == "filter":
            result = analyzer.filter_data(request.prompt, df.columns.tolist())

        else:
            raise HTTPException(status_code=400, detail=f"Unsupported intent: {intent}")

        # Handle DataFrame result
        if isinstance(result, pd.DataFrame):
            result = {"message": "No data found"} if result.empty else result.to_dict(orient="records")

        # Finalize and return
        analysis_jobs[job_id]["result"] = result
        analysis_jobs[job_id]["status"] = "completed"

        return {
            "job_id": job_id,
            "result": make_json_safe(result)
        }

    except Exception as e:
        analysis_jobs[job_id]["status"] = "failed"
        analysis_jobs[job_id]["result"] = {"error": str(e)}
        raise HTTPException(status_code=500, detail=str(e))


async def generate_chat_response(prompt: str, job_id: Optional[str] = None):
    job_info = analysis_jobs.get(job_id)
    
    def format_data(content: str, error: bool = False):
        return f"data: {json.dumps({'content': content, 'error': error})}\n\n"
    
    if job_info and job_info["result"]:
        result = job_info["result"]

        if job_info.get("intent") == "error":
            yield format_data(result["message"], error=True)
            await asyncio.sleep(0.1)
            yield format_data("[DONE]")
            return
        
        yield format_data("✅ Data analyzed. Now generating explanation...\n\n")
        await asyncio.sleep(0.1)

        if isinstance(result, pd.DataFrame):
            result = json.dumps(result.to_dict(orient="records"), indent=2)

        if job_info.get("intent") == "whatif":
            # Separate historical and forecast data if needed
            forecast_data_only = result[result["type"] == "forecast"].to_string(index=False)

            llama_prompt = f"""
            You are an assistant in the DataPrompt app. Your task is to explain analysis results clearly and simply for end users.

            - Keep the explanation short and easy to understand.
            - Currency is in NRs (Nepali Rupees).
            - Format the response as clean, user-friendly **Markdown** for the frontend UI.
            - Explain the analysis based on the user's original intent.

            Context:
            - **User Intent**: {job_info.get("intent")}
            - **User Prompt**: {prompt}

            - **Forecast Result (after applying what-if changes)**:
            {forecast_data_only}

            Focus only on the **forecasted changes** after applying the what-if scenario. Do not describe historical data or overall trends unless necessary.
            """
        else:
            llama_prompt = f"""
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
- User Intent: {job_info.get("intent")}
- User Prompt: {prompt}
- Result (for your reference only, do NOT return this): {result}

Your task:
Write a short interpretation of the result above, as if explaining it to a non-technical user. Return only the explanation in Markdown — no raw output or JSON.

Output (Markdown explanation only):
"""



        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    OLLAMA_URL,
                    json={"model": MODEL_NAME, "prompt": llama_prompt, "stream": True},
                ) as response:
                    if response.status == 200:
                        async for line in response.content:
                            if line:
                                chunk = json.loads(line.decode())
                                if content := chunk.get("response", ""):
                                    yield format_data(content)
                                if chunk.get("done", False):
                                    break
                        yield format_data("[DONE]")
                    else:
                        yield format_data(f"LLM Error: {response.status}", error=True)
        except Exception as e:
            yield format_data(f"Connection Error: {str(e)}", error=True)
    else:
        yield format_data("No analysis result available", error=True)
    
    yield format_data("[DONE]")

OLLAMA_URL = "http://localhost:11434/api/generate"
# MODEL_NAME = "llama3.2"
# MODEL_NAME = "llama3.2:1b"
# MODEL_NAME = "llama3.2:1b"
# MODEL_NAME = "qwen2.5:1.5b"
MODEL_NAME = "qwen2.5:0.5b"




@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Chat with the AI about the data.
    """
    return StreamingResponse(
        generate_chat_response(request.prompt, request.job_id),
        # generate_llama_response(request.prompt),
        media_type="text/event-stream"
    )

# ============== Test
# def generate_llama_response(prompt: str):
#     sample_df = pd.DataFrame({
#         "Product": ["Widget A", "Widget B", "Widget C"],
#         "UnitsSold": [120, 85, 60],
#         "Revenue": [2400.0, 1700.0, 1200.0],
#         "Profit": [600.0, 450.0, 300.0],
#         "Region": ["North", "South", "West"]
#     })

#     # Convert the DataFrame to a readable markdown table or CSV-style string
#     table_str = json.dumps(sample_df.to_dict(orient="records"), indent=2)

#     full_prompt = (
#         "Explain the following analysis result in simple terms and properly structure it in the markdown:\n\n"
#         f"{table_str}\n\n"
#         f"{prompt.strip()}"
#     )
#     payload = {
#         "model": MODEL_NAME,
#         "prompt": full_prompt,
#         "result": sample_df.to_dict(orient='records')  # Convert DataFrame to list of dicts
#     }

#     try:
#         # Make a synchronous POST request to the LLaMA API
#         response = requests.post(OLLAMA_URL, json=payload, stream=True)
#         print("Response from LLaMA:", response.text)
#         # Check for successful response
#         if response.status_code == 200:
#             for chunk in response.iter_lines():
#                 if chunk:
#                     yield f"data: {chunk.decode('utf-8')}\n\n"
#         else:
#             yield f"data: [Error {response.status_code}: Failed to get response from LLaMA]\n\n"

#     except requests.RequestException as e:
#         yield f"data: [Error: {str(e)}]\n\n"
        
# # Test simple streaming response
# @app.post("/stream")
# def stream(prompt: str):
#     return StreamingResponse(generate_llama_response(prompt), media_type="text/event-stream")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)



