import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Union
import json
import requests
import re

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "llama3.2"

class DataAnalyzer:
    def __init__(self, df: pd.DataFrame):
        self.df = df

        # Identify numeric, categorical, and date columns
        self.numeric_columns = df.select_dtypes(include=["number"]).columns.tolist()
        self.categorical_columns = df.select_dtypes(include=["object", "category"]).columns.tolist()
        self.date_columns = df.select_dtypes(include=["datetime", "datetime64"]).columns.tolist()

        # Optionally, try parsing additional columns to datetime if not already
        for col in df.columns:
            if col not in self.date_columns:
                try:
                    parsed_col = pd.to_datetime(df[col])
                    if parsed_col.notnull().sum() > 0:  # has valid datetime entries
                        self.date_columns.append(col)
                except Exception:
                    continue

    
    def get_column_metadata(self) -> str:
        """
        Generate a textual summary of column names and types for LLM.
        """
        metadata = []
        for col in self.df.columns:
            dtype = self.df[col].dtype
            sample_values = self.df[col].dropna().unique()[:3].tolist()
            metadata.append(f"- {col} ({dtype}): sample values {sample_values}")
        return "\n".join(metadata)

    # def _detect_column_types(self):
    #     """
    #     Detect and categorize columns by their data types.
    #     """
    #     self.numeric_columns = self.df.select_dtypes(include=['number']).columns.tolist()
    #     self.categorical_columns = self.df.select_dtypes(include=['object', 'category']).columns.tolist()
        
    #     # Detect date columns
    #     self.date_columns = []
    #     for col in self.df.columns:
    #         if self.df[col].dtype == 'object':
    #             parsed = pd.to_datetime(self.df[col], errors='coerce')
    #             # If at least 80% of values were successfully parsed, consider it a date column
    #             if parsed.notna().mean() > 0.8:
    #                 self.date_columns.append(col)

    
    def generate_summary(self) -> Dict[str, Any]:
        """
        Generate a structured summary of the dataset.
        """
        df = self.df
        summary = {
            "dataset_info": {
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": df.columns.tolist(),
                "numeric_columns": self.numeric_columns,
                "categorical_columns": self.categorical_columns,
                "date_columns": self.date_columns,
                "missing_values": df.isnull().sum().to_dict()
            }
        }

        # Numeric statistics
        if self.numeric_columns:
            summary["numeric_stats"] = df[self.numeric_columns].describe().to_dict()

        # Categorical statistics
        if self.categorical_columns:
            summary["categorical_stats"] = {
                col: {
                    "unique_values": df[col].nunique(),
                    "top_values": df[col].value_counts().head(10).to_dict()
                }
                for col in self.categorical_columns
            }

        # Date statistics
        if self.date_columns:
            date_stats = {}
            for col in self.date_columns:
                try:
                    date_series = pd.to_datetime(df[col])
                    date_stats[col] = {
                        "min_date": date_series.min().isoformat(),
                        "max_date": date_series.max().isoformat(),
                        "range_days": (date_series.max() - date_series.min()).days
                    }
                except Exception as e:
                    date_stats[col] = {"error": str(e)}
            summary["date_stats"] = date_stats

        return {
            "type": "summary",
            "data": summary
        }

    def execute_query(self, query: str, chat_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        try:
            # Step 1: Prepare metadata
            column_info = self.get_column_metadata()
            system_prompt = "You are a pandas expert. Given a user query and dataframe columns, return pandas code to fulfill the query."

            user_prompt = f"""
    The user asked: "{query}"
    Here are the columns in the dataset:
    {column_info}

    Write only the pandas code to answer the question. Do not explain. Assume the DataFrame is called df.
    """

            llama_payload = {
                "model": MODEL_NAME,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            }

            # Step 2: Ask LLaMA for pandas code
            response = requests.post(OLLAMA_URL, json=llama_payload)
            response.raise_for_status()
            code_block = response.json().get("message", {}).get("content", "").strip()

            # Extract code from triple-backtick block if needed
            match = re.search(r"```(?:python)?\s*(.*?)```", code_block, re.DOTALL)
            code_str = match.group(1) if match else code_block

            # Step 3: Execute the code
            local_vars = {"df": self.df.copy()}
            exec(code_str, {}, local_vars)

            # Try to extract the resulting variable (assuming last line is a result)
            result_var = list(local_vars.values())[-1]
            if isinstance(result_var, pd.DataFrame):
                data = result_var.to_dict(orient='records')
            elif isinstance(result_var, (pd.Series, list)):
                data = str(result_var)
            else:
                data = str(result_var)

            return {
                "type": "query",
                "query": query,
                "pandas_code": code_str,
                "data": data
            }

        except Exception as e:
            return {
                "type": "error",
                "message": f"Error executing query: {str(e)}"
            }


    # def analyze_trend(self, time_column: Optional[str] = None, value_column: Optional[str] = None) -> Dict[str, Any]:
    #     """
    #     Analyze trends over time.
    #     """
    #     # If time_column not provided, try to detect it
    #     if not time_column:
    #         if self.date_columns:
    #             time_column = self.date_columns[0]
    #         else:
    #             # Try to find a column with 'date' or 'time' in the name
    #             for col in self.df.columns:
    #                 if any(term in col.lower() for term in ['date', 'time', 'year', 'month', 'day']):
    #                     time_column = col
    #                     break
        
    #     # If value_column not provided, use the first numeric column
    #     if not value_column and self.numeric_columns:
    #         value_column = self.numeric_columns[0]
        
    #     if not time_column or not value_column:
    #         return {
    #             "type": "error",
    #             "message": "Could not identify appropriate time and value columns for trend analysis."
    #         }
        
    #     try:
    #         # Convert time column to datetime if it's not already
    #         if time_column not in self.date_columns:
    #             self.df[time_column] = pd.to_datetime(self.df[time_column], errors='coerce')
            
    #         # Group by time and aggregate the value column
    #         # First, determine the appropriate time frequency
    #         time_series = pd.to_datetime(self.df[time_column])
    #         date_range = time_series.max() - time_series.min()
            
    #         if date_range.days > 365 * 2:  # More than 2 years
    #             freq = 'M'  # Monthly
    #             format_str = '%Y-%m'
    #         elif date_range.days > 90:  # More than 3 months
    #             freq = 'W'  # Weekly
    #             format_str = '%Y-%m-%d'
    #         else:
    #             freq = 'D'  # Daily
    #             format_str = '%Y-%m-%d'
            
    #         # Group by the time frequency
    #         grouped = self.df.groupby(pd.Grouper(key=time_column, freq=freq))
            
    #         # Aggregate the value column
    #         trend_data = grouped[value_column].agg(['sum', 'mean', 'count']).reset_index()
            
    #         # Format the date column
    #         trend_data[time_column] = trend_data[time_column].dt.strftime(format_str)
            
    #         # Calculate period-over-period growth if possible
    #         if len(trend_data) > 1:
    #             trend_data['growth'] = trend_data['sum'].pct_change() * 100
            
    #         return {
    #             "type": "trend",
    #             "time_column": time_column,
    #             "value_column": value_column,
    #             "frequency": freq,
    #             "data": trend_data.to_dict(orient='records')
    #         }
    #     except Exception as e:
    #         return {
    #             "type": "error",
    #             "message": f"Error analyzing trend: {str(e)}"
    #         }
    
    # def aggregate_data(
    #     self, 
    #     group_by_columns: List[str], 
    #     agg_column: Optional[str] = None, 
    #     agg_function: str = "sum"
    # ) -> Dict[str, Any]:
    #     """
    #     Aggregate data by grouping columns.
    #     """
    #     # If group_by_columns not provided or invalid, try to use categorical columns
    #     valid_group_by = []
    #     for col in group_by_columns:
    #         if col in self.df.columns:
    #             valid_group_by.append(col)
        
    #     if not valid_group_by:
    #         if self.categorical_columns:
    #             valid_group_by = [self.categorical_columns[0]]
    #         else:
    #             return {
    #                 "type": "error",
    #                 "message": "Could not identify appropriate columns for grouping."
    #             }
        
    #     # If agg_column not provided, use the first numeric column
    #     if not agg_column and self.numeric_columns:
    #         agg_column = self.numeric_columns[0]
        
    #     if not agg_column:
    #         return {
    #             "type": "error",
    #             "message": "Could not identify appropriate column for aggregation."
    #         }
        
    #     try:
    #         # Group by the specified columns
    #         grouped = self.df.groupby(valid_group_by)
            
    #         # Apply the aggregation function
    #         if agg_function == "sum":
    #             agg_data = grouped[agg_column].sum().reset_index()
    #         elif agg_function == "mean":
    #             agg_data = grouped[agg_column].mean().reset_index()
    #         elif agg_function == "count":
    #             agg_data = grouped[agg_column].count().reset_index()
    #         elif agg_function == "min":
    #             agg_data = grouped[agg_column].min().reset_index()
    #         elif agg_function == "max":
    #             agg_data = grouped[agg_column].max().reset_index()
    #         else:
    #             # Default to sum
    #             agg_data = grouped[agg_column].sum().reset_index()
            
    #         return {
    #             "type": "aggregation",
    #             "group_by_columns": valid_group_by,
    #             "agg_column": agg_column,
    #             "agg_function": agg_function,
    #             "data": agg_data.to_dict(orient='records')
    #         }
    #     except Exception as e:
    #         return {
    #             "type": "error",
    #             "message": f"Error aggregating data: {str(e)}"
    #         }
    
    # def filter_data(self, filter_conditions: List[Dict[str, Any]]) -> Dict[str, Any]:
    #     """
    #     Filter data based on conditions.
    #     """
    #     if not filter_conditions:
    #         return {
    #             "type": "error",
    #             "message": "No filter conditions provided."
    #         }
        
    #     try:
    #         filtered_df = self.df.copy()
            
    #         for condition in filter_conditions:
    #             column = condition.get("column")
    #             operator = condition.get("operator", "==")
    #             value = condition.get("value")
                
    #             if not column or column not in filtered_df.columns or value is None:
    #                 continue
                
    #             if operator == "==":
    #                 filtered_df = filtered_df[filtered_df[column] == value]
    #             elif operator == "!=":
    #                 filtered_df = filtered_df[filtered_df[column] != value]
    #             elif operator == ">":
    #                 filtered_df = filtered_df[filtered_df[column] > value]
    #             elif operator == ">=":
    #                 filtered_df = filtered_df[filtered_df[column] >= value]
    #             elif operator == "<":
    #                 filtered_df = filtered_df[filtered_df[column] < value]
    #             elif operator == "<=":
    #                 filtered_df = filtered_df[filtered_df[column] <= value]
    #             elif operator == "in":
    #                 if isinstance(value, list):
    #                     filtered_df = filtered_df[filtered_df[column].isin(value)]
    #             elif operator == "contains":
    #                 filtered_df = filtered_df[filtered_df[column].astype(str).str.contains(str(value), na=False)]
            
    #         return {
    #             "type": "filter",
    #             "conditions": filter_conditions,
    #             "row_count": len(filtered_df),
    #             "data": filtered_df.head(100).to_dict(orient='records')  # Limit to 100 rows
    #         }
    #     except Exception as e:
    #         return {
    #             "type": "error",
    #             "message": f"Error filtering data: {str(e)}"
    #         }
    
    # def execute_query(self, query: str) -> Dict[str, Any]:
    #     """
    #     Execute a general query on the data.
    #     This is a fallback method when the intent cannot be classified.
    #     """
    #     try:
    #         # For now, just return a sample of the data
    #         return {
    #             "type": "query",
    #             "query": query,
    #             "data": self.df.head(50).to_dict(orient='records')
    #         }
    #     except Exception as e:
    #         return {
    #             "type": "error",
    #             "message": f"Error executing query: {str(e)}"
    #         }
