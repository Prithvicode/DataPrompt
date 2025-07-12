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
import math
import aiohttp
import requests

# Import services
from services.file_service import save_file, get_dataset, list_datasets
from services.nlp_service import classify_intent, extract_operation_from_prompt, stream_llama_response
from services.data_service import DataAnalyzer
from services.forecast_service import make_dynamic_prediction, make_prediction


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

def clean_data(data):
    """
    Recursively clean data to remove NaN and infinite float values.
    """
    if isinstance(data, dict):
        return {k: clean_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [clean_data(item) for item in data]
    elif isinstance(data, float):
        return None if math.isinf(data) or math.isnan(data) else data
    elif isinstance(data, (np.integer, np.int64, np.int32, np.int16, np.int8)):
        return int(data)
    elif isinstance(data, (np.floating, np.float64, np.float32, np.float16)):
        return None if math.isinf(data) or math.isnan(data) else float(data)
    elif isinstance(data, pd.Timestamp):
        return data.isoformat()
    elif isinstance(data, pd.Series):
        return clean_data(data.tolist())
    elif isinstance(data, pd.DataFrame):
        return clean_data(data.to_dict(orient='records'))
    elif isinstance(data, np.bool_):
        return bool(data)
    else:
        return data

async def stream_response(generator):
    """
    Helper function to stream the response in a format that the frontend can understand.
    """
    try:
        for chunk in generator:
            if chunk:
                yield f"data: {json.dumps({'content': chunk})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"
    finally:
        yield "data: [DONE]\n\n"

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

@app.get("/health")
async def health_check():
    """
    Simple health check endpoint to verify the backend is running.
    """
    return {
        "status": "healthy",
        "message": "Backend is running",
        "timestamp": datetime.now().isoformat()
    }

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

@app.post("/process")
async def process_file_and_prompt(
    file: UploadFile = File(...), 
    prompt: str = Form(...),
    column_config: str = Form(None)
):
    try:
        if not prompt.strip():
            raise HTTPException(status_code=400, detail="Prompt cannot be empty.")

        # Validate file extension – only CSV files are allowed
        if not file.filename.lower().endswith(".csv"):
            raise HTTPException(status_code=400, detail="Only CSV files are supported.")

        # Read and decode the CSV file
        contents = await file.read()
        if not contents:
            raise HTTPException(status_code=400, detail="File is empty.")
            
        try:
            df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
            if df.empty:
                raise HTTPException(status_code=400, detail="CSV file contains no data.")
        except pd.errors.ParserError as parse_err:
            raise HTTPException(status_code=400, detail=f"CSV Parsing Error: {parse_err}")
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="Invalid file encoding. Please use UTF-8.")

        # Apply column configuration if provided
        if column_config:
            try:
                config = json.loads(column_config)
                numeric_columns = config.get("numeric_columns", [])
                categorical_columns = config.get("categorical_columns", [])
                date_columns = config.get("date_columns", [])
                target_column = config.get("target_column")
                
                # Convert column types
                for col in numeric_columns:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                        
                for col in categorical_columns:
                    if col in df.columns:
                        df[col] = df[col].astype('category')
                        
                for col in date_columns:
                    if col in df.columns:
                        df[col] = pd.to_datetime(df[col], errors='coerce')
                        
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid column configuration format.")

        # Use NLP service to extract operation from the prompt
        op = extract_operation_from_prompt(prompt)
        operation = op.get("operation")
        
        # Process the data based on the operation
        result_data = {}
        response_message = ""
        
        if operation == "summarize":
            # Generate summary statistics using pandas
            if column_config:
                # Use dynamic summary with column configuration
                from services.data_service import DataAnalyzer
                analyzer = DataAnalyzer(df)
                summary_result = analyzer.generate_dynamic_summary(config)
                result_data = summary_result
            else:
                # Use basic summary
                summary_stats = clean_data(df.describe(include="all").to_dict())
                result_data = {
                    "operation": "summarize",
                    "data": summary_stats
                }
            response_message = "Data summary generated."
            
        elif operation == "row":
            row_index = op.get("row_value")
            if row_index is None:
                raise HTTPException(status_code=400, detail="No row number provided in the prompt.")
            
            try:
                row_index = int(row_index)
                if row_index < 0 or row_index >= len(df):
                    raise HTTPException(status_code=400, detail="Row number out of range.")
                
                row_data = clean_data(df.iloc[row_index].to_dict())
                result_data = {
                    "operation": "row",
                    "data": row_data
                }
                response_message = f"Row {row_index} data retrieved."
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid row number provided.")
                
        elif operation == "table":
            # Convert the entire DataFrame to a dictionary
            table_data = clean_data(df.to_dict(orient="records"))
            result_data = {
                "operation": "table",
                "data": table_data
            }
            response_message = "Table data retrieved."
            
        elif operation == "forecast":
            # Make predictions using the forecast service with dynamic configuration
            if column_config and target_column:
                forecast_results = make_dynamic_prediction(df, config)
            else:
                forecast_results = make_prediction(df)
            result_data = {
                "operation": "forecast",
                "data": forecast_results
            }
            response_message = "Forecast completed successfully."
            
        else:
            # For general queries, just return a message
            response_message = "No specific operation detected. Please try again with a more specific prompt."
            result_data = {
                "operation": "query",
                "data": None
            }
        
        # Generate a natural language explanation using the LLM
        explanation_generator = stream_llama_response(prompt, result_data)
        
        # Return streaming response
        return StreamingResponse(
            stream_response(explanation_generator),
            media_type="text/event-stream"
        )

    except Exception as e:
        print(f"[ERROR] Process endpoint error: {e}")
        print(f"[ERROR] Error type: {type(e)}")
        import traceback
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/upload-and-analyze")
async def upload_and_analyze(file: UploadFile = File(...)):
    """
    Upload a CSV file and return column information for configuration.
    """
    try:
        if not file.filename.lower().endswith(".csv"):
            raise HTTPException(status_code=400, detail="Only CSV files are supported.")

        contents = await file.read()
        if not contents:
            raise HTTPException(status_code=400, detail="File is empty.")
            
        try:
            df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
            if df.empty:
                raise HTTPException(status_code=400, detail="CSV file contains no data.")
        except pd.errors.ParserError as parse_err:
            raise HTTPException(status_code=400, detail=f"CSV Parsing Error: {parse_err}")
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="Invalid file encoding. Please use UTF-8.")

        # Analyze columns
        columns_info = []
        for col in df.columns:
            col_info = {
                "name": col,
                "dtype": str(df[col].dtype),
                "unique_values": int(df[col].nunique()),
                "missing_values": int(df[col].isnull().sum()),
                "sample_values": df[col].dropna().unique()[:5].tolist()
            }
            
            # Auto-detect column type
            if df[col].dtype in ['int64', 'float64']:
                col_info["suggested_type"] = "numeric"
            elif df[col].dtype == 'object':
                # Check if it might be a date
                try:
                    pd.to_datetime(df[col].dropna().iloc[:10])
                    col_info["suggested_type"] = "date"
                except:
                    col_info["suggested_type"] = "categorical"
            else:
                col_info["suggested_type"] = "categorical"
                
            columns_info.append(col_info)

        return {
            "filename": file.filename,
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "columns": columns_info
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/configure-columns")
async def configure_columns(
    file: UploadFile = File(...),
    column_config: str = Form(...)
):
    """
    Configure column types and target variable for analysis.
    """
    try:
        print(f"[DEBUG] Starting configure-columns with file: {file.filename}")
        
        # Parse column configuration
        try:
            config = json.loads(column_config)
            print(f"[DEBUG] Parsed config: {config}")
        except json.JSONDecodeError as e:
            print(f"[ERROR] Failed to parse column_config JSON: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid JSON in column_config: {str(e)}")
        
        # Read the file
        try:
            contents = await file.read()
            if not contents:
                raise HTTPException(status_code=400, detail="File is empty")
            
            df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
            if df.empty:
                raise HTTPException(status_code=400, detail="CSV file contains no data")
            
            print(f"[DEBUG] Successfully read CSV with {len(df)} rows and {len(df.columns)} columns")
            print(f"[DEBUG] Columns: {df.columns.tolist()}")
            
        except pd.errors.ParserError as e:
            print(f"[ERROR] CSV parsing error: {e}")
            raise HTTPException(status_code=400, detail=f"CSV Parsing Error: {str(e)}")
        except UnicodeDecodeError as e:
            print(f"[ERROR] File encoding error: {e}")
            raise HTTPException(status_code=400, detail="Invalid file encoding. Please use UTF-8.")
        except Exception as e:
            print(f"[ERROR] File reading error: {e}")
            raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")
        
        # Apply column configuration
        numeric_columns = config.get("numeric_columns", [])
        categorical_columns = config.get("categorical_columns", [])
        date_columns = config.get("date_columns", [])
        target_column = config.get("target_column")
        
        print(f"[DEBUG] Configuring columns - Numeric: {numeric_columns}, Categorical: {categorical_columns}, Date: {date_columns}, Target: {target_column}")
        
        # Validate that all configured columns exist in the DataFrame
        all_configured_columns = set(numeric_columns + categorical_columns + date_columns)
        if target_column:
            all_configured_columns.add(target_column)
        
        missing_columns = all_configured_columns - set(df.columns)
        if missing_columns:
            print(f"[ERROR] Missing columns in DataFrame: {missing_columns}")
            raise HTTPException(status_code=400, detail=f"Columns not found in dataset: {list(missing_columns)}")
        
        # Convert column types with error handling
        try:
            for col in numeric_columns:
                if col in df.columns:
                    print(f"[DEBUG] Converting {col} to numeric")
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    
            for col in categorical_columns:
                if col in df.columns:
                    print(f"[DEBUG] Converting {col} to categorical")
                    df[col] = df[col].astype('category')
                    
            for col in date_columns:
                if col in df.columns:
                    print(f"[DEBUG] Converting {col} to datetime")
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                    
        except Exception as e:
            print(f"[ERROR] Error converting column types: {e}")
            raise HTTPException(status_code=400, detail=f"Error converting column types: {str(e)}")
        
        # Clean data for response
        try:
            processed_data = clean_data(df.head(10).to_dict(orient="records"))
        except Exception as e:
            print(f"[ERROR] Error cleaning data: {e}")
            processed_data = []
        
        print(f"[DEBUG] Configuration completed successfully")
        
        # Store configuration in session or return processed data
        return {
            "message": "Column configuration applied successfully",
            "target_column": target_column,
            "numeric_columns": numeric_columns,
            "categorical_columns": categorical_columns,
            "date_columns": date_columns,
            "processed_data": processed_data
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        print(f"[ERROR] Unexpected error in configure-columns: {e}")
        print(f"[ERROR] Error type: {type(e)}")
        import traceback
        print(f"[ERROR] Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

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



