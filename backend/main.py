from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
from fastapi.responses import StreamingResponse
import pandas as pd
import io
import math
import json
from services import nlp_service
from services import forecast_service

app = FastAPI()

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Only allow frontend origin
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

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

@app.post("/process")
async def process_file_and_prompt(file: UploadFile = File(...), prompt: str = Form(...)):
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

        # Use NLP service to extract operation from the prompt
        op = nlp_service.extract_operation_from_prompt(prompt)
        operation = op.get("operation")
        
        # Process the data based on the operation
        result_data = {}
        response_message = ""
        
        if operation == "summarize":
            # Generate summary statistics using pandas
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
            # Make predictions using the forecast service
            forecast_results = forecast_service.make_prediction(df)
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
        explanation_generator = nlp_service.stream_llama_response(prompt, result_data)
        
        # Return streaming response
        return StreamingResponse(
            stream_response(explanation_generator),
            media_type="text/event-stream"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
