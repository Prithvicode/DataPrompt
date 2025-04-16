import { useState, useEffect } from "react";
import MessageList from "./chat/MessageList";
import ChatInput from "./chat/ChatInput";
import DataTable from "./chat/DataTable";
import DataSummary from "./chat/DataSummary";
import ForecastResults from "./chat/ForecastResults";
import { Message, TableRow } from "./chat/types";

export default function ChatComponent() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [tableData, setTableData] = useState<TableRow[] | null>(null);
  const [summaryData, setSummaryData] = useState<Record<string, any> | null>(
    null
  );
  const [forecastData, setForecastData] = useState<any | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [showSidebar, setShowSidebar] = useState(false);
  const [streamContent, setStreamContent] = useState("");

  // Prevent body scrolling
  useEffect(() => {
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = "auto";
    };
  }, []);

  const processData = async (prompt: string) => {
    if (!prompt.trim()) return;

    // Check if a file is selected
    if (!file) {
      // Show error message to user
      setMessages((prev) => [
        ...prev,
        {
          role: "user",
          content: prompt,
          timestamp: new Date(),
        },
        {
          role: "assistant",
          content: "Error: Please upload a CSV file before asking questions.",
          timestamp: new Date(),
        },
      ]);
      return;
    }

    setLoading(true);
    setIsStreaming(true);
    setShowSidebar(true);
    setStreamContent("");

    // Add user message to the chat
    const userMessage: Message = {
      role: "user",
      content: prompt,
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMessage]);

    // Add a temporary assistant message
    const tempAssistantMessage: Message = {
      role: "assistant",
      content: "",
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, tempAssistantMessage]);

    // Clear any previous data
    setTableData(null);
    setSummaryData(null);
    setForecastData(null);

    const formData = new FormData();
    formData.append("prompt", prompt);
    formData.append("file", file);

    try {
      const response = await fetch("http://localhost:8000/process", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error("Failed to get response reader");
      }

      let accumulatedContent = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        // Convert the chunk to text
        const chunk = new TextDecoder().decode(value);
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const data = line.slice(6);
            if (data === "[DONE]") {
              // Update the final message
              setMessages((prev) => {
                const newMessages = [...prev];
                newMessages[newMessages.length - 1] = {
                  role: "assistant",
                  content: accumulatedContent,
                  timestamp: new Date(),
                };
                return newMessages;
              });
            } else {
              try {
                const parsed = JSON.parse(data);
                if (parsed.content) {
                  accumulatedContent += parsed.content;
                  setStreamContent(accumulatedContent);
                }
              } catch (e) {
                console.error("Failed to parse streaming data:", e);
              }
            }
          }
        }
      }
    } catch (error) {
      console.error("Error processing data:", error);
      // Update the temporary message with an error message
      setMessages((prev) => {
        const newMessages = [...prev];
        newMessages[newMessages.length - 1] = {
          role: "assistant",
          content: `Error: ${(error as Error).message}`,
          timestamp: new Date(),
        };
        return newMessages;
      });
    } finally {
      setLoading(false);
      setIsStreaming(false);
      setStreamContent("");
    }
  };

  const DataView = () => (
    <div className="space-y-6">
      {tableData && <DataTable data={tableData} />}
      {summaryData && <DataSummary data={summaryData} />}
      {forecastData && <ForecastResults data={forecastData} />}
    </div>
  );

  return (
    <div className="flex h-[600px] bg-[#1A1A1A] text-white w-full overflow-hidden">
      {/* Custom scrollbar styles */}
      <style jsx global>{`
        /* Custom scrollbar styles */
        ::-webkit-scrollbar {
          width: 8px;
          height: 8px;
        }

        ::-webkit-scrollbar-track {
          background: #1a1a1a;
        }

        ::-webkit-scrollbar-thumb {
          background: #3a3a3a;
          border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb:hover {
          background: #4a4a4a;
        }

        /* Firefox scrollbar */
        * {
          scrollbar-width: thin;
          scrollbar-color: #3a3a3a #1a1a1a;
        }
      `}</style>

      {/* Main Chat Area */}
      <div
        className={`flex flex-col flex-1 transition-all duration-300 ${
          showSidebar ? "lg:w-2/3" : "w-full"
        }`}
      >
        <div className="flex-1 overflow-hidden">
          <div className="h-full relative">
            <div className="absolute inset-0 overflow-y-auto">
              <div className="max-w-5xl mx-auto px-4">
                <MessageList
                  messages={messages}
                  isStreaming={isStreaming}
                  streamContent={streamContent}
                />
              </div>
            </div>
          </div>
        </div>

        <div className="w-full">
          <ChatInput
            onSend={processData}
            loading={loading}
            file={file}
            onFileChange={setFile}
          />
        </div>
      </div>

      {/* Data Visualization Sidebar - Desktop */}
      {(tableData || summaryData || forecastData) && showSidebar && (
        <div className="hidden lg:block w-1/3 border-l border-gray-800 overflow-y-auto bg-[#222222] p-4">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-semibold text-[#2A9FD6]">
              Data Analysis
            </h2>
            <button
              onClick={() => setShowSidebar(false)}
              className="text-gray-400 hover:text-white"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-5 w-5"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fillRule="evenodd"
                  d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                  clipRule="evenodd"
                />
              </svg>
            </button>
          </div>
          <DataView />
        </div>
      )}

      {/* Data Visualization - Mobile */}
      {(tableData || summaryData || forecastData) && showSidebar && (
        <div className="lg:hidden fixed inset-0 z-50 bg-[#222222] overflow-y-auto">
          <div className="p-4">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold text-[#2A9FD6]">
                Data Analysis
              </h2>
              <button
                onClick={() => setShowSidebar(false)}
                className="text-gray-400 hover:text-white p-2"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-6 w-6"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                    clipRule="evenodd"
                  />
                </svg>
              </button>
            </div>
            <DataView />
          </div>
        </div>
      )}

      {/* Toggle Sidebar Button */}
      {(tableData || summaryData || forecastData) && !showSidebar && (
        <button
          onClick={() => setShowSidebar(true)}
          className="fixed right-4 bottom-24 bg-[#2A9FD6] text-white p-3 rounded-full shadow-lg hover:bg-[#1E8BC0] transition-colors z-10"
          title="Show Data Analysis"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-6 w-6"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
            />
          </svg>
        </button>
      )}
    </div>
  );
}
