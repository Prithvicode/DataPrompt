import { useState } from "react";

interface TableRow {
  [key: string]: string | number | boolean | null;
}

export default function ChatComponent() {
  const [prompt, setPrompt] = useState("");
  const [response, setResponse] = useState("");
  const [loading, setLoading] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [tableData, setTableData] = useState<TableRow[] | null>(null);
  const [summaryData, setSummaryData] = useState<Record<string, any> | null>(
    null
  );

  // Process both the prompt and the CSV file
  const processData = async () => {
    if (!prompt.trim() || !file) return;
    setLoading(true);
    setResponse("");
    // Clear any previous data
    setTableData(null);
    setSummaryData(null);

    const formData = new FormData();
    formData.append("prompt", prompt);
    formData.append("file", file);

    try {
      const res = await fetch("http://localhost:8000/process", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      setResponse(data.response);
      // Check if the returned data is an array (table) or an object (summary)
      if (data.data) {
        if (Array.isArray(data.data)) {
          setTableData(data.data); // Set table data if array
        } else {
          setSummaryData(data.data); // Set summary data if object
        }
      }
    } catch (error) {
      console.error("Error processing data:", error);
    } finally {
      setLoading(false);
    }
  };

  const uploadFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const uploadedFile = e.target.files ? e.target.files[0] : null;
    setFile(uploadedFile);
  };

  return (
    <div className="w-full max-w-5xl mx-auto p-6 bg-[#2D2D2D] text-white shadow-lg rounded-3xl">
      <div className="mb-6 flex flex-col space-y-5">
        {/* Prompt Input */}
        <div className="flex items-center space-x-3">
          <input
            type="text"
            placeholder="Enter your prompt..."
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            className="flex-1 p-4 bg-[#3C3C3C] text-white rounded-2xl border border-[#444444] focus:outline-none focus:ring-2 focus:ring-[#2A9FD6] transition duration-300"
          />
          <button
            onClick={processData}
            disabled={loading || !file}
            className="px-6 py-3 bg-[#2A9FD6] hover:bg-[#1D8CB7] rounded-full text-white font-semibold disabled:opacity-50 transition duration-300"
          >
            {loading ? "Thinking..." : "Send"}
          </button>
        </div>

        {/* File Upload with Round Button */}
        <div className="flex items-center space-x-4">
          <input
            type="file"
            onChange={uploadFile}
            className="hidden"
            id="fileUpload"
          />
          <label
            htmlFor="fileUpload"
            className="size-10 flex items-center justify-center rounded-full bg-[#2A9FD6] text-white cursor-pointer hover:bg-[#1D8CB7] transition duration-300"
          >
            <span className="text-3xl">+</span>
          </label>
          {file && (
            <span className="text-gray-300 text-sm truncate max-w-xs">
              {file.name}
            </span>
          )}
        </div>
      </div>

      {/* Display Response */}
      {response && (
        <div className="mt-6 p-6 bg-[#3C3C3C] border border-[#444444] rounded-2xl">
          <p className="text-gray-300">{response}</p>
        </div>
      )}

      {/* Display Table Data */}
      {tableData && (
        <div className="mt-6 overflow-x-auto bg-[#3C3C3C] border border-[#444444] rounded-2xl">
          <table className="min-w-full border-collapse text-gray-300">
            <thead>
              <tr className="bg-[#444444]">
                {Object.keys(tableData[0]).map((key) => (
                  <th
                    key={key}
                    className="px-6 py-3 text-left font-medium text-gray-400"
                  >
                    {key}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {tableData.map((row, index) => (
                <tr key={index} className="bg-[#3C3C3C]">
                  {Object.values(row).map((value, idx) => (
                    <td
                      key={idx}
                      className="px-6 py-4 border-t border-[#444444] text-sm"
                    >
                      {value !== null ? value : "N/A"}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Display Summary Data */}
      {summaryData && (
        <div className="mt-6 p-6 bg-[#3C3C3C] border border-[#444444] rounded-2xl">
          <h3 className="text-xl font-bold mb-4 text-[#2A9FD6]">
            Data Summary
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {Object.entries(summaryData.summary_stats).map(
              ([column, stats]) => (
                <div key={column} className="space-y-2">
                  <h4 className="font-semibold text-gray-300">{column}</h4>
                  <ul className="list-disc pl-5 space-y-1">
                    {typeof stats === "object" && stats !== null
                      ? Object.entries(stats).map(([key, value]) => (
                          <li key={key} className="text-sm text-gray-400">
                            {key}: {value !== null ? value : "N/A"}
                          </li>
                        ))
                      : String(stats)}
                  </ul>
                </div>
              )
            )}
          </div>
          <div className="mt-4 p-4 bg-[#444444] text-gray-300 rounded-lg">
            <p>{summaryData.summary_explanation}</p>
          </div>
        </div>
      )}
    </div>
  );
}
