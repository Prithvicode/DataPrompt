from typing import Dict, Any, List, Optional
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
import pandas as pd
import numpy as np

def create_visualization(result: Dict[str, Any], intent_type: str) -> Dict[str, Any]:
    """
    Create visualization specifications based on analysis results.
    
    Args:
        result: Analysis result
        intent_type: Type of analysis
        
    Returns:
        Visualization specification
    """
    if not result or "data" not in result:
        return None
    
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
    if "data" not in result or "dataset_info" not in result["data"]:
        return None
    
    dataset_info = result["data"]["dataset_info"]
    
    # Create column type distribution chart
    column_types = {
        "Numeric": len(dataset_info.get("numeric_columns", [])),
        "Categorical": len(dataset_info.get("categorical_columns", [])),
        "Date": len(dataset_info.get("date_columns", []))
    }
    
    plt.figure(figsize=(10, 6))
    plt.bar(column_types.keys(), column_types.values(), color=['#4285F4', '#34A853', '#FBBC05'])
    plt.title('Column Types Distribution')
    plt.ylabel('Count')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Save plot to base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    column_types_plot = base64.b64encode(buffer.read()).decode('utf-8')
    plt.close()
    
    # Create missing values chart if available
    missing_values_plot = None
    if "missing_values" in dataset_info:
        missing_values = dataset_info["missing_values"]
        
        # Filter to only columns with missing values
        missing_values = {k: v for k, v in missing_values.items() if v > 0}
        
        if missing_values:
            plt.figure(figsize=(10, 6))
            plt.bar(missing_values.keys(), missing_values.values(), color='#DB4437')
            plt.title('Missing Values by Column')
            plt.ylabel('Count')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            
            # Save plot to base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png')
            buffer.seek(0)
            missing_values_plot = base64.b64encode(buffer.read()).decode('utf-8')
            plt.close()
    
    return {
        "type": "summary",
        "plots": {
            "column_types": column_types_plot,
            "missing_values": missing_values_plot
        }
    }

def create_trend_visualization(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create visualization for trend results.
    """
    if "data" not in result or not result["data"]:
        return None
    
    data = result["data"]
    time_column = result.get("time_column")
    value_column = result.get("value_column")
    
    if not time_column or not value_column:
        return None
    
    # Create DataFrame from data
    df = pd.DataFrame(data)
    
    # Create line chart
    plt.figure(figsize=(10, 6))
    plt.plot(df[time_column], df["sum"], marker='o', linestyle='-', color='#4285F4')
    plt.title(f'{value_column} Trend Over Time')
    plt.xlabel(time_column)
    plt.ylabel(value_column)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    # Save plot to base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    trend_plot = base64.b64encode(buffer.read()).decode('utf-8')
    plt.close()
    
    # Create growth chart if available
    growth_plot = None
    if "growth" in df.columns:
        plt.figure(figsize=(10, 6))
        plt.bar(df[time_column], df["growth"], color=['#34A853' if x >= 0 else '#DB4437' for x in df["growth"]])
        plt.title(f'{value_column} Period-over-Period Growth (%)')
        plt.xlabel(time_column)
        plt.ylabel('Growth (%)')
        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        # Save plot to base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        growth_plot = base64.b64encode(buffer.read()).decode('utf-8')
        plt.close()
    
    return {
        "type": "trend",
        "plots": {
            "trend": trend_plot,
            "growth": growth_plot
        },
        "visualization": {
            "type": "line",
            "title": f"{value_column} Trend Over Time",
            "data": data,
            "x": time_column,
            "y": "sum",
            "xLabel": time_column,
            "yLabel": value_column
        }
    }

def create_aggregation_visualization(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create visualization for aggregation results.
    """
    if "data" not in result or not result["data"]:
        return None
    
    data = result["data"]
    group_by_columns = result.get("group_by_columns", [])
    agg_column = result.get("agg_column")
    agg_function = result.get("agg_function", "sum")
    
    if not group_by_columns or not agg_column:
        return None
    
    # Create DataFrame from data
    df = pd.DataFrame(data)
    
    # Use the first group by column for visualization
    group_col = group_by_columns[0]
    
    # Sort by aggregated value
    df = df.sort_values(by=agg_column, ascending=False)
    
    # Limit to top 10 for visualization
    if len(df) > 10:
        df = df.head(10)
    
    # Create bar chart
    plt.figure(figsize=(10, 6))
    plt.bar(df[group_col].astype(str), df[agg_column], color='#4285F4')
    plt.title(f'{agg_function.capitalize()} of {agg_column} by {group_col}')
    plt.xlabel(group_col)
    plt.ylabel(f'{agg_function.capitalize()} of {agg_column}')
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    # Save plot to base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    agg_plot = base64.b64encode(buffer.read()).decode('utf-8')
    plt.close()
    
    return {
        "type": "aggregation",
        "plots": {
            "aggregation": agg_plot
        },
        "visualization": {
            "type": "bar",
            "title": f"{agg_function.capitalize()} of {agg_column} by {group_col}",
            "data": data,
            "x": group_col,
            "y": agg_column,
            "xLabel": group_col,
            "yLabel": f"{agg_function.capitalize()} of {agg_column}"
        }
    }

def create_forecast_visualization(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create visualization for forecast results.
    """
    # If we already have a plot, use it
    if "plot" in result:
        return {
            "type": "forecast",
            "plots": {
                "forecast": result["plot"]
            }
        }
    
    if "data" not in result or not result["data"]:
        return None
    
    data = result["data"]
    target_column = result.get("target_column")
    
    if not target_column:
        return None
    
    # Create DataFrame from data
    df = pd.DataFrame(data)
    
    # Create line chart
    plt.figure(figsize=(10, 6))
    
    # Plot historical data
    historical = df[df["is_forecast"] == False]
    plt.plot(historical["period"], historical["value"], marker='o', linestyle='-', color='#4285F4', label='Historical')
    
    # Plot forecast data
    forecast = df[df["is_forecast"] == True]
    if not forecast.empty:
        plt.plot(forecast["period"], forecast["value"], marker='o', linestyle='--', color='#FBBC05', label='Forecast')
    
    plt.title(f'Forecast for {target_column}')
    plt.xlabel('Period')
    plt.ylabel(target_column)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.xticks(rotation=45, ha='right')
    plt.legend()
    plt.tight_layout()
    
    # Save plot to base64
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    forecast_plot = base64.b64encode(buffer.read()).decode('utf-8')
    plt.close()
    
    return {
        "type": "forecast",
        "plots": {
            "forecast": forecast_plot
        },
        "visualization": {
            "type": "line",
            "title": f"Forecast for {target_column}",
            "data": data,
            "x": "period",
            "y": "value",
            "series": "is_forecast",
            "xLabel": "Period",
            "yLabel": target_column
        }
    }

def create_filter_visualization(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create visualization for filter results.
    """
    if "data" not in result or not result["data"]:
        return None
    
    data = result["data"]
    
    # For filtered data, we'll create a simple table visualization
    return {
        "type": "filter",
        "visualization": {
            "type": "table",
            "title": "Filtered Data",
            "data": data[:100]  # Limit to 100 rows
        }
    }

def create_generic_visualization(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a generic visualization for query results.
    """
    if "data" not in result or not result["data"]:
        return None
    
    data = result["data"]
    
    # For generic queries, we'll create a simple table visualization
    return {
        "type": "query",
        "visualization": {
            "type": "table",
            "title": "Query Results",
            "data": data[:100]  # Limit to 100 rows
        }
    }
