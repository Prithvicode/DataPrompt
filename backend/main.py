from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.encoders import jsonable_encoder
import pandas as pd
import io
import math
from services import nlp_service

app = FastAPI()

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for debugging
    allow_credentials=True,
    allow_methods=["*"],
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
        try:
            df = pd.read_csv(io.StringIO(contents.decode("utf-8")))
        except pd.errors.ParserError as parse_err:
            raise HTTPException(status_code=400, detail=f"CSV Parsing Error: {parse_err}")

        # Use NLP service to extract operation from the prompt
        op = nlp_service.extract_operation_from_prompt(prompt)
        operation = op.get("operation")

        if operation == "summarize":
            summary_stats = clean_data(df.describe(include="all").to_dict())
            response_message = "Data summary generated."
            result = {
                "summary_stats": summary_stats,
                "summary_explanation": "Summary text goes here...",
            }
        elif operation == "row":
            row_index = op.get("row_value")
            if row_index is None:
                response_message = "No row number provided in the prompt."
                result = {}
            else:
                try:
                    row_index = int(row_index)
                    if row_index < 0 or row_index >= len(df):
                        response_message = "Row number out of range."
                        result = {}
                    else:
                        result = clean_data(df.iloc[row_index].to_dict())
                        response_message = f"Row {row_index} data retrieved."
                except ValueError:
                    response_message = "Invalid row number provided."
                    result = {}
        elif operation == "table":
            # Convert the entire DataFrame to a dictionary and clean it
            result = clean_data(df.to_dict(orient="records"))
            response_message = "Table data retrieved."
        else:
            response_message = "Unsupported operation."
            result = "Supported operations: summarize, row <number>, table."

        return {"response": response_message, "data": jsonable_encoder(result)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
