import { useState, useEffect } from "react";

interface ColumnInfo {
  name: string;
  dtype: string;
  unique_values: number;
  missing_values: number;
  sample_values: any[];
  suggested_type: string;
}

interface ColumnConfigProps {
  file: File | null;
  onConfigComplete: (config: any) => void;
  onBack: () => void;
}

export default function ColumnConfig({
  file,
  onConfigComplete,
  onBack,
}: ColumnConfigProps) {
  const [columns, setColumns] = useState<ColumnInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [columnTypes, setColumnTypes] = useState<Record<string, string>>({});
  const [targetColumn, setTargetColumn] = useState<string>("");

  useEffect(() => {
    if (file) {
      analyzeFile();
    }
  }, [file]);

  const analyzeFile = async () => {
    if (!file) return;

    setLoading(true);
    setError(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch("http://localhost:8000/upload-and-analyze", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setColumns(data.columns);

      // Initialize column types with suggested types
      const initialTypes: Record<string, string> = {};
      data.columns.forEach((col: ColumnInfo) => {
        initialTypes[col.name] = col.suggested_type;
      });
      setColumnTypes(initialTypes);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const handleColumnTypeChange = (columnName: string, type: string) => {
    setColumnTypes((prev) => ({
      ...prev,
      [columnName]: type,
    }));
  };

  const handleSubmit = async () => {
    if (!file) return;

    setLoading(true);

    // Prepare configuration
    const numericColumns = Object.entries(columnTypes)
      .filter(([_, type]) => type === "numeric")
      .map(([name, _]) => name);

    const categoricalColumns = Object.entries(columnTypes)
      .filter(([_, type]) => type === "categorical")
      .map(([name, _]) => name);

    const dateColumns = Object.entries(columnTypes)
      .filter(([_, type]) => type === "date")
      .map(([name, _]) => name);

    const config = {
      numeric_columns: numericColumns,
      categorical_columns: categoricalColumns,
      date_columns: dateColumns,
      target_column: targetColumn,
    };

    const formData = new FormData();
    formData.append("file", file);
    formData.append("column_config", JSON.stringify(config));

    try {
      const response = await fetch("http://localhost:8000/configure-columns", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error("Backend error response:", errorText);

        let errorMessage = `HTTP error! status: ${response.status}`;
        try {
          const errorData = JSON.parse(errorText);
          if (errorData.detail) {
            errorMessage = errorData.detail;
          }
        } catch (e) {
          // If we can't parse the error as JSON, use the raw text
          if (errorText) {
            errorMessage = errorText;
          }
        }

        throw new Error(errorMessage);
      }

      const data = await response.json();
      onConfigComplete({ ...config, file });
    } catch (err) {
      console.error("Error in handleSubmit:", err);
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  if (loading && columns.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-[400px] bg-white">
        <div className="text-center">
          <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Analyzing your dataset...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[400px] bg-white">
        <div className="text-center">
          <div className="text-red-500 mb-4">
            <svg
              className="w-12 h-12 mx-auto"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
          </div>
          <p className="text-red-600 mb-4">Error: {error}</p>
          <button
            onClick={onBack}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6 bg-white min-h-screen">
      <div className="mb-6">
        <button
          onClick={onBack}
          className="flex items-center text-gray-600 hover:text-gray-800 mb-4 transition-colors"
        >
          <svg
            className="w-5 h-5 mr-2"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15 19l-7-7 7-7"
            />
          </svg>
          Back to Upload
        </button>

        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Configure Your Dataset
        </h2>
        <p className="text-gray-600">
          Review and configure column types for optimal analysis. Select your
          target variable for predictions.
        </p>
      </div>

      <div className="bg-gray-50 rounded-lg p-6 mb-6 border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Target Variable (Y)
        </h3>
        <p className="text-gray-600 mb-4">
          Select the column you want to predict (e.g., Revenue, Sales, Price)
        </p>
        <select
          value={targetColumn}
          onChange={(e) => setTargetColumn(e.target.value)}
          className="w-full p-3 bg-white border border-gray-300 rounded-lg text-gray-900 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
        >
          <option value="">Select target variable...</option>
          {columns.map((col) => (
            <option key={col.name} value={col.name}>
              {col.name} ({col.suggested_type})
            </option>
          ))}
        </select>
      </div>

      <div className="bg-gray-50 rounded-lg p-6 mb-6 border border-gray-200">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Column Configuration
        </h3>
        <div className="space-y-4">
          {columns.map((col) => (
            <div
              key={col.name}
              className="border border-gray-200 rounded-lg p-4 bg-white"
            >
              <div className="flex items-center justify-between mb-3">
                <div>
                  <h4 className="text-gray-900 font-medium">{col.name}</h4>
                  <p className="text-sm text-gray-600">
                    Type: {col.dtype} | Unique: {col.unique_values} | Missing:{" "}
                    {col.missing_values}
                  </p>
                </div>
                <div className="flex space-x-2">
                  {["numeric", "categorical", "date"].map((type) => (
                    <button
                      key={type}
                      onClick={() => handleColumnTypeChange(col.name, type)}
                      className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
                        columnTypes[col.name] === type
                          ? "bg-blue-600 text-white"
                          : "bg-gray-200 text-gray-700 hover:bg-gray-300"
                      }`}
                    >
                      {type.charAt(0).toUpperCase() + type.slice(1)}
                    </button>
                  ))}
                </div>
              </div>

              {col.sample_values.length > 0 && (
                <div className="text-sm text-gray-600">
                  <span className="font-medium">Sample values:</span>{" "}
                  {col.sample_values.slice(0, 3).join(", ")}
                  {col.sample_values.length > 3 && "..."}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="flex justify-end space-x-4">
        <button
          onClick={onBack}
          className="px-6 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
        >
          Cancel
        </button>
        <button
          onClick={handleSubmit}
          disabled={loading || !targetColumn}
          className={`px-6 py-3 rounded-lg transition-colors ${
            loading || !targetColumn
              ? "bg-gray-400 text-gray-600 cursor-not-allowed"
              : "bg-blue-600 text-white hover:bg-blue-700"
          }`}
        >
          {loading ? (
            <div className="flex items-center">
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
              Configuring...
            </div>
          ) : (
            "Start Analysis"
          )}
        </button>
      </div>
    </div>
  );
}
