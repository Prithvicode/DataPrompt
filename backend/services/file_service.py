from fastapi import UploadFile, HTTPException
import pandas as pd
import io
import os
import uuid
from typing import Dict, Any, List
import json
from datetime import datetime

# In-memory storage for datasets
# In production, use a database or file system
cached_datasets = {}

async def save_file(df: pd.DataFrame, filename: str) -> str:
    """
    Save a DataFrame to in-memory cache and return a dataset ID.
    
    Args:
        df: pandas DataFrame to save
        filename: Original filename
        
    Returns:
        Dataset ID
    """
    dataset_id = str(uuid.uuid4())
    cached_datasets[dataset_id] = {
        "df": df,
        "filename": filename,
        "upload_time": datetime.now().isoformat(),
        "columns": list(df.columns),
        "row_count": len(df)
    }
    return dataset_id

def get_dataset_path(dataset_id: str) -> str:
    """
    Get the path to a dataset.
    In this in-memory implementation, we just return the dataset ID if it exists.
    
    Args:
        dataset_id: Dataset ID
        
    Returns:
        Dataset path or ID
    """
    if dataset_id not in cached_datasets:
        return None
    
    return dataset_id

def list_datasets() -> List[Dict[str, Any]]:
    """
    List all available datasets.
    
    Returns:
        List of dataset information
    """
    return [
        {
            "id": dataset_id,
            "filename": info["filename"],
            "upload_time": info["upload_time"],
            "columns": info["columns"],
            "row_count": info["row_count"]
        }
        for dataset_id, info in cached_datasets.items()
    ]

def get_dataset(dataset_id: str) -> pd.DataFrame:
    """
    Get a dataset by ID.
    
    Args:
        dataset_id: Dataset ID
        
    Returns:
        pandas DataFrame
    """
    if dataset_id not in cached_datasets:
        return None
    
    return cached_datasets[dataset_id]["df"]
