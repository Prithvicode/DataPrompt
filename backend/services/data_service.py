import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Union
import json
import requests
import re
import traceback
from datetime import datetime, timedelta

from services.nlp_service import generate_panda_code_from_prompt
from services.prepare_data_for_prediction import predict_sales, forecast_weekly_sales, forecast_monthly_sales

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "llama3.2"

class DataAnalyzer:
    def __init__(self, df: pd.DataFrame):
        print("[DEBUG] Initializing DataAnalyzer")
        self.df = df

        # Identify numeric, categorical, and date columns
        self.numeric_columns = df.select_dtypes(include=["number"]).columns.tolist()
        print(f"[DEBUG] Numeric columns: {self.numeric_columns}")
        
        self.categorical_columns = df.select_dtypes(include=["object", "category"]).columns.tolist()
        print(f"[DEBUG] Categorical columns: {self.categorical_columns}")
        
        self.date_columns = df.select_dtypes(include=["datetime", "datetime64"]).columns.tolist()
        print(f"[DEBUG] Initial date columns: {self.date_columns}")

        # Optionally, try parsing additional columns to datetime if not already
        for col in df.columns:
            if col not in self.date_columns:
                try:
                    print(f"[DEBUG] Attempting to parse {col} as datetime")
                    parsed_col = pd.to_datetime(df[col])
                    if parsed_col.notnull().sum() > 0:  # has valid datetime entries
                        self.date_columns.append(col)
                        print(f"[DEBUG] Successfully parsed {col} as datetime")
                except Exception as e:
                    print(f"[DEBUG] Failed to parse {col} as datetime: {str(e)}")
                    continue
        
        print(f"[DEBUG] Final date columns: {self.date_columns}")

    
    def get_column_metadata(self) -> str:
        """
        Generate a textual summary of column names and types for LLM.
        """
        print("[DEBUG] Generating column metadata")
        metadata = []
        for col in self.df.columns:
            dtype = self.df[col].dtype
            sample_values = self.df[col].dropna().unique()[:3].tolist()
            metadata.append(f"- {col} ({dtype}): sample values {sample_values}")
        
        result = "\n".join(metadata)
        print(f"[DEBUG] Column metadata generated with {len(metadata)} columns")
        return result

    def generate_summary(self) -> Dict[str, Any]:
        """
        Generate a structured summary of the dataset.
        """
        print("[DEBUG] Generating dataset summary")
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
            print(f"[DEBUG] Calculating statistics for {len(self.numeric_columns)} numeric columns")
            summary["numeric_stats"] = df[self.numeric_columns].describe().to_dict()

        # Categorical statistics
        if self.categorical_columns:
            print(f"[DEBUG] Calculating statistics for {len(self.categorical_columns)} categorical columns")
            summary["categorical_stats"] = {
                col: {
                    "unique_values": df[col].nunique(),
                    "top_values": df[col].value_counts().head(10).to_dict()
                }
                for col in self.categorical_columns
            }

        # Date statistics
        if self.date_columns:
            print(f"[DEBUG] Calculating statistics for {len(self.date_columns)} date columns")
            date_stats = {}
            for col in self.date_columns:
                try:
                    date_series = pd.to_datetime(df[col])
                    date_stats[col] = {
                        "min_date": date_series.min().isoformat(),
                        "max_date": date_series.max().isoformat(),
                        "range_days": (date_series.max() - date_series.min()).days
                    }
                    print(f"[DEBUG] Date stats for {col}: range = {date_stats[col]['range_days']} days")
                except Exception as e:
                    print(f"[ERROR] Error calculating date stats for {col}: {str(e)}")
                    date_stats[col] = {"error": str(e)}
            summary["date_stats"] = date_stats

        print("[DEBUG] Summary generation complete")
        return {
            "type": "summary",
            "data": summary
        }
    def filter_data(self, prompt: str, df_columns: List[str]):
        """
        Filter the DataFrame based on the user's query and return the resulting DataFrame.
        Returns a structured dictionary with type and data fields.
        """
        # Add explicit instructions for the LLM to generate better filtering code
        augmented_prompt = f"""
        Create pandas code to filter the following DataFrame with columns: {df_columns}.
        Based on this request: "{prompt}"
        
        IMPORTANT GUIDELINES:
        1. Make sure your code assigns the filtered result back to 'df'
        2. For selecting top N rows by a value, use: df = df.nlargest(N, 'column_name')
        3. For filtering by condition, use: df = df[df['column_name'] > value]
        4. Always check if the columns you're using exist in the dataframe
        5. Return ONLY executable pandas code without explanations
        """
        
        code = generate_panda_code_from_prompt(augmented_prompt, df_columns)
        print("Generated code from LLM:", code)
        
        # Preprocessing step to validate and fix common errors in the generated code
        try:
            # Check for common mistakes in the generated code and attempt to fix them
            if 'nlargest' in code and '[df' in code:
                # Fix the syntax for nlargest improperly used inside indexing brackets
                match = re.search(r'df\s*=\s*df\s*\[\s*df\s*\[\s*[\'"](\w+)[\'"]\s*\]\s*\.nlargest\s*\(\s*(\d+)\s*\)\s*\]', code)
                if match:
                    column, n = match.groups()
                    code = f"df = df.nlargest({n}, '{column}')"
                    print(f"[DEBUG] Fixed nlargest syntax: {code}")
            
            # Ensure all column references are valid
            for col in re.findall(r"df\['([^']+)'\]", code):
                if col not in df_columns:
                    raise ValueError(f"Generated code references non-existent column: {col}")
        
        except Exception as e:
            # If we can't fix the code, log the error and generate a safer alternative
            print(f"[DEBUG] Error preprocessing code: {str(e)}")
            # Fallback to a safer template based on the prompt analysis
            if 'largest' in prompt.lower() or 'highest' in prompt.lower() or 'top' in prompt.lower():
                # Extract possible numeric values and column names from the prompt
                numbers = re.findall(r'\b(\d+)\b', prompt)
                n = int(numbers[0]) if numbers else 5  # Default to top 5 if no number specified
                
                # Try to identify the column to sort by from the prompt
                possible_columns = [col for col in df_columns if col.lower() in prompt.lower()]
                if not possible_columns and 'revenue' in prompt.lower():
                    possible_columns = [col for col in df_columns if 'revenue' in col.lower() or 'sales' in col.lower() or 'amount' in col.lower()]
                
                sort_column = possible_columns[0] if possible_columns else df_columns[0]
                code = f"df = df.nlargest({n}, '{sort_column}')"
                print(f"[DEBUG] Fallback to safe template: {code}")
        
        try:
            # Execute the code with safety measures
            local_vars = {'df': self.df.copy()}
            
            # Add a timeout mechanism to prevent infinite loops (if supported in your environment)
            exec(code, {}, local_vars)
            
            # Check if the result is a valid DataFrame
            result_df = local_vars.get('df')
            if not isinstance(result_df, pd.DataFrame):
                print(f"[DEBUG] Result is not a DataFrame, type: {type(result_df)}")
                return {
                    "type": "error",
                    "data": {
                        "message": f"Filter operation produced an invalid result of type {type(result_df).__name__}",
                        "original_code": code
                    }
                }
            
            # Validate the result isn't empty unless that was explicitly intended
            if result_df.empty and not self.df.empty:
                print("[DEBUG] Filtering produced an empty DataFrame, returning error")
                return {
                    "type": "error",
                    "data": {
                        "message": "Filter operation produced an empty result. Please refine your filter criteria.",
                        "original_code": code
                    }
                }
                
            print(f"[DEBUG] Filtering successful - original size: {len(self.df)}, filtered size: {len(result_df)}")
            return {
                "type": "filter",
                "data": result_df
            }
                
        except Exception as e:
            error_message = str(e)
            print(f"Error executing generated code: {error_message}")
            traceback.print_exc()
            
            # Try one more time with a very simple approach if we're looking for top values
            if 'largest' in prompt.lower() or 'highest' in prompt.lower() or 'top' in prompt.lower():
                try:
                    # Find numeric columns that might be relevant
                    numeric_cols = [col for col in df_columns if col in self.df.select_dtypes(include=['number']).columns]
                    if numeric_cols:
                        # Look for relevant columns based on prompt keywords
                        possible_cols = [col for col in numeric_cols if col.lower() in prompt.lower()]
                        if not possible_cols:
                            possible_cols = [col for col in numeric_cols if any(kw in col.lower() for kw in ['revenue', 'sales', 'price', 'amount', 'profit'])]
                        
                        sort_col = possible_cols[0] if possible_cols else numeric_cols[0]
                        n = 5  # Default to top 5
                        numbers = re.findall(r'\b(\d+)\b', prompt)
                        if numbers:
                            n = int(numbers[0])
                        
                        result_df = self.df.nlargest(n, sort_col)
                        print(f"[DEBUG] Recovery filter applied: top {n} rows by {sort_col}")
                        return {
                            "type": "filter_result",
                            "data": result_df,
                            "note": f"Using fallback filter: top {n} results by {sort_col}"
                        }
                except Exception as recovery_error:
                    print(f"[DEBUG] Recovery filtering failed: {str(recovery_error)}")
            
            # Return error in the requested format
            return {
                "type": "error",
                "data": {
                    "message": f"Error executing filter: {error_message}",
                    "original_code": code
                }
            }

        """
        Filter the DataFrame based on the user's query and return the resulting DataFrame.
        """
        # Add explicit instructions for the LLM to generate better filtering code
        augmented_prompt = f"""
        Create pandas code to filter the following DataFrame with columns: {df_columns}.
        Based on this request: "{prompt}"
        
        IMPORTANT GUIDELINES:
        1. Make sure your code assigns the filtered result back to 'df'
        2. For selecting top N rows by a value, use: df = df.nlargest(N, 'column_name')
        3. For filtering by condition, use: df = df[df['column_name'] > value]
        4. Always check if the columns you're using exist in the dataframe
        5. Return ONLY executable pandas code without explanations
        """
        
        code = generate_panda_code_from_prompt(augmented_prompt, df_columns)
        print("Generated code from LLM:", code)
        
        # Preprocessing step to validate and fix common errors in the generated code
        try:
            # Check for common mistakes in the generated code and attempt to fix them
            if 'nlargest' in code and '[df' in code:
                # Fix the syntax for nlargest improperly used inside indexing brackets
                match = re.search(r'df\s*=\s*df\s*\[\s*df\s*\[\s*[\'"](\w+)[\'"]\s*\]\s*\.nlargest\s*\(\s*(\d+)\s*\)\s*\]', code)
                if match:
                    column, n = match.groups()
                    code = f"df = df.nlargest({n}, '{column}')"
                    print(f"[DEBUG] Fixed nlargest syntax: {code}")
            
            # Ensure all column references are valid
            for col in re.findall(r"df\['([^']+)'\]", code):
                if col not in df_columns:
                    raise ValueError(f"Generated code references non-existent column: {col}")
        
        except Exception as e:
            # If we can't fix the code, log the error and generate a safer alternative
            print(f"[DEBUG] Error preprocessing code: {str(e)}")
            # Fallback to a safer template based on the prompt analysis
            if 'largest' in prompt.lower() or 'highest' in prompt.lower() or 'top' in prompt.lower():
                # Extract possible numeric values and column names from the prompt
                numbers = re.findall(r'\b(\d+)\b', prompt)
                n = int(numbers[0]) if numbers else 5  # Default to top 5 if no number specified
                
                # Try to identify the column to sort by from the prompt
                possible_columns = [col for col in df_columns if col.lower() in prompt.lower()]
                if not possible_columns and 'revenue' in prompt.lower():
                    possible_columns = [col for col in df_columns if 'revenue' in col.lower() or 'sales' in col.lower() or 'amount' in col.lower()]
                
                sort_column = possible_columns[0] if possible_columns else df_columns[0]
                code = f"df = df.nlargest({n}, '{sort_column}')"
                print(f"[DEBUG] Fallback to safe template: {code}")
        
        try:
            # Execute the code with safety measures
            local_vars = {'df': self.df.copy()}
            
            # Add a timeout mechanism to prevent infinite loops (if supported in your environment)
            exec(code, {}, local_vars)
            
            # Check if the result is a valid DataFrame
            result_df = local_vars.get('df')
            if not isinstance(result_df, pd.DataFrame):
                print(f"[DEBUG] Result is not a DataFrame, type: {type(result_df)}")
                return self.df
            
            # Validate the result isn't empty unless that was explicitly intended
            if result_df.empty and not self.df.empty:
                print("[DEBUG] Filtering produced an empty DataFrame, returning original")
                return self.df
                
            print(f"[DEBUG] Filtering successful - original size: {len(self.df)}, filtered size: {len(result_df)}")
            return result_df
                
        except Exception as e:
            print(f"Error executing generated code: {str(e)}")
            traceback.print_exc()
            
            # Try one more time with a very simple approach if we're looking for top values
            if 'largest' in prompt.lower() or 'highest' in prompt.lower() or 'top' in prompt.lower():
                try:
                    # Find numeric columns that might be relevant
                    numeric_cols = [col for col in df_columns if col in self.df.select_dtypes(include=['number']).columns]
                    if numeric_cols:
                        # Look for relevant columns based on prompt keywords
                        possible_cols = [col for col in numeric_cols if col.lower() in prompt.lower()]
                        if not possible_cols:
                            possible_cols = [col for col in numeric_cols if any(kw in col.lower() for kw in ['revenue', 'sales', 'price', 'amount', 'profit'])]
                        
                        sort_col = possible_cols[0] if possible_cols else numeric_cols[0]
                        n = 5  # Default to top 5
                        numbers = re.findall(r'\b(\d+)\b', prompt)
                        if numbers:
                            n = int(numbers[0])
                        
                        result_df = self.df.nlargest(n, sort_col)
                        print(f"[DEBUG] Recovery filter applied: top {n} rows by {sort_col}")
                        return result_df
                except Exception as recovery_error:
                    print(f"[DEBUG] Recovery filtering failed: {str(recovery_error)}")
            
            return self.df  # Fall back to the original DataFrame if all else fails
    def execute_query(self, query: str, chat_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Execute a custom query using LLM to generate pandas code.
        """
        try:
            print(f"[DEBUG] Executing query: {query}")
            # Step 1: Prepare metadata
            column_info = self.get_column_metadata()
            system_prompt = "You are a pandas expert. Given a user query and dataframe columns, return pandas code to fulfill the query."

            user_prompt = f"""
    The user asked: "{query}"
    Here are the columns in the dataset:
    {column_info}

    Write only the pandas code to answer the question. Do not explain. Assume the DataFrame is called df.
    """

            print("[DEBUG] Sending request to Ollama for pandas code generation")
            llama_payload = {
                "model": MODEL_NAME,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ]
            }

            # Step 2: Ask LLaMA for pandas code
            response = requests.post(OLLAMA_URL, json=llama_payload)
            print(f"[DEBUG] Response : {response}")
            response.raise_for_status()
            code_block = response.json().get("message", {}).get("content", "").strip()
            print(f"[DEBUG] Received code from Ollama: {code_block[:100]}...")

            # Extract code from triple-backtick block if needed
            match = re.search(r"```(?:python)?\s*(.*?)```", code_block, re.DOTALL)
            code_str = match.group(1) if match else code_block
            print(f"[DEBUG] Extracted code: {code_str[:100]}...")

            # Step 3: Execute the code
            local_vars = {"df": self.df.copy()}
            print("[DEBUG] Executing generated pandas code")
            exec(code_str, {}, local_vars)

            # Try to extract the resulting variable (assuming last line is a result)
            result_var = list(local_vars.values())[-1]
            print(f"[DEBUG] Code execution complete, result type: {type(result_var)}")
            
            if isinstance(result_var, pd.DataFrame):
                data = result_var.head(100).to_dict(orient='records')
                print(f"[DEBUG] Result is DataFrame with {len(result_var)} rows")
            elif isinstance(result_var, (pd.Series, list)):
                data = str(result_var)
                print(f"[DEBUG] Result is Series or list with length {len(result_var)}")
            else:
                data = str(result_var)
                print(f"[DEBUG] Result is {type(result_var)}")

            return {
                "type": "query",
                "query": query,
                "pandas_code": code_str,
                "data": data
            }

        except Exception as e:
            print(f"[ERROR] Error executing query: {str(e)}")
            print(f"[ERROR] Traceback: {traceback.format_exc()}")
            return {
                "type": "error",
                "message": f"Error executing query: {str(e)}"
            }
    
    def analyze_trend(self, prompt: str, **parameters) -> Dict[str, Any]:
        """
        Analyze trends in time series data.
        """
        try:
            print(f"[DEBUG] Analyzing trend with prompt: {prompt}")
            
            # Step 1: Identify the time column and value column
            time_col = None
            value_col = None
            
            # First, try to find a date column
            if self.date_columns:
                time_col = self.date_columns[0]  # Use the first date column by default
                print(f"[DEBUG] Using date column for time: {time_col}")
            
            # Look for time-related keywords in the prompt
            time_keywords = ["time", "date", "month", "year", "day", "week", "period"]
            for col in self.df.columns:
                if any(keyword in col.lower() for keyword in time_keywords):
                    time_col = col
                    print(f"[DEBUG] Found time column from keywords: {time_col}")
                    break
            
            # If still no time column, look for columns with "date" or "time" in the name
            if not time_col:
                for col in self.df.columns:
                    if "date" in col.lower() or "time" in col.lower():
                        time_col = col
                        print(f"[DEBUG] Found time column from name: {time_col}")
                        break
            
            # Look for value column in the prompt
            value_keywords = ["revenue", "sales", "profit", "amount", "value", "price", "cost", "units"]
            for keyword in value_keywords:
                if keyword in prompt.lower():
                    # Find a column that matches this keyword
                    for col in self.numeric_columns:
                        if keyword in col.lower():
                            value_col = col
                            print(f"[DEBUG] Found value column from prompt keyword: {value_col}")
                            break
                    if value_col:
                        break
            
            # If no value column found, use the first numeric column
            if not value_col and self.numeric_columns:
                value_col = self.numeric_columns[0]
                print(f"[DEBUG] Using default value column: {value_col}")
            
            if not time_col or not value_col:
                print("[ERROR] Could not identify time or value column")
                return {
                    "type": "error",
                    "message": "Could not identify time and value columns for trend analysis."
                }
            
            # Step 2: Prepare the data
            print(f"[DEBUG] Preparing trend data with time_col={time_col} and value_col={value_col}")
            
            # Convert time column to datetime if it's not already
            if time_col not in self.date_columns:
                try:
                    self.df[time_col] = pd.to_datetime(self.df[time_col])
                    print(f"[DEBUG] Converted {time_col} to datetime")
                except Exception as e:
                    print(f"[ERROR] Failed to convert {time_col} to datetime: {str(e)}")
                    return {
                        "type": "error",
                        "message": f"Failed to convert {time_col} to datetime: {str(e)}"
                    }
            
            # Determine the appropriate time grouping (day, week, month, year)
            # Look for time period keywords in the prompt
            time_period = "month"  # Default to monthly
            if "daily" in prompt.lower() or "day" in prompt.lower():
                time_period = "day"
            elif "weekly" in prompt.lower() or "week" in prompt.lower():
                time_period = "week"
            elif "yearly" in prompt.lower() or "year" in prompt.lower() or "annual" in prompt.lower():
                time_period = "year"
            
            print(f"[DEBUG] Using time period: {time_period}")
            
            # Group by the time period and calculate the sum of the value column
            if time_period == "day":
                grouped = self.df.groupby(self.df[time_col].dt.date)
            elif time_period == "week":
                grouped = self.df.groupby(pd.Grouper(key=time_col, freq='W'))
            elif time_period == "year":
                grouped = self.df.groupby(self.df[time_col].dt.year)
            else:  # Default to month
                grouped = self.df.groupby(pd.Grouper(key=time_col, freq='M'))
            
            # Calculate aggregates
            agg_data = grouped.agg({value_col: 'sum'}).reset_index()
            print(f"[DEBUG] Aggregated data shape: {agg_data.shape}")
            
            # Format the time column  Aggregated data shape: {agg_data.shape}")
            
            # Format the time column
            if time_period == "day":
                agg_data['period'] = agg_data[time_col].dt.strftime('%Y-%m-%d')
            elif time_period == "week":
                agg_data['period'] = agg_data[time_col].dt.strftime('%Y-%m-%d')
            elif time_period == "year":
                agg_data['period'] = agg_data[time_col].astype(str)
            else:  # month
                agg_data['period'] = agg_data[time_col].dt.strftime('%Y-%m')
            
            print(f"[DEBUG] Formatted time column as 'period'")
            
            # Rename columns for clarity
            agg_data = agg_data.rename(columns={value_col: 'sum'})
            
            # Calculate period-over-period growth
            agg_data['growth'] = agg_data['sum'].pct_change() * 100
            print(f"[DEBUG] Calculated period-over-period growth")
            
            # Prepare the result
            result_data = agg_data.to_dict(orient='records')
            print(f"[DEBUG] Prepared {len(result_data)} records for trend result")
            
            # Create visualization data in the format expected by the frontend
            chart_data = []
            for record in result_data:
                if pd.notna(record.get('sum')):  # Skip NaN values
                    chart_data.append({
                        "month": record.get('period'),
                        "desktop": float(record.get('sum')),
                        "mobile": 0  # Default to 0 for mobile since we're only tracking one metric
                    })
            
            print(f"[DEBUG] Prepared chart data with {len(chart_data)} points")
            
            return {
                "type": "trend",
                "time_column": "period",
                "value_column": value_col,
                "time_period": time_period,
                "data": result_data,
                "chart_data": chart_data
            }
            
        except Exception as e:
            print(f"[ERROR] Error analyzing trend: {str(e)}")
            print(f"[ERROR] Traceback: {traceback.format_exc()}")
            return {
                "type": "error",
                "message": f"Error analyzing trend: {str(e)}"
            }
    
    def aggregate(self, prompt: str, **parameters) -> Dict[str, Any]:
        """
        Aggregate data based on one or more dimensions.
        """
        try:
            print(f"[DEBUG] Aggregating data with prompt: {prompt}")
            
            # Step 1: Identify the group by columns and aggregation column
            group_by_cols = []
            agg_col = None
            agg_func = "sum"  # Default aggregation function
            
            # Look for aggregation keywords in the prompt
            agg_keywords = {
                "sum": ["sum", "total"],
                "avg": ["average", "avg", "mean"],
                "count": ["count", "number"],
                "min": ["min", "minimum", "lowest"],
                "max": ["max", "maximum", "highest"]
            }
            
            # Determine aggregation function from prompt
            for func, keywords in agg_keywords.items():
                if any(keyword in prompt.lower() for keyword in keywords):
                    agg_func = func
                    print(f"[DEBUG] Found aggregation function: {agg_func}")
                    break
            
            # Look for "by" or "group by" in the prompt to identify group by columns
            by_match = re.search(r"(?:group\s+by|by)\s+([a-zA-Z0-9, ]+)", prompt.lower())
            if by_match:
                # Split the matched group by commas or "and"
                group_by_text = by_match.group(1)
                group_by_candidates = re.split(r",|\sand\s", group_by_text)
                
                # Clean up the candidates and match to actual columns
                for candidate in group_by_candidates:
                    candidate = candidate.strip()
                    print(f"[DEBUG] Group by candidate: {candidate}")
                    
                    # Try to match the candidate to a column name
                    for col in self.df.columns:
                        if candidate.lower() in col.lower() or col.lower() in candidate.lower():
                            group_by_cols.append(col)
                            print(f"[DEBUG] Matched group by column: {col}")
                            break
            
            # If no group by columns found, look for categorical columns mentioned in the prompt
            if not group_by_cols:
                for col in self.categorical_columns:
                    if col.lower() in prompt.lower():
                        group_by_cols.append(col)
                        print(f"[DEBUG] Found categorical column in prompt: {col}")
            
            # Look for aggregation column in the prompt
            agg_value_keywords = ["revenue", "sales", "profit", "amount", "value", "price", "cost", "units"]
            for keyword in agg_value_keywords:
                if keyword in prompt.lower():
                    # Find a column that matches this keyword
                    for col in self.numeric_columns:
                        if keyword in col.lower():
                            agg_col = col
                            print(f"[DEBUG] Found aggregation column from keyword: {agg_col}")
                            break
                    if agg_col:
                        break
            
            # If no aggregation column found, use the first numeric column
            if not agg_col and self.numeric_columns:
                agg_col = self.numeric_columns[0]
                print(f"[DEBUG] Using default aggregation column: {agg_col}")
            
            # If still no group by columns, use the first categorical column
            if not group_by_cols and self.categorical_columns:
                group_by_cols.append(self.categorical_columns[0])
                print(f"[DEBUG] Using default group by column: {group_by_cols[0]}")
            
            if not group_by_cols or not agg_col:
                print("[ERROR] Could not identify group by columns or aggregation column")
                return {
                    "type": "error",
                    "message": "Could not identify group by columns or aggregation column for aggregation."
                }
            
            # Step 2: Perform the aggregation
            print(f"[DEBUG] Aggregating {agg_col} by {group_by_cols} using {agg_func}")
            
            # Group by the columns and calculate the aggregation
            grouped = self.df.groupby(group_by_cols)
            
            # Apply the aggregation function
            if agg_func == "sum":
                agg_data = grouped[agg_col].sum().reset_index()
            elif agg_func == "avg":
                agg_data = grouped[agg_col].mean().reset_index()
            elif agg_func == "count":
                agg_data = grouped[agg_col].count().reset_index()
            elif agg_func == "min":
                agg_data = grouped[agg_col].min().reset_index()
            elif agg_func == "max":
                agg_data = grouped[agg_col].max().reset_index()
            else:
                agg_data = grouped[agg_col].sum().reset_index()
            
            print(f"[DEBUG] Aggregation complete, result shape: {agg_data.shape}")
            
            # Sort by the aggregated value in descending order
            agg_data = agg_data.sort_values(by=agg_col, ascending=False)
            
            # Prepare the result
            result_data = agg_data.to_dict(orient='records')
            print(f"[DEBUG] Prepared {len(result_data)} records for aggregation result")
            
            return {
                "type": "aggregation",
                "group_by_columns": group_by_cols,
                "agg_column": agg_col,
                "agg_function": agg_func,
                "data": result_data
            }
            
        except Exception as e:
            print(f"[ERROR] Error aggregating data: {str(e)}")
            print(f"[ERROR] Traceback: {traceback.format_exc()}")
            return {
                "type": "error",
                "message": f"Error aggregating data: {str(e)}"
            }
    
    def forecast(self, prompt: str, **parameters) -> Dict[str, Any]:
        """
        Generate forecasts using the pre-trained model.
        """
        try:
            print(f"[DEBUG] Generating forecast with prompt: {prompt}")
            
            # Step 1: Determine forecast parameters from the prompt
            
            # Determine forecast period (weeks or months)
            period = "month"  # Default to monthly
            if "weekly" in prompt.lower() or "week" in prompt.lower():
                period = "week"
                print("[DEBUG] Using weekly forecast period")
            else:
                print("[DEBUG] Using monthly forecast period")
            
            # Determine number of periods to forecast
            periods = 3  # Default to 3 periods
            period_match = re.search(r"(\d+)\s+(?:weeks|months|periods)", prompt.lower())
            if period_match:
                periods = int(period_match.group(1))
                print(f"[DEBUG] Found {periods} periods to forecast")
            
            # Determine target column (what to forecast)
            target_col = None
            target_keywords = ["revenue", "sales", "profit", "units"]
            for keyword in target_keywords:
                if keyword in prompt.lower():
                    # Find a column that matches this keyword
                    for col in self.numeric_columns:
                        if keyword in col.lower():
                            target_col = col
                            print(f"[DEBUG] Found target column from keyword: {target_col}")
                            break
                    if target_col:
                        break
            
            # If no target column found, use Revenue or the first numeric column
            if not target_col:
                if "Revenue" in self.df.columns:
                    target_col = "Revenue"
                    print(f"[DEBUG] Using default target column: {target_col}")
                elif self.numeric_columns:
                    target_col = self.numeric_columns[0]
                    print(f"[DEBUG] Using default target column: {target_col}")
                else:
                    print("[ERROR] Could not identify target column for forecast")
                    return {
                        "type": "error",
                        "message": "Could not identify target column for forecast."
                    }
            
            # Step 2: Extract product categories, names, regions, and segments if available
            product_categories = []
            product_names = []
            regions = []
            segments = []
            
            # Check if these columns exist in the dataframe
            if "ProductCategory" in self.df.columns:
                product_categories = self.df["ProductCategory"].unique().tolist()
                print(f"[DEBUG] Found {len(product_categories)} product categories")
            
            if "ProductName" in self.df.columns:
                product_names = self.df["ProductName"].unique().tolist()
                print(f"[DEBUG] Found {len(product_names)} product names")
            
            if "Region" in self.df.columns:
                regions = self.df["Region"].unique().tolist()
                print(f"[DEBUG] Found {len(regions)} regions")
            
            if "CustomerSegment" in self.df.columns:
                segments = self.df["CustomerSegment"].unique().tolist()
                print(f"[DEBUG] Found {len(segments)} customer segments")
            
            # If any of these are empty, use defaults
            if not product_categories:
                product_categories = ["Default"]
            if not product_names:
                product_names = ["Default"]
            if not regions:
                regions = ["Default"]
            if not segments:
                segments = ["Default"]
            
            # Step 3: Generate the forecast
            print(f"[DEBUG] Generating {period} forecast for {periods} periods")
            
            # Get current date
            today = datetime.now()
            start_date = today.strftime('%Y-%m-%d')
            
            # Generate forecast
            if period == "week":
                forecast_df = forecast_weekly_sales(
                    start_date=start_date,
                    weeks=periods,
                    product_categories=product_categories,
                    product_names=product_names,
                    regions=regions,
                    segments=segments
                )
                print(f"[DEBUG] Generated weekly forecast with shape: {forecast_df.shape}")
            else:
                forecast_df = forecast_monthly_sales(
                    start_date=start_date,
                    months=periods,
                    product_categories=product_categories,
                    product_names=product_names,
                    regions=regions,
                    segments=segments
                )
                print(f"[DEBUG] Generated monthly forecast with shape: {forecast_df.shape}")
            
            # Step 4: Prepare the result
            
            # Group by time period for overall forecast
            if period == "week":
                time_group = forecast_df.groupby(['Year', 'Week'])
                time_label = 'Week'
            else:
                time_group = forecast_df.groupby(['Year', 'Month'])
                time_label = 'Month'
            
            # Calculate aggregates
            agg_data = time_group.agg({
                'PredictedRevenue': 'sum',
                'PredictedProfit': 'sum'
            }).reset_index()
            
            # Create time period label
            if period == "week":
                agg_data['Period'] = agg_data['Year'].astype(str) + '-W' + agg_data['Week'].astype(str)
            else:
                agg_data['Period'] = agg_data['Year'].astype(str) + '-' + agg_data['Month'].astype(str)
            
            # Prepare the result data
            result_data = []
            for _, row in agg_data.iterrows():
                result_data.append({
                    "period": row['Period'],
                    "value": float(row['PredictedRevenue']),
                    "profit": float(row['PredictedProfit']),
                    "is_forecast": True
                })
            
            print(f"[DEBUG] Prepared {len(result_data)} records for forecast result")
            
            # Create visualization data in the format expected by the frontend
            chart_data = []
            for record in result_data:
                chart_data.append({
                    "month": record["period"],
                    "desktop": float(record["value"]),
                    "mobile": float(record["profit"])
                })
            
            print(f"[DEBUG] Prepared chart data with {len(chart_data)} points")
            
            return {
                "type": "forecast",
                "target_column": target_col,
                "period": period,
                "num_periods": periods,
                "data": result_data,
                "chart_data": chart_data
            }
            
        except Exception as e:
            print(f"[ERROR] Error generating forecast: {str(e)}")
            print(f"[ERROR] Traceback: {traceback.format_exc()}")
            return {
                "type": "error",
                "message": f"Error generating forecast: {str(e)}"
            }