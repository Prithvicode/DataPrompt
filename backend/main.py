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
from services.nlp_service import classify_intent, stream_llama_response
from services.data_service import DataAnalyzer
from services.visualization_service import create_visualization


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


def make_json_safe(data):
    """
    Recursively convert all NumPy and pandas types to Python native types
    to ensure JSON serialization works correctly.
    """
    if data is None:
        return None
    elif isinstance(data, dict):
        return {k: make_json_safe(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [make_json_safe(item) for item in data]
    elif isinstance(data, (np.integer, np.int64, np.int32, np.int16, np.int8)):
        return int(data)
    elif isinstance(data, (np.floating, np.float64, np.float32, np.float16)):
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
        # Handle objects with to_json method
        return json.loads(data.to_json())
    elif hasattr(data, '__dict__'):
        # Handle custom objects by converting to dict
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

        if intent == "summary":
            result = analyzer.generate_summary()

        elif intent == "query":
            result = analyzer.execute_query(request.prompt)

        elif intent == "trend":
            result = analyzer.analyze_trend(request.prompt, **parameters)

        elif intent == "forecast":
            result = analyzer.forecast(request.prompt, **parameters)

        elif intent == "whatif":
            result = analyzer.what_if_analysis(request.prompt, **parameters)
            
        elif intent == "aggregation":
            result = analyzer.aggregate(request.prompt, **parameters)

        elif intent == "filter":
            # Pass the columns of the dataframe along with the prompt to filter_data
            # print("Columns:", df.columns.tolist())
            result = analyzer.filter_data(request.prompt, df.columns.tolist())
            print("Thes result",result)

        else:
            raise HTTPException(status_code=400, detail=f"Unsupported intent: {intent}")

        # Check if result is a DataFrame and handle accordingly
        if isinstance(result, pd.DataFrame):
            if result.empty:
                result = {"message": "No data found"}
            else:
                result = result.to_dict(orient="records")  # Convert DataFrame to a list of records

        # Update the job with result and set status to completed
        analysis_jobs[job_id]["result"] = result
        analysis_jobs[job_id]["status"] = "completed"

        safe_result = make_json_safe(result)
        return {
            "job_id": job_id,
            "result": safe_result
        }

    except Exception as e:
        # In case of an error, set the job status to failed and capture the error
        analysis_jobs[job_id]["status"] = "failed"
        analysis_jobs[job_id]["result"] = {"error": str(e)}
        raise HTTPException(status_code=500, detail=str(e))


async def generate_chat_response(prompt: str, job_id: Optional[str] = None):
    """
    Generate a streaming chat response.
    """
    job_info = None
    if job_id and job_id in analysis_jobs:
        job_info = analysis_jobs[job_id]

    def format_data(content: str):
        return f"data: {json.dumps({'content': content})}\n\n"

    # Start with a greeting
    yield format_data("I've analyzed your data.")
    await asyncio.sleep(0.5)

    if job_info and job_info["result"]:
        result = job_info["result"]

        # Check the type of result before accessing it
        if isinstance(result, dict) and "type" in result:
            if result["type"] == "summary":
                data_info = result["data"]["dataset_info"]
                yield format_data(f"Your dataset has {data_info['rows']} rows and {data_info['columns']} columns.")
                await asyncio.sleep(0.5)

                yield format_data(f"The columns are: {', '.join(data_info['column_names'][:5])}...")
                await asyncio.sleep(0.5)

                missing_values = sum(data_info['missing_values'].values())
                if missing_values > 0:
                    yield format_data(f"There are {missing_values} missing values in the dataset.")
                    await asyncio.sleep(0.5)
        elif isinstance(result, list):
            # Handle the case when result is a list (like DataFrame records)
            records_count = len(result)
            yield format_data(f"I found {records_count} matching records in your dataset.")
            await asyncio.sleep(0.5)
            
            # Optionally show a preview of the first few records
            if records_count > 0:
                yield format_data("Here's a sample of what I found:")
                await asyncio.sleep(0.5)
                
                # Show first 3 records or fewer if less are available
                sample_size = min(3, records_count)
                for i in range(sample_size):
                    yield format_data(f"Record {i+1}: {str(result[i])}")
                    await asyncio.sleep(0.3)
        elif isinstance(result, dict) and "message" in result:
            # Handle message-only results
            yield format_data(result["message"])
            await asyncio.sleep(0.5)
        elif isinstance(result, dict) and "error" in result:
            # Handle error results
            yield format_data(f"I encountered an error: {result['error']}")
            await asyncio.sleep(0.5)
        else:
            # Generic fallback for other result types
            yield format_data(f"Analysis complete. Result type: {type(result).__name__}")
            await asyncio.sleep(0.5)

    yield format_data("You can ask me more specific questions about this data if you'd like.")
    await asyncio.sleep(0.5)

    # Signal the end
    yield "data: [DONE]\n\n"

@app.post("/chat")
async def chat(request: ChatRequest):
    """
    Chat with the AI about the data.
    """
    return StreamingResponse(
        generate_chat_response(request.prompt, request.job_id),
        media_type="text/event-stream"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)



