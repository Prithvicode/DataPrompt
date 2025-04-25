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
import { fetchDatasets as fetchDatasetsAPI } from "@/services/query";

// Import UI components
import { Header } from "./Header";
import { IconHeader } from "./IconHeader";
import { ActionButton } from "./ActionButton";
import { EmptyState } from "./EmptyState";
import { Sidebar } from "./Sidebar";
import { SuggestionGrid } from "./SuggestionGrid";
import PredictionResults from "./chat/PredictResults";
import { Loader } from "./Loader";
import QueryResultCard from "./chat/QueryResultCard";

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
    fetchDatasetsData();
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

  const fetchDatasetsData = async () => {
    try {
      const response = await fetchDatasetsAPI();
      if (response && response.datasets) {
        setDatasets(response.datasets);
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

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `File "${data.filename}" uploaded successfully. You can now ask questions about this data.`,
          timestamp: new Date(),
        },
      ]);

      fetchDatasetsData();
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
    if (!prompt.trim() && !attachedFile) return;

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
    setAnalysisResult(null);

    let datasetId = activeDatasetId;
    if (attachedFile) {
      datasetId = await uploadFile(attachedFile);
      setFile(null);
    }

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
      setLoading(false);
      return;
    }

    const chatHistory = messages
      .slice(-10)
      .map((msg) => ({ role: msg.role, content: msg.content }));

    setMessages((prev) => [
      ...prev,
      { role: "assistant", content: "", timestamp: new Date() },
    ]);

    try {
      const analysisResponse = await fetch("http://localhost:8000/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt,
          dataset_id: datasetId,
          chat_history: chatHistory,
        }),
      });

      if (!analysisResponse.ok)
        throw new Error(`Analysis failed: ${analysisResponse.statusText}`);
      const analysisData = await analysisResponse.json();
      if (analysisData.result) {
        setAnalysisResult(analysisData.result);
        setShowSidebar(true);
      }

      const chatResponse = await fetch("http://localhost:8000/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          prompt,
          chat_history: chatHistory,
          job_id: analysisData.job_id,
        }),
      });

      if (!chatResponse.ok)
        throw new Error(`Chat failed: ${chatResponse.statusText}`);
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
      case "predict":
        return (
          <PredictionResults
            data={analysisResult.data}
            mae={analysisResult.mae ?? 0}
            r2={analysisResult.r2 ?? 0}
            visualization={
              analysisResult.visualization ?? {
                type: "",
                data: [],
                x: "",
                y: "",
                title: "",
                xLabel: "",
                yLabel: "",
              }
            }
          />
        );
      case "aggregation":
        return <AggregationResults data={analysisResult} />;
      case "filter":
        return <DataTable data={analysisResult.data} intentType="filter" />;
      case "query":
        return analysisResult.data ? (
          <QueryResultCard
            value={analysisResult.data}
            note={analysisResult.note}
          />
        ) : null;
      default:
        return (
          <div className="p-4 text-gray-500">
            No visualization available for this result type.
          </div>
        );
    }
  };

  const hasData = !!analysisResult;
  const hasMessages = messages.length > 0;

  const examplePrompts = [
    "Analyze trends in this dataset",
    "Summarize key insights",
    "Create a 3-month forecast",
    "Find outliers in this data",
  ];

  return (
    <div className="flex h-screen text-gray-800 bg-gray-200 overflow-hidden w-full custom-scrollbar">
      <div
        className={cn(
          "flex flex-col flex-1 h-full transition-all duration-300 ease-in-out",
          showSidebar && hasData ? "lg:pr-[600px]" : ""
        )}
      >
        <Header
          leftContent={
            <IconHeader
              icon={Sparkles}
              text="DataPrompt"
              iconColor="text-blue-600"
            />
          }
          rightContent={
            datasets.length > 0 && (
              <div className="flex items-center">
                <Database className="h-4 w-4 text-blue-600 mr-2" />
                <DatasetSelector
                  datasets={datasets}
                  activeDatasetId={activeDatasetId}
                  onSelect={handleDatasetSelect}
                />
              </div>
            )
          }
        />

        {!hasMessages ? (
          <EmptyState
            icon={Sparkles}
            title="Chat with DataPrompt"
            description="Upload your data and ask questions to get insights, visualizations, and forecasts."
            iconColor="text-blue-600"
            className="flex-1 bg-gray-100"
            action={
              <>
                <ChatInput
                  onSend={processData}
                  loading={loading}
                  file={file}
                  onFileChange={setFile}
                />
                <SuggestionGrid
                  suggestions={examplePrompts}
                  onSelect={(suggestion: string) =>
                    processData(suggestion, file)
                  }
                  className="mt-8"
                />
              </>
            }
          />
        ) : (
          <>
            <div className="flex-1 overflow-y-auto px-4 py-4 scroll-smooth bg-gray-100 custom-scrollbar">
              <MessageList
                messages={messages}
                isStreaming={!!streamContent}
                streamContent={streamContent}
              />
              {loading && !streamContent && <Loader loading={loading} />}
              <div ref={messagesEndRef} />
            </div>

            <div className="p-6 bg-gray-100">
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

      <Sidebar
        isOpen={showSidebar && hasData}
        onClose={() => setShowSidebar(false)}
        header={<IconHeader icon={BarChart} text="Data Analysis" />}
      >
        <DataView />
      </Sidebar>

      {!showSidebar && hasData && (
        <ActionButton
          icon={BarChart}
          onClick={() => setShowSidebar(true)}
          className="fixed bottom-24 right-4"
          label="Show data analysis"
        />
      )}
    </div>
  );
}
