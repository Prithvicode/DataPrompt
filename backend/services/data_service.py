import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Union
import json
import requests
import re
import traceback
from datetime import datetime, timedelta
import json

# from services.prepare_data_for_prediction import forecast_weekly_sales, forecast_monthly_sales  # Adjust to your actual import path
from dateutil.parser import parse as parse_date

from services.nlp_service import generate_panda_code_from_prompt, classify_forecast_intent, parse_whatif_scenarios
from services.forecast_service import process_and_predict

# from services.prepare_data_for_prediction import predict_sales, forecast_weekly_sales, forecast_monthly_sales

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

    # def generate_summary(self) -> Dict[str, Any]:
    #     """
    #     Generate a structured summary of the dataset.
    #     """
    #     print("[DEBUG] Generating dataset summary")
    #     df = self.df
    #     summary = {
    #         "dataset_info": {
    #             "rows": len(df),
    #             "columns": len(df.columns),
    #             "column_names": df.columns.tolist(),
    #             "numeric_columns": self.numeric_columns,
    #             "categorical_columns": self.categorical_columns,
    #             "date_columns": self.date_columns,
    #             "missing_values": df.isnull().sum().to_dict()
    #         }
    #     }

    #     # Numeric statistics
    #     if self.numeric_columns:
    #         print(f"[DEBUG] Calculating statistics for {len(self.numeric_columns)} numeric columns")
    #         summary["numeric_stats"] = df[self.numeric_columns].describe().to_dict()

    #     # Categorical statistics
    #     if self.categorical_columns:
    #         print(f"[DEBUG] Calculating statistics for {len(self.categorical_columns)} categorical columns")
    #         summary["categorical_stats"] = {
    #             col: {
    #                 "unique_values": df[col].nunique(),
    #                 "top_values": df[col].value_counts().head(10).to_dict()
    #             }
    #             for col in self.categorical_columns
    #         }

    #     # Date statistics
    #     if self.date_columns:
    #         print(f"[DEBUG] Calculating statistics for {len(self.date_columns)} date columns")
    #         date_stats = {}
    #         for col in self.date_columns:
    #             try:
    #                 date_series = pd.to_datetime(df[col])
    #                 date_stats[col] = {
    #                     "min_date": date_series.min().isoformat(),
    #                     "max_date": date_series.max().isoformat(),
    #                     "range_days": (date_series.max() - date_series.min()).days
    #                 }
    #                 print(f"[DEBUG] Date stats for {col}: range = {date_stats[col]['range_days']} days")
    #             except Exception as e:
    #                 print(f"[ERROR] Error calculating date stats for {col}: {str(e)}")
    #                 date_stats[col] = {"error": str(e)}
    #         summary["date_stats"] = date_stats

    #     print("[DEBUG] Summary generation complete")
    #     return {
    #         "type": "summary",
    #         "data": summary
    #     }
    
    def generate_summary(self) -> Dict[str, Any]:
        """
        Generate a structured summary of the dataset with enhanced insights for visualization.
        """
        print("[DEBUG] Generating enhanced dataset summary")
        df = self.df
        
        # Base summary structure
        summary = {
            "dataset_info": {
                "rows": len(df),
                "columns": len(df.columns),
                "column_names": df.columns.tolist(),
                "numeric_columns": self.numeric_columns,
                "categorical_columns": self.categorical_columns,
                "date_columns": self.date_columns,
                "missing_values": df.isnull().sum().to_dict()
            },
            "charts_data": {}  # Data specifically formatted for Recharts
        }
        
        # Numeric statistics
        if self.numeric_columns:
            print(f"[DEBUG] Calculating statistics for {len(self.numeric_columns)} numeric columns")
            summary["numeric_stats"] = df[self.numeric_columns].describe().to_dict()
            
            # Revenue and profit trends by time period (for time series charts)
            if all(col in df.columns for col in ['Revenue', 'Profit', 'Month', 'Year']):
                monthly_performance = df.groupby(['Year', 'Month']).agg({
                    'Revenue': 'sum',
                    'Profit': 'sum',
                    'UnitsSold': 'sum'
                }).reset_index()
                
                # Format for time series chart
                summary["charts_data"]["monthly_performance"] = [
                    {
                        "date": f"{int(row['Year'])}-{int(row['Month']):02d}",
                        "revenue": round(row['Revenue'], 2),
                        "profit": round(row['Profit'], 2),
                        "unitsSold": int(row['UnitsSold'])
                    }
                    for _, row in monthly_performance.iterrows()
                ]
                
            # Product performance metrics (for bar/pie charts)
            if all(col in df.columns for col in ['ProductCategory', 'Revenue', 'Profit']):
                product_performance = df.groupby('ProductCategory').agg({
                    'Revenue': 'sum',
                    'Profit': 'sum',
                    'UnitsSold': 'sum',
                    'OrderID': 'nunique'
                }).reset_index()
                
                # Calculate additional metrics
                product_performance['AverageOrderValue'] = product_performance['Revenue'] / product_performance['OrderID']
                product_performance['ProfitPerUnit'] = product_performance['Profit'] / product_performance['UnitsSold']
                
                # Format for category comparison charts
                summary["charts_data"]["product_category_performance"] = [
                    {
                        "category": row['ProductCategory'],
                        "revenue": round(row['Revenue'], 2),
                        "profit": round(row['Profit'], 2),
                        "unitsSold": int(row['UnitsSold']),
                        "orders": int(row['OrderID']),
                        "avgOrderValue": round(row['AverageOrderValue'], 2),
                        "profitPerUnit": round(row['ProfitPerUnit'], 2)
                    }
                    for _, row in product_performance.iterrows()
                ]
                
            # Regional performance (for map or comparison charts)
            if 'Region' in df.columns:
                regional_performance = df.groupby('Region').agg({
                    'Revenue': 'sum',
                    'Profit': 'sum',
                    'UnitsSold': 'sum',
                    'OrderID': 'nunique'
                }).reset_index()
                
                # Format for regional charts
                summary["charts_data"]["regional_performance"] = [
                    {
                        "region": row['Region'],
                        "revenue": round(row['Revenue'], 2),
                        "profit": round(row['Profit'], 2),
                        "unitsSold": int(row['UnitsSold']),
                        "orders": int(row['OrderID'])
                    }
                    for _, row in regional_performance.iterrows()
                ]
                
            # Promotion effectiveness (for comparison charts)
            if 'PromotionApplied' in df.columns:
                promotion_effect = df.groupby('PromotionApplied').agg({
                    'Revenue': 'sum',
                    'Profit': 'sum',
                    'UnitsSold': 'sum',
                    'ProfitMargin': 'mean'
                }).reset_index()
                
                # Format for promotion comparison
                summary["charts_data"]["promotion_effectiveness"] = [
                    {
                        "promotionApplied": bool(row['PromotionApplied']),
                        "revenue": round(row['Revenue'], 2),
                        "profit": round(row['Profit'], 2),
                        "unitsSold": int(row['UnitsSold']),
                        "avgProfitMargin": round(row['ProfitMargin'] * 100, 2)
                    }
                    for _, row in promotion_effect.iterrows()
                ]
                
            # Customer segment analysis
            if 'CustomerSegment' in df.columns:
                segment_analysis = df.groupby('CustomerSegment').agg({
                    'Revenue': 'sum',
                    'Profit': 'sum',
                    'UnitsSold': 'sum',
                    'OrderID': 'nunique'
                }).reset_index()
                
                segment_analysis['AvgRevenuePerOrder'] = segment_analysis['Revenue'] / segment_analysis['OrderID']
                
                # Format for segment comparison
                summary["charts_data"]["customer_segments"] = [
                    {
                        "segment": row['CustomerSegment'],
                        "revenue": round(row['Revenue'], 2),
                        "profit": round(row['Profit'], 2),
                        "unitsSold": int(row['UnitsSold']),
                        "avgRevenuePerOrder": round(row['AvgRevenuePerOrder'], 2)
                    }
                    for _, row in segment_analysis.iterrows()
                ]
        
        # Categorical statistics with enhanced insights
        if self.categorical_columns:
            print(f"[DEBUG] Calculating statistics for {len(self.categorical_columns)} categorical columns")
            summary["categorical_stats"] = {
                col: {
                    "unique_values": df[col].nunique(),
                    "top_values": df[col].value_counts().head(10).to_dict(),
                    "distribution": [
                        {"name": str(k), "value": int(v)} 
                        for k, v in df[col].value_counts().head(10).items()
                    ]
                }
                for col in self.categorical_columns
            }
            
            # Seasonal trends (if applicable)
            if 'Holiday' in df.columns:
                holiday_impact = df.groupby('Holiday').agg({
                    'Revenue': 'sum',
                    'UnitsSold': 'sum',
                    'FootTraffic': 'mean' if 'FootTraffic' in df.columns else 'count'
                }).reset_index()
                
                summary["charts_data"]["holiday_impact"] = [
                    {
                        "holiday": bool(row['Holiday']),
                        "revenue": round(row['Revenue'], 2),
                        "unitsSold": int(row['UnitsSold']),
                        "avgFootTraffic": round(row['FootTraffic'], 2)
                    }
                    for _, row in holiday_impact.iterrows()
                ]
        
        # Date statistics with enhanced time series data
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
                    
                    # Create time series distribution
                    if col == 'OrderDate':
                        # Daily order counts for timeline chart
                        daily_orders = df.groupby(date_series.dt.date).size().reset_index()
                        daily_orders.columns = ['date', 'count']
                        
                        # Format for timeline chart
                        summary["charts_data"]["daily_order_volume"] = [
                            {
                                "date": date.isoformat(),
                                "orders": int(count)
                            }
                            for date, count in zip(daily_orders['date'], daily_orders['count'])
                        ]
                        
                        # Weekday distribution
                        weekday_distribution = df.groupby(date_series.dt.day_name()).size().reset_index()
                        weekday_distribution.columns = ['weekday', 'count']
                        
                        # Ensure proper weekday ordering
                        weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                        weekday_distribution['weekday_order'] = weekday_distribution['weekday'].map(
                            {day: i for i, day in enumerate(weekday_order)}
                        )
                        weekday_distribution = weekday_distribution.sort_values('weekday_order')
                        
                        # Format for weekday distribution chart
                        summary["charts_data"]["weekday_distribution"] = [
                            {
                                "weekday": weekday,
                                "orders": int(count)
                            }
                            for weekday, count in zip(weekday_distribution['weekday'], weekday_distribution['count'])
                        ]
                    
                    print(f"[DEBUG] Date stats for {col}: range = {date_stats[col]['range_days']} days")
                except Exception as e:
                    print(f"[ERROR] Error calculating date stats for {col}: {str(e)}")
                    date_stats[col] = {"error": str(e)}
            
            summary["date_stats"] = date_stats
        
        # Additional insights
        # Temperature impact on sales (if temperature data exists)
        if 'Temperature' in df.columns:
            # Group by temperature ranges
            df['TempRange'] = pd.cut(df['Temperature'], 
                                    bins=[0, 10, 20, 30, 40, 100], 
                                    labels=['0-10', '10-20', '20-30', '30-40', '40+'])
            
            temp_impact = df.groupby('TempRange').agg({
                'UnitsSold': 'sum',
                'Revenue': 'sum',
                'FootTraffic': 'mean' if 'FootTraffic' in df.columns else 'count'
            }).reset_index()
            
            summary["charts_data"]["temperature_impact"] = [
                {
                    "tempRange": str(row['TempRange']),
                    "unitsSold": int(row['UnitsSold']),
                    "revenue": round(row['Revenue'], 2),
                    "footTraffic": round(row['FootTraffic'], 2)
                }
                for _, row in temp_impact.iterrows() if not pd.isna(row['TempRange'])
            ]
        
        # Profit margin distribution (for histogram)
        if 'ProfitMargin' in df.columns:
            # Create bins for profit margin distribution
            margin_bins = [-0.5, 0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
            margin_labels = ['Loss', '0-10%', '10-20%', '20-30%', '30-40%', '40-50%', 
                            '50-60%', '60-70%', '70-80%', '80-90%', '90-100%']
            
            df['MarginRange'] = pd.cut(df['ProfitMargin'], 
                                    bins=margin_bins,
                                    labels=margin_labels)
            
            margin_dist = df.groupby('MarginRange').size().reset_index()
            margin_dist.columns = ['range', 'count']
            
            summary["charts_data"]["profit_margin_distribution"] = [
                {
                    "range": str(range_name),
                    "count": int(count)
                }
                for range_name, count in zip(margin_dist['range'], margin_dist['count'])
                if not pd.isna(range_name)
            ]
        
        # Product performance over time
        if all(col in df.columns for col in ['ProductCategory', 'Month', 'Year', 'Revenue']):
            product_time = df.groupby(['ProductCategory', 'Year', 'Month']).agg({
                'Revenue': 'sum',
                'Profit': 'sum'
            }).reset_index()
            
            # Format for stacked/grouped bar or line chart
            summary["charts_data"]["product_category_time_series"] = [
                {
                    "date": f"{int(row['Year'])}-{int(row['Month']):02d}",
                    "category": row['ProductCategory'],
                    "revenue": round(row['Revenue'], 2),
                    "profit": round(row['Profit'], 2)
                }
                for _, row in product_time.iterrows()
            ]
        
        print("[DEBUG] Enhanced summary generation complete")
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



    def execute_query(self, prompt: str, df_columns: List[str]):
        """
        Execute a custom query using LLM to generate pandas code, returning
        either a scalar or a DataFrame.
        """
        code = generate_panda_code_from_prompt(prompt, df_columns)
        print("Generated code from LLM:", code)

        try:
            print(f"[DEBUG] Aggregating data with prompt: {prompt}")
            local_vars = {'df': self.df.copy()}

            # Only wrap if the model didn't already assign to `result`
            if not re.search(r'^\s*result\s*=', code):
                exec_code = f"result = {code}"
            else:
                exec_code = code

            print(f"[DEBUG] Executing code:\n{exec_code}")
            exec(exec_code, {}, local_vars)

            # Grab the result
            result = local_vars.get('result')

            # If still None, fall back to df
            if result is None:
                result = local_vars['df']

            print(f"[DEBUG] Aggregation result: {result!r}")
            return {
                'type' : 'query',
                'data' : result,
                'note' : {prompt}
            }

        except Exception as e:
            print(f"[ERROR] Error aggregating data: {str(e)}")
            print(traceback.format_exc())
            return {
                "type": "error",
                "message": f"Error aggregating data: {str(e)}"
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
    
    def aggregate(self, prompt: str, df_columns: List[str]):
        """
        Aggregate data based on one or more dimensions.
        """
        code = generate_panda_code_from_prompt(prompt, df_columns)
        print("Generated code from LLM:", code)

        try:
            print(f"[DEBUG] Aggregating data with prompt: {prompt}")
            local_vars = {'df': self.df.copy()}

                # Only wrap if the model didn't already assign to `result`
            if not re.search(r'^\s*result\s*=', code):
                exec_code = f"result = {code}"
            else:
                exec_code = code

            print(f"[DEBUG] Executing code:\n{exec_code}")
            exec(exec_code, {}, local_vars)

                # Grab the result
            result = local_vars.get('result')

                # If still None, fall back to df
            if result is None:
                 result = local_vars['df']

            print(f"[DEBUG] Aggregation result: {result!r}")
            return {
                    'type' : 'query',
                    'data' : result,
                    'note': {prompt}
                }

        except Exception as e:
                print(f"[ERROR] Error aggregating data: {str(e)}")
                print(traceback.format_exc())
                return {
                    "type": "error",
                    "message": f"Error aggregating data: {str(e)}"
                }
    
    def forecast(self, prompt: str, **parameters):
        """
        Forecast sales based on the user's prompt and the provided parameters.
        This method integrates with the LLM to determine what time range the user is asking for.
        """
        try:
            print(f"[DEBUG] Forecasting with prompt: {prompt}")
            
            # Step 1: Classify the intent of the forecast
            model_response = classify_forecast_intent(prompt, df_columns= self.df.columns.tolist())
            # Parse the string response to a dictionary
            try:
                intentResponse = json.loads(model_response)
            except json.JSONDecodeError as e:
                print(f"[ERROR] Failed to parse intent response: {e}")
                raise ValueError("Failed to parse forecast intent response as JSON.")

            print(f"[DEBUG] Classified intent: {intentResponse}")

            period_type = intentResponse.get("periodType", "weekly")
            period_ahead = intentResponse.get("periods_ahead", 1)  # Default to 1 week/month if not specified
            target_variable = intentResponse.get("target_variable", "Revenue")
            filters = intentResponse.get("filters")

            predictions = forecast_revenue(period_type=period_type, periods_ahead=period_ahead, df=self.df)
            print(f"[DEBUG] Predictions : {predictions}")
            
            return {
                "type": "forecast",
               "data": predictions,
            }


            
      
            
        #     # Step 3: Generate predictions based on the classified intent
        #     predictions = {
        #         "type": "forecast",
        #         "intent": intent,
        #         "data": forecast_data
        #     }
            
        #     print(f"[DEBUG] Forecasting complete, predictions shape: {len(predictions['data'])}")
            
        except Exception as e:
            print(f"[ERROR] Error during forecasting: {str(e)}")
            print(f"[ERROR] Traceback: {traceback.format_exc()}")
            return {
                "type": "error",
                "message": f"Error during forecasting: {str(e)}"
            }
       
        # return predictions

    def what_if_analysis(self, prompt: str, **parameters):
        feature_input = parse_whatif_scenarios(prompt, self.df.columns.tolist())
        print(f"[DEBUG] What-if analysis input: {feature_input}")
    
    def predict(self, prompt: str, **parameters):
        print("DEBUG] Predicting with prompt: ", prompt)
        result_df, mae, r2, visualization = process_and_predict(self.df)
        print(f"[DEBUG] Result DataFrame: {result_df.head()}")

        return {
            "type" : "predict",
            "data": result_df,
            "mae" : mae,
            "r2" : r2,
            "visualization" : visualization
        }