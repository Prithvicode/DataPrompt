"use client";

import { useState, useEffect, useRef } from "react";
import { Sparkles, X, BarChart } from "lucide-react";
import MessageList from "./chat/MessageList";
import ChatInput from "./chat/ChatInput";
import DataTable from "./chat/DataTable";
import DataSummary from "./chat/DataSummary";
import ForecastResults from "./chat/ForecastResults";
import type { Message, TableRow } from "./chat/types";
import { cn } from "@/lib/utils";

export default function ChatComponent() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [tableData, setTableData] = useState<TableRow[] | null>(null);
  const [summaryData, setSummaryData] = useState<any>(null);
  const [forecastData, setForecastData] = useState<any>(null);
  const [streamContent, setStreamContent] = useState("");
  const [showSidebar, setShowSidebar] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    document.body.style.overflow = "hidden";
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

    // Only show sidebar if we have data to display
    if (tableData || summaryData || forecastData) {
      setShowSidebar(true);
    }

    // Clear previous results
    setTableData(null);
    setSummaryData(null);
    setForecastData(null);

    const formData = new FormData();
    formData.append("prompt", prompt);
    if (attachedFile) formData.append("file", attachedFile);

    // Temp assistant message placeholder
    setMessages((prev) => [
      ...prev,
      { role: "assistant", content: "", timestamp: new Date() },
    ]);

    try {
      const response = await fetch("http://localhost:8000/process", {
        method: "POST",
        body: formData,
      });

      // Check if the response is not ok (status code outside the range 200-299)
      if (!response.ok) {
        let errorMessage = `Error: Server responded with status ${response.status}`;

        try {
          const errorData = await response.json();

          if (errorData.detail && Array.isArray(errorData.detail)) {
            // Format validation errors in a user-friendly way
            const errors = errorData.detail.map((error: any) => {
              // Handle missing file error specifically
              if (error.type === "missing" && error.loc.includes("file")) {
                return "Please upload a file to analyze.";
              }

              // Format other validation errors
              const field = error.loc[error.loc.length - 1];
              return `${error.msg} for ${field}`;
            });

            errorMessage = errors.join("\n");
          } else if (typeof errorData.detail === "string") {
            errorMessage = errorData.detail;
          }
        } catch (parseError) {
          // If we can't parse the error response as JSON, use the status text
          errorMessage = `Error: ${
            response.statusText || "Something went wrong"
          }`;
        }

        setMessages((prev) => {
          const updated = [...prev];
          updated[updated.length - 1] = {
            role: "assistant",
            content: errorMessage,
            timestamp: new Date(),
          };
          return updated;
        });

        setLoading(false);
        setStreamContent("");
        return;
      }

      const reader = response.body?.getReader();
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
                  const { operation, data } = parsed.content;

                  if (operation === "summarize") {
                    setSummaryData(data);
                    setShowSidebar(true);
                  } else if (operation === "table") {
                    setTableData(data);
                    setShowSidebar(true);
                  } else if (operation === "forecast") {
                    setForecastData(data);
                    setShowSidebar(true);
                  }

                  fullContent += parsed.message || "";
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

  const DataView = () => (
    <div className="space-y-6">
      {tableData && <DataTable data={tableData} />}
      {summaryData && <DataSummary data={summaryData} />}
      {forecastData && <ForecastResults data={forecastData} />}
    </div>
  );

  const hasData = tableData || summaryData || forecastData;
  const hasMessages = messages.length > 0;

  return (
    <div className="flex h-screen text-gray-100 overflow-hidden w-full">
      {/* Main Chat Area */}
      <div
        className={cn(
          "flex flex-col flex-1 h-full transition-all duration-300 ease-in-out ",
          showSidebar && hasData ? "lg:pr-[400px]" : ""
        )}
      >
        {/* Chat Header */}
        <div className="border-b border-gray-800 py-3 bg-gray-950 px-4 flex items-center justify-center">
          <div className="flex items-center gap-2 ">
            <Sparkles className="h-5 w-5 text-blue-400" />
            <h1 className="text-xl font-semibold">DataPrompt</h1>
          </div>
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
          "fixed top-0 right-0 h-full w-[400px] bg-gray-900 border-l border-gray-800 transition-all duration-300 ease-in-out transform",
          showSidebar && hasData ? "translate-x-0" : "translate-x-full"
        )}
      >
        <div className="h-full flex flex-col">
          <div className="border-b border-gray-800 p-4 flex justify-between items-center">
            <div className="flex items-center gap-2">
              <BarChart className="h-5 w-5 text-blue-400" />
              <h2 className="font-semibold">Data Analysis</h2>
            </div>
            <button
              onClick={() => setShowSidebar(false)}
              className="p-1 rounded-md hover:bg-gray-800 transition-colors"
              aria-label="Close sidebar"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-4">
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

// import { useState, useEffect } from "react";
// import MessageList from "./chat/MessageList";
// import ChatInput from "./chat/ChatInput";
// import DataTable from "./chat/DataTable";
// import DataSummary from "./chat/DataSummary";
// import ForecastResults from "./chat/ForecastResults";
// import { Message, TableRow } from "./chat/types";

// export default function ChatComponent() {
//   const [messages, setMessages] = useState<Message[]>([]);
//   const [loading, setLoading] = useState(false);
//   const [file, setFile] = useState<File | null>(null);
//   const [tableData, setTableData] = useState<TableRow[] | null>(null);
//   const [summaryData, setSummaryData] = useState<any>(null);
//   const [forecastData, setForecastData] = useState<any>(null);
//   const [streamContent, setStreamContent] = useState("");
//   const [showSidebar, setShowSidebar] = useState(false);

//   useEffect(() => {
//     document.body.style.overflow = "hidden";
//     return () => {
//       document.body.style.overflow = "auto";
//     };
//   }, []);

//   const processData = async (prompt: string) => {
//     if (!prompt.trim()) return;

//     setMessages((prev) => [
//       ...prev,
//       { role: "user", content: prompt, timestamp: new Date() },
//     ]);

//     setLoading(true);
//     setStreamContent("");
//     setShowSidebar(true);

//     // Clear previous results
//     setTableData(null);
//     setSummaryData(null);
//     setForecastData(null);

//     const formData = new FormData();
//     formData.append("prompt", prompt);
//     if (file) formData.append("file", file); // ✅ only append if exists

//     // Temp assistant message placeholder
//     setMessages((prev) => [
//       ...prev,
//       { role: "assistant", content: "", timestamp: new Date() },
//     ]);

//     try {
//       const response = await fetch("http://localhost:8000/process", {
//         method: "POST",
//         body: formData,
//       });
//       const reader = response.body?.getReader();
//       if (!reader) throw new Error("No reader");

//       let fullContent = "";
//       while (true) {
//         const { done, value } = await reader.read();
//         if (done) break;
//         const lines = new TextDecoder().decode(value).split("\n");

//         for (const line of lines) {
//           if (line.startsWith("data: ")) {
//             const data = line.slice(6);
//             if (data === "[DONE]") {
//               setMessages((prev) => {
//                 const updated = [...prev];
//                 updated[updated.length - 1] = {
//                   role: "assistant",
//                   content: fullContent,
//                   timestamp: new Date(),
//                 };
//                 return updated;
//               });
//             } else {
//               try {
//                 const parsed = JSON.parse(data);
//                 if (parsed.content) {
//                   const { operation, data } = parsed.content;

//                   if (operation === "summarize") {
//                     setSummaryData(data);
//                   } else if (operation === "table") {
//                     setTableData(data);
//                   } else if (operation === "forecast") {
//                     setForecastData(data);
//                   }

//                   fullContent += parsed.message || "";
//                   setStreamContent(fullContent);
//                 }
//               } catch (e) {
//                 console.error("Parsing error:", e);
//               }
//             }
//           }
//         }
//       }
//     } catch (err: any) {
//       setMessages((prev) => {
//         const updated = [...prev];
//         updated[updated.length - 1] = {
//           role: "assistant",
//           content: `Error: ${err.message}`,
//           timestamp: new Date(),
//         };
//         return updated;
//       });
//     } finally {
//       setLoading(false);
//       setStreamContent("");
//     }
//   };

//   const DataView = () => (
//     <div className="space-y-4">
//       {tableData && <DataTable data={tableData} />}
//       {summaryData && <DataSummary data={summaryData} />}
//       {forecastData && <ForecastResults data={forecastData} />}
//     </div>
//   );

//   return (
//     <div className="flex h-screen bg-[#1A1A1A] text-white w-full overflow-hidden">
//       <h2 className="text-2xl font-bold mb-4 text-center">
//         Chat with DataPrompt
//       </h2>
//       <div
//         className={`flex flex-col flex-1 ${
//           showSidebar ? "lg:w-2/3" : "w-full"
//         }`}
//       >
//         <div className="flex-1 overflow-y-auto px-4">
//           <MessageList
//             messages={messages}
//             isStreaming={!!streamContent}
//             streamContent={streamContent}
//           />
//         </div>
//         <ChatInput
//           onSend={processData}
//           loading={loading}
//           file={file}
//           onFileChange={setFile}
//         />
//       </div>

//       {showSidebar && (tableData || summaryData || forecastData) && (
//         <div className="hidden lg:block w-1/3 bg-[#222222] p-4 overflow-y-auto border-l border-gray-800">
//           <div className="flex justify-between items-center mb-2">
//             <h2 className="text-lg font-semibold text-[#2A9FD6]">
//               Data Analysis
//             </h2>
//             <button
//               onClick={() => setShowSidebar(false)}
//               className="text-white"
//             >
//               ✕
//             </button>
//           </div>
//           <DataView />
//         </div>
//       )}

//       {!showSidebar && (tableData || summaryData || forecastData) && (
//         <button
//           onClick={() => setShowSidebar(true)}
//           className="fixed bottom-24 right-4 bg-[#2A9FD6] text-white p-3 rounded-full shadow"
//           title="Show Data Analysis"
//         >
//           📊
//         </button>
//       )}
//     </div>
//   );
// }
