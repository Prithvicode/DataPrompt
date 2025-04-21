import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Union
import json
import requests
import re

from services.nlp_service import filter_query

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
    def filter_data(self, prompt: str, df_columns: List[str]) -> Dict[str, Any]:
        """
        Filter data based on the condition and other instructions (e.g., 'top 5').
        Uses filter_query to get the generated code and applies it to the dataframe.
        Returns both the code and the result.
        """
        try:
            print(f"[DEBUG] filter_data called with prompt: '{prompt}'")
            
            # Pre-process the prompt to identify column-specific filtering
            column_filters = {}
            for col in df_columns:
                # Look for patterns like "Column equals/is/= value" or "Column contains value"
                col_patterns = [
                    rf"{col}\s+(?:equals|is|=|==)\s+['\"]*([^'\"]+)['\"]*",
                    rf"{col}\s+(?:contains|has|like)\s+['\"]*([^'\"]+)['\"]*",
                    rf"{col}\s+(?:greater than|>)\s+([0-9.]+)",
                    rf"{col}\s+(?:less than|<)\s+([0-9.]+)"
                ]
                
                for pattern in col_patterns:
                    match = re.search(pattern, prompt, re.IGNORECASE)
                    if match:
                        value = match.group(1).strip()
                        if "contains" in pattern or "has" in pattern or "like" in pattern:
                            # For string contains operations
                            column_filters[col] = f"`{col}`.str.contains('{value}', case=False)"
                        elif "greater" in pattern or ">" in pattern:
                            # For numeric greater than
                            column_filters[col] = f"`{col}` > {value}"
                        elif "less" in pattern or "<" in pattern:
                            # For numeric less than
                            column_filters[col] = f"`{col}` < {value}"
                        else:
                            # For equality
                            try:
                                # Try to convert to number if it looks like one
                                float_val = float(value)
                                column_filters[col] = f"`{col}` == {value}"
                            except ValueError:
                                # It's a string
                                column_filters[col] = f"`{col}` == '{value}'"
                        break
            
            # If we found explicit column filters, use them directly
            if column_filters:
                print(f"[DEBUG] Found explicit column filters: {column_filters}")
                filter_condition = " and ".join(column_filters.values())
                extra_instructions = "none"
                
                # Check for top N in the prompt
                top_match = re.search(r"top\s+(\d+)", prompt.lower())
                if top_match:
                    n = int(top_match.group(1))
                    extra_instructions = f"top {n}"
                    
                    # Look for sort column
                    for col in df_columns:
                        if f"by {col}" in prompt.lower() or f"sort {col}" in prompt.lower():
                            extra_instructions += f" sort by {col}"
                            break
            else:
                # Special case handling for common queries
                if "top" in prompt.lower() and any(col.lower() in prompt.lower() for col in ["revenue", "profit", "sales"]):
                    print("[DEBUG] Detected 'top N' query for a specific column")
                    
                    # Extract the number after "top"
                    try:
                        top_num = int(''.join(c for c in prompt.lower().split("top")[1].strip().split()[0] if c.isdigit()))
                        print(f"[DEBUG] Extracted top {top_num} from prompt")
                    except (ValueError, IndexError):
                        print("[DEBUG] Could not extract number after 'top', using default 5")
                        top_num = 5
                    
                    # Determine which column to sort by
                    sort_column = None
                    for col in ["Revenue", "Profit", "Sales", "UnitsSold"]:
                        if col.lower() in prompt.lower() and col in df_columns:
                            sort_column = col
                            break
                    
                    if not sort_column and "Revenue" in df_columns:
                        sort_column = "Revenue"  # Default to Revenue if available
                    elif not sort_column and "Profit" in df_columns:
                        sort_column = "Profit"   # Or Profit if Revenue is not available
                    
                    if sort_column:
                        print(f"[DEBUG] Using direct sorting approach for top {top_num} by {sort_column}")
                        # Sort by the column in descending order and take top N
                        filtered_df = self.df.sort_values(by=sort_column, ascending=False).head(top_num)
                        
                        return {
                            "type": "filter",
                            "row_count": len(filtered_df),
                            "filter_condition": f"Sorted by {sort_column} (descending)",
                            "extra_instructions": f"top {top_num}",
                            "data": filtered_df.to_dict(orient='records')
                        }
                
                # Get the filtering code from the NLP service
                filter_condition, extra_instructions = filter_query(prompt, df_columns)
                
            print(f"[DEBUG] Using filter_condition: '{filter_condition}'")
            print(f"[DEBUG] Using extra_instructions: '{extra_instructions}'")

            if not filter_condition:
                print("[DEBUG] No filter condition generated")
                
                # Special case for "top N" queries when no filter condition was generated
                if "top" in prompt.lower() or "top" in extra_instructions.lower():
                    # Extract the number after "top" from either prompt or extra_instructions
                    try:
                        if "top" in prompt.lower():
                            top_text = prompt.lower().split("top")[1].strip()
                        else:
                            top_text = extra_instructions.lower().split("top")[1].strip()
                        
                        top_num = int(''.join(c for c in top_text.split()[0] if c.isdigit()))
                        print(f"[DEBUG] Extracted top {top_num}")
                    except (ValueError, IndexError):
                        print("[DEBUG] Could not extract number after 'top', using default 5")
                        top_num = 5
                    
                    # Determine which column to sort by
                    sort_column = None
                    for col in ["Revenue", "Profit", "Sales", "UnitsSold"]:
                        if col in df_columns and (col.lower() in prompt.lower() or col.lower() in extra_instructions.lower()):
                            sort_column = col
                            break
                    
                    if not sort_column and "Revenue" in df_columns:
                        sort_column = "Revenue"  # Default to Revenue if available
                    
                    if sort_column:
                        print(f"[DEBUG] Using fallback sorting approach for top {top_num} by {sort_column}")
                        # Sort by the column in descending order and take top N
                        filtered_df = self.df.sort_values(by=sort_column, ascending=False).head(top_num)
                        
                        return {
                            "type": "filter",
                            "row_count": len(filtered_df),
                            "filter_condition": f"Sorted by {sort_column} (descending)",
                            "extra_instructions": f"top {top_num}",
                            "data": filtered_df.to_dict(orient='records')
                        }
                
                # Try to extract column-value pairs from the prompt
                extracted_filters = []
                for col in df_columns:
                    # Look for patterns like "Column: value" or "Column = value"
                    col_pattern = rf"(?:^|\s)({col})(?:\s*[:=]\s*|\s+is\s+)['\"]*([^'\"]+)['\"]*"
                    matches = re.finditer(col_pattern, prompt, re.IGNORECASE)
                    
                    for match in matches:
                        col_name = match.group(1)
                        value = match.group(2).strip()
                        
                        # Try to determine if value is numeric or string
                        try:
                            float(value)
                            extracted_filters.append(f"`{col_name}` == {value}")
                        except ValueError:
                            extracted_filters.append(f"`{col_name}` == '{value}'")
                
                if extracted_filters:
                    filter_condition = " and ".join(extracted_filters)
                    print(f"[DEBUG] Extracted filter condition: {filter_condition}")
                else:
                    return {
                        "type": "error",
                        "message": "No filter condition could be generated from the prompt."
                    }

            # Apply the filter condition to the dataframe using query
            try:
                print(f"[DEBUG] Attempting to apply filter: {filter_condition}")
                filtered_df = self.df.query(filter_condition)
                print(f"[DEBUG] Filter applied successfully. Result shape: {filtered_df.shape}")
            except Exception as query_error:
                print(f"[ERROR] Failed to apply filter: {str(query_error)}")
                # Try to fix common issues with the filter condition
                fixed_condition = filter_condition
                
                # Fix column names with spaces by adding backticks
                for col in df_columns:
                    if ' ' in col and f'`{col}`' not in fixed_condition and col in fixed_condition:
                        fixed_condition = fixed_condition.replace(col, f'`{col}`')
                
                # Fix string comparisons (ensure consistent quote usage)
                fixed_condition = re.sub(r'([a-zA-Z_`]+)\s*==\s*([^\'"][a-zA-Z][^\'"\d]*[^\'"])', r'\1 == "\2"', fixed_condition)
                
                try:
                    print(f"[DEBUG] Attempting with fixed condition: {fixed_condition}")
                    filtered_df = self.df.query(fixed_condition)
                    print(f"[DEBUG] Fixed filter applied successfully. Result shape: {filtered_df.shape}")
                except Exception as fixed_error:
                    print(f"[ERROR] Fixed filter also failed: {str(fixed_error)}")
                    # Last resort: if the query is about top N, just sort and return top N
                    if "top" in extra_instructions.lower():
                        try:
                            top_match = re.search(r"top\s+(\d+)", extra_instructions.lower())
                            if top_match:
                                n = int(top_match.group(1))
                                print(f"[DEBUG] Falling back to top {n} approach")
                                
                                # Try to find a column to sort by
                                sort_column = None
                                sort_match = re.search(r"sort\s+by\s+(.+?)(?:\s|$)", extra_instructions.lower())
                                if sort_match:
                                    sort_column = sort_match.group(1).strip()
                                
                                # If no sort column specified, try to infer from the prompt
                                if not sort_column:
                                    for col in ["Revenue", "Profit", "Sales", "UnitsSold"]:
                                        if col in df_columns and col.lower() in prompt.lower():
                                            sort_column = col
                                            break
                                
                                # Default to Revenue if available
                                if not sort_column and "Revenue" in df_columns:
                                    sort_column = "Revenue"
                                
                                if sort_column and sort_column in df_columns:
                                    filtered_df = self.df.sort_values(by=sort_column, ascending=False).head(n)
                                    return {
                                        "type": "filter",
                                        "row_count": len(filtered_df),
                                        "filter_condition": f"Sorted by {sort_column} (descending)",
                                        "extra_instructions": f"top {n}",
                                        "data": filtered_df.to_dict(orient='records')
                                    }
                        except Exception as fallback_error:
                            print(f"[ERROR] Fallback approach also failed: {str(fallback_error)}")
                    
                    # If all else fails, return an error
                    return {
                        "type": "error",
                        "message": f"Error applying filter condition: {str(fixed_error)}"
                    }

            # Apply additional instructions like sorting and limiting
            if extra_instructions and extra_instructions.lower() != "none":
                print(f"[DEBUG] Processing extra instructions: {extra_instructions}")
                
                # Handle "top N" instruction
                top_match = re.search(r"top\s+(\d+)", extra_instructions.lower())
                if top_match:
                    n = int(top_match.group(1))
                    print(f"[DEBUG] Applying top {n} limit")
                    
                    # Check if we need to sort before taking top N
                    sort_match = re.search(r"sort\s+by\s+(.+?)(?:\s|$)", extra_instructions.lower())
                    if sort_match:
                        sort_column = sort_match.group(1).strip()
                        # Check if the sort column exists
                        if sort_column in df_columns:
                            print(f"[DEBUG] Sorting by column: {sort_column}")
                            filtered_df = filtered_df.sort_values(by=sort_column, ascending=False).head(n)
                        else:
                            print(f"[WARNING] Sort column '{sort_column}' not found in dataframe")
                            filtered_df = filtered_df.head(n)
                    else:
                        # If no sort column specified but we're looking for top N revenue/profit
                        for col in ["Revenue", "Profit"]:
                            if col in df_columns and col.lower() in prompt.lower():
                                print(f"[DEBUG] Implicitly sorting by {col} for top {n}")
                                filtered_df = filtered_df.sort_values(by=col, ascending=False).head(n)
                                break
                        else:
                            # No specific column to sort by
                            filtered_df = filtered_df.head(n)
                else:
                    # Handle "sort by" instruction without top N
                    sort_match = re.search(r"sort\s+by\s+(.+?)(?:\s|$)", extra_instructions.lower())
                    if sort_match:
                        sort_column = sort_match.group(1).strip()
                        # Check if the sort column exists
                        if sort_column in df_columns:
                            print(f"[DEBUG] Sorting by column: {sort_column}")
                            filtered_df = filtered_df.sort_values(by=sort_column, ascending=False)
                        else:
                            print(f"[WARNING] Sort column '{sort_column}' not found in dataframe")

            # Return the filtered and processed DataFrame
            print(f"[DEBUG] Final filtered df shape: {filtered_df.shape}")
            
            return {
                "type": "filter",
                "row_count": len(filtered_df),
                "filter_condition": filter_condition,
                "extra_instructions": extra_instructions,
                "data": filtered_df.head(100).to_dict(orient='records')  # Limit to 100 rows
            }

        except Exception as e:
            print(f"[ERROR] Error in filter_data: {str(e)}")
            import traceback
            print(f"[ERROR] Traceback: {traceback.format_exc()}")
            return {
                "type": "error",
                "message": f"Error filtering data: {str(e)}"
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
    
    