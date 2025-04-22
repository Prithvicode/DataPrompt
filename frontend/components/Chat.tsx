"use client";

import { useState, useEffect, useRef } from "react";
import { Sparkles, X, BarChart, Database } from "lucide-react";
import MessageList from "./chat/MessageList";
import ChatInput from "./chat/ChatInput";
import DataTable from "./chat/DataTable";
import DataSummary from "./chat/DataSummary";
import ForecastResults from "./chat/ForecastResults";

import AggregationResults from "./chat/AggregationResults";
import DatasetSelector from "./chat/DatasetSelector";
import type { Message, DatasetInfo, AnalysisResult } from "./chat/types";
import { cn } from "@/lib/utils";

export default function ChatComponent() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(
    null
  );
  const [streamContent, setStreamContent] = useState("");
  const [showSidebar, setShowSidebar] = useState(false);
  const [datasets, setDatasets] = useState<DatasetInfo[]>([]);
  const [activeDatasetId, setActiveDatasetId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    document.body.style.overflow = "hidden";
    fetchDatasets();
    return () => {
      document.body.style.overflow = "auto";
    };
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamContent]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const fetchDatasets = async () => {
    try {
      const response = await fetch("http://localhost:8000/datasets");
      if (response.ok) {
        const data = await response.json();
        setDatasets(data.datasets || []);
      }
    } catch (error) {
      console.error("Error fetching datasets:", error);
    }
  };

  const uploadFile = async (file: File) => {
    const formData = new FormData();
    formData.append("file", file);

    try {
      setLoading(true);
      const response = await fetch("http://localhost:8000/upload", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.statusText}`);
      }

      const data = await response.json();
      setActiveDatasetId(data.id);

      // Add a system message about the successful upload
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `File "${data.filename}" uploaded successfully. You can now ask questions about this data.`,
          timestamp: new Date(),
        },
      ]);

      // Refresh the datasets list
      fetchDatasets();
      return data.id;
    } catch (error) {
      console.error("Error uploading file:", error);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Error uploading file: ${
            error instanceof Error ? error.message : "Unknown error"
          }`,
          timestamp: new Date(),
        },
      ]);
      return null;
    } finally {
      setLoading(false);
    }
  };

  const processData = async (prompt: string, attachedFile: File | null) => {
    // Allow sending a message with just a file (no text)
    if (!prompt.trim() && !attachedFile) return;

    // Add user message with file attachment if present
    setMessages((prev) => [
      ...prev,
      {
        role: "user",
        content: prompt,
        timestamp: new Date(),
        file: attachedFile
          ? {
              name: attachedFile.name,
              type: attachedFile.type,
              size: attachedFile.size,
            }
          : null,
      },
    ]);

    setLoading(true);
    setStreamContent("");

    // Clear previous results
    setAnalysisResult(null);

    // Handle file upload if a new file is attached
    let datasetId = activeDatasetId;
    if (attachedFile) {
      datasetId = await uploadFile(attachedFile);
      setFile(null); // Clear the file input after upload
    }

    // If we don't have a dataset ID (either from previous uploads or a new upload), show an error
    if (!datasetId) {
      if (!attachedFile) {
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content:
              "Please upload a file first or select a dataset to analyze.",
            timestamp: new Date(),
          },
        ]);
        setLoading(false);
        return;
      }
      // If we tried to upload a file but it failed, we've already shown an error message
      setLoading(false);
      return;
    }

    // Prepare chat history for context
    const chatHistory = messages
      .slice(-10) // Only use the last 10 messages for context
      .map((msg) => ({
        role: msg.role,
        content: msg.content,
      }));

    // Temp assistant message placeholder
    setMessages((prev) => [
      ...prev,
      { role: "assistant", content: "", timestamp: new Date() },
    ]);

    try {
      // First, try to get a structured analysis
      const analysisResponse = await fetch("http://localhost:8000/analyze", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          prompt,
          dataset_id: datasetId,
          chat_history: chatHistory,
        }),
      });

      if (!analysisResponse.ok) {
        throw new Error(`Analysis failed: ${analysisResponse.statusText}`);
      }

      const analysisData = await analysisResponse.json();
      console.log("Analysis response:", analysisData);

      // If we have a result, show it in the sidebar
      if (analysisData.result) {
        setAnalysisResult(analysisData.result);
        setShowSidebar(true);
      }

      // Now get a streaming explanation using the /chat endpoint
      const chatResponse = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          prompt,
          chat_history: chatHistory,
          job_id: analysisData.job_id,
        }),
      });

      if (!chatResponse.ok) {
        throw new Error(`Chat failed: ${chatResponse.statusText}`);
      }

      console.log("Chat response:", chatResponse.body);
      const reader = chatResponse.body?.getReader();
      if (!reader) throw new Error("No reader");

      let fullContent = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const lines = new TextDecoder().decode(value).split("\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const data = line.slice(6);
            if (data === "[DONE]") {
              setMessages((prev) => {
                const updated = [...prev];
                updated[updated.length - 1] = {
                  role: "assistant",
                  content: fullContent,
                  timestamp: new Date(),
                };
                return updated;
              });
            } else {
              try {
                const parsed = JSON.parse(data);
                if (parsed.content) {
                  fullContent += parsed.content;
                  setStreamContent(fullContent);
                }
              } catch (e) {
                console.error("Parsing error:", e);
              }
            }
          }
        }
      }
    } catch (err: any) {
      // Handle network or other errors
      console.error("Error in processData:", err);
      const errorMessage = `I encountered an error: ${err.message}`;

      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          role: "assistant",
          content: errorMessage,
          timestamp: new Date(),
        };
        return updated;
      });
    } finally {
      setLoading(false);
      setStreamContent("");
    }
  };

  const handleDatasetSelect = (datasetId: string) => {
    setActiveDatasetId(datasetId);

    // Find the dataset info
    const dataset = datasets.find((d) => d.id === datasetId);
    if (dataset) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Dataset "${dataset.filename}" selected. You can now ask questions about this data.`,
          timestamp: new Date(),
        },
      ]);
    }
  };

  const DataView = () => {
    if (!analysisResult) return null;

    switch (analysisResult.type) {
      case "summary":
        return <DataSummary data={analysisResult.data} />;
      case "forecast":
        return <ForecastResults data={analysisResult} />;
      case "aggregation":
        return <AggregationResults data={analysisResult} />;
      case "filter":
        return <DataTable data={analysisResult.data} />;
      case "query":
        return analysisResult.data ? (
          <DataTable data={analysisResult.data} />
        ) : null;
      default:
        return (
          <div className="p-4 text-gray-400">
            No visualization available for this result type.
          </div>
        );
    }
  };

  const hasData = !!analysisResult;
  const hasMessages = messages.length > 0;

  return (
    <div className="flex h-screen text-gray-100 overflow-hidden w-full custom-scrollbar">
      {/* Main Chat Area */}
      <div
        className={cn(
          "flex flex-col flex-1 h-full transition-all duration-300 ease-in-out",
          showSidebar && hasData ? "lg:pr-[600px]" : ""
        )}
      >
        {/* Chat Header */}
        <div className="border-b border-gray-800 py-3 bg-gray-950 px-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-blue-400" />
            <h1 className="text-xl font-semibold">DataPrompt</h1>
          </div>

          {datasets.length > 0 && (
            <div className="flex items-center">
              <Database className="h-4 w-4 text-blue-400 mr-2" />
              <DatasetSelector
                datasets={datasets}
                activeDatasetId={activeDatasetId}
                onSelect={handleDatasetSelect}
              />
            </div>
          )}
        </div>

        {/* Conditional Layout based on whether there are messages */}
        {!hasMessages ? (
          // Empty state with centered input
          <div className="flex flex-col flex-1 items-center justify-center px-4 bg-gray-950">
            <div className="w-full max-w-md space-y-8">
              <div className="text-center space-y-4">
                <Sparkles className="h-12 w-12 text-blue-400 mx-auto opacity-80" />
                <h2 className="text-2xl font-semibold">Chat with DataPrompt</h2>
                <p className="text-gray-400 mb-8">
                  Upload your data and ask questions to get insights,
                  visualizations, and forecasts.
                </p>
              </div>

              {/* Centered chat input */}
              <ChatInput
                onSend={processData}
                loading={loading}
                file={file}
                onFileChange={setFile}
              />

              {/* Example prompts */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-8">
                {[
                  "Analyze trends in this dataset",
                  "Summarize key insights",
                  "Create a 3-month forecast",
                  "Find outliers in this data",
                ].map((suggestion, i) => (
                  <button
                    key={i}
                    onClick={() => processData(suggestion, file)}
                    className="text-left p-3 rounded-lg border border-gray-800 hover:border-blue-500 hover:bg-gray-900 transition-all"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          // Regular chat layout with messages and input at bottom
          <>
            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto px-4 py-4 scroll-smooth bg-gray-950 custom-scrollbar">
              <MessageList
                messages={messages}
                isStreaming={!!streamContent}
                streamContent={streamContent}
              />
              <div ref={messagesEndRef} />
            </div>

            {/* Input Area at bottom */}
            <div className="p-6 bg-gray-950 ">
              <ChatInput
                onSend={processData}
                loading={loading}
                file={file}
                onFileChange={setFile}
              />
            </div>
          </>
        )}
      </div>

      {/* Data Visualization Sidebar */}
      <div
        className={cn(
          "fixed top-0 right-0 h-full w-full sm:w-[500px] md:w-[600px] lg:w-[700px] xl:w-[800px] 2xl:w-[900px] bg-gray-900 border-l border-gray-800 shadow-lg transition-all duration-300 ease-in-out transform z-50",
          showSidebar && hasData ? "translate-x-0" : "translate-x-full"
        )}
      >
        <div className="h-full flex flex-col">
          {/* Header */}
          <div className="border-b border-gray-800 p-4 flex justify-between items-center bg-gray-900">
            <div className="flex items-center gap-2">
              <BarChart className="h-5 w-5 text-blue-400" />
              <h2 className="font-semibold text-white text-lg">
                Data Analysis
              </h2>
            </div>
            <button
              onClick={() => setShowSidebar(false)}
              className="p-2 rounded-md hover:bg-gray-800 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500"
              aria-label="Close sidebar"
            >
              <X className="h-5 w-5 text-gray-300" />
            </button>
          </div>

          {/* Scrollable content */}
          <div className="flex-1 overflow-y-auto p-6 custom-scrollbar bg-gray-900">
            <DataView />
          </div>
        </div>
      </div>

      {/* Toggle Sidebar Button */}
      {!showSidebar && hasData && (
        <button
          onClick={() => setShowSidebar(true)}
          className="fixed bottom-24 right-4 bg-blue-600 text-white p-3 rounded-full shadow-lg hover:shadow-xl transition-all"
          aria-label="Show data analysis"
        >
          <BarChart className="h-5 w-5" />
        </button>
      )}
    </div>
  );
}
