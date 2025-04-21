from typing import Dict, Any, List, Optional
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
import pandas as pd
import numpy as np
import json

def create_visualization(result: Dict[str, Any], intent_type: str) -> Dict[str, Any]:
    """
    Create visualization specifications based on analysis results.
    
    Args:
        result: Analysis result
        intent_type: Type of analysis
        
    Returns:
        Visualization specification
    """
    print(f"[DEBUG] Creating visualization for intent type: {intent_type}")
    
    if not result or "data" not in result:
        print("[ERROR] No data available for visualization")
        return None
    
    # Check if chart_data is available in the result
    if "chart_data" in result:
        print(f"[DEBUG] Found chart_data in result with {len(result['chart_data'])} points")
        return {
            "type": intent_type,
            "chart_data": result["chart_data"]
        }
    
    if intent_type == "summary":
        return create_summary_visualization(result)
    elif intent_type == "trend":
        return create_trend_visualization(result)
    elif intent_type == "aggregation":
        return create_aggregation_visualization(result)
    elif intent_type == "forecast":
        return create_forecast_visualization(result)
    elif intent_type == "filter":
        return create_filter_visualization(result)
    else:
        return create_generic_visualization(result)

def create_summary_visualization(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create visualization for summary results.
    """
    print("[DEBUG] Creating summary visualization")
    
    if "data" not in result or "dataset_info" not in result["data"]:
        print("[ERROR] Invalid summary data structure")
        return None
    
    dataset_info = result["data"]["dataset_info"]
    
    # Create column type distribution chart
    column_types = {
        "Numeric": len(dataset_info.get("numeric_columns", [])),
        "Categorical": len(dataset_info.get("categorical_columns", [])),
        "Date": len(dataset_info.get("date_columns", []))
    }
    
    print(f"[DEBUG] Column types: {column_types}")
    
    # Create chart data in the format expected by the frontend
    chart_data = [
        {"month": "Column Types", "desktop": column_types["Numeric"], "mobile": column_types["Categorical"]}
    ]
    
    # If there are missing values, add them to the chart
    if "missing_values" in dataset_info:
        missing_values = dataset_info["missing_values"]
        missing_count = sum(missing_values.values())
        if missing_count > 0:
            print(f"[DEBUG] Found {missing_count} missing values")
            chart_data.append({"month": "Missing Values", "desktop": missing_count, "mobile": 0})
    
    return {
        "type": "summary",
        "chart_data": chart_data
    }

def create_trend_visualization(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create visualization for trend results.
    """
    print("[DEBUG] Creating trend visualization")
    
    if "data" not in result or not result["data"]:
        print("[ERROR] No data available for trend visualization")
        return None
    
    data = result["data"]
    time_column = result.get("time_column", "period")
    value_column = result.get("value_column", "value")
    
    # Create chart data in the format expected by the frontend
    chart_data = []
    for record in data:
        if "period" in record and "sum" in record:
            chart_data.append({
                "month": record["period"],
                "desktop": float(record["sum"]),
                "mobile": float(record.get("growth", 0)) if "growth" in record and pd.notna(record["growth"]) else 0
            })
    
    print(f"[DEBUG] Created trend chart data with {len(chart_data)} points")
    
    return {
        "type": "trend",
        "chart_data": chart_data
    }

def create_aggregation_visualization(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create visualization for aggregation results.
    """
    print("[DEBUG] Creating aggregation visualization")
    
    if "data" not in result or not result["data"]:
        print("[ERROR] No data available for aggregation visualization")
        return None
    
    data = result["data"]
    group_by_columns = result.get("group_by_columns", [])
    agg_column = result.get("agg_column")
    
    if not group_by_columns or not agg_column:
        print("[ERROR] Missing group_by_columns or agg_column")
        return None
    
    # Use the first group by column for visualization
    group_col = group_by_columns[0]
    
    # Create chart data in the format expected by the frontend
    chart_data = []
    for record in data:
        if group_col in record and agg_column in record:
            chart_data.append({
                "month": str(record[group_col]),
                "desktop": float(record[agg_column]),
                "mobile": 0  # No secondary metric for aggregation
            })
    
    print(f"[DEBUG] Created aggregation chart data with {len(chart_data)} points")
    
    return {
        "type": "aggregation",
        "chart_data": chart_data
    }

def create_forecast_visualization(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create visualization for forecast results.
    """
    print("[DEBUG] Creating forecast visualization")
    
    if "data" not in result or not result["data"]:
        print("[ERROR] No data available for forecast visualization")
        return None
    
    data = result["data"]
    
    # Create chart data in the format expected by the frontend
    chart_data = []
    for record in data:
        if "period" in record and "value" in record:
            chart_data.append({
                "month": record["period"],
                "desktop": float(record["value"]),
                "mobile": float(record.get("profit", 0)) if "profit" in record else 0
            })
    
    print(f"[DEBUG] Created forecast chart data with {len(chart_data)} points")
    
    return {
        "type": "forecast",
        "chart_data": chart_data
    }

def create_filter_visualization(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create visualization for filter results.
    """
    print("[DEBUG] Creating filter visualization")
    
    if "data" not in result or not result["data"]:
        print("[ERROR] No data available for filter visualization")
        return None
    
    data = result["data"]
    
    # For filtered data, try to find numeric columns to visualize
    if not data or not isinstance(data, list) or len(data) == 0:
        print("[ERROR] Invalid or empty data for filter visualization")
        return None
    
    # Get the first record to determine columns
    first_record = data[0]
    numeric_cols = []
    
    # Find numeric columns
    for key, value in first_record.items():
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            numeric_cols.append(key)
    
    print(f"[DEBUG] Found {len(numeric_cols)} numeric columns for filter visualization")
    
    if not numeric_cols:
        print("[WARNING] No numeric columns found for visualization")
        return None
    
    # Use the first two numeric columns for visualization
    primary_col = numeric_cols[0] if numeric_cols else None
    secondary_col = numeric_cols[1] if len(numeric_cols) > 1 else None
    
    # Create chart data in the format expected by the frontend
    chart_data = []
    for i, record in enumerate(data[:10]):  # Limit to 10 records for visualization
        if primary_col:
            chart_data.append({
                "month": f"Record {i+1}",
                "desktop": float(record.get(primary_col, 0)),
                "mobile": float(record.get(secondary_col, 0)) if secondary_col else 0
            })
    
    print(f"[DEBUG] Created filter chart data with {len(chart_data)} points")
    
    return {
        "type": "filter",
        "chart_data": chart_data
    }

def create_generic_visualization(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a generic visualization for query results.
    """
    print("[DEBUG] Creating generic visualization")
    
    if "data" not in result:
        print("[ERROR] No data available for generic visualization")
        return None
    
    data = result["data"]
    
    # If data is a list of dictionaries, try to visualize it
    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
        return create_filter_visualization(result)
    
    # Otherwise, no visualization
    print("[WARNING] Cannot create visualization for this data type")
    return None