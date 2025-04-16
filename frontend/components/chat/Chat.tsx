import { useState, useRef, useEffect } from "react";
import { Message } from "./types";
import MessageList from "./MessageList";
import ChatInput from "./ChatInput";

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const handleSendMessage = async (content: string) => {
    if (!content.trim()) return;

    const userMessage: Message = {
      role: "user",
      content,
      timestamp: new Date(),
    };

    const tempAssistantMessage: Message = {
      role: "assistant",
      content: "",
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage, tempAssistantMessage]);
    setIsStreaming(true);

    try {
      abortControllerRef.current = new AbortController();

      // Create FormData for the request
      const formData = new FormData();
      formData.append("prompt", content);
      if (file) {
        formData.append("file", file);
      }

      const response = await fetch("http://localhost:8000/process", {
        method: "POST",
        body: formData,
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Handle streaming response
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let accumulatedContent = "";

      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value);
          const lines = chunk.split("\n");

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              const data = line.slice(6);
              if (data === "[DONE]") {
                break;
              }

              try {
                const parsed = JSON.parse(data);
                if (parsed.content) {
                  accumulatedContent += parsed.content;
                  setMessages((prev) => {
                    const newMessages = [...prev];
                    newMessages[newMessages.length - 1] = {
                      role: "assistant",
                      content: accumulatedContent,
                      timestamp: new Date(),
                    };
                    return newMessages;
                  });
                }
              } catch (e) {
                console.error("Error parsing streaming data:", e);
              }
            }
          }
        }
      }
    } catch (error: any) {
      setMessages((prev) => {
        const newMessages = [...prev];
        newMessages[newMessages.length - 1] = {
          role: "assistant",
          content: "Sorry, I encountered an error. Please try again.",
          timestamp: new Date(),
        };
        return newMessages;
      });

      if (error.name === "AbortError") {
        console.log("Request aborted");
      } else {
        console.error("Error sending message:", error);
      }
    } finally {
      setIsStreaming(false);
      abortControllerRef.current = null;
    }
  };

  const handleStopStreaming = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  };

  useEffect(() => {
    // Prevent body scrolling when component mounts
    document.body.style.overflow = "hidden";

    // Cleanup function to restore body scrolling when component unmounts
    return () => {
      document.body.style.overflow = "auto";
    };
  }, []);

  return (
    <div className="flex flex-col h-screen bg-[#1A1A1A] text-white">
      {/* Header */}
      <header className="flex-none border-b border-gray-700 bg-[#1A1A1A] py-4 px-6">
        <div className="max-w-5xl mx-auto">
          <h1 className="text-xl font-semibold text-[#2A9FD6]">
            Data Analysis Chat
          </h1>
        </div>
      </header>

      {/* Main content area */}
      <div className="flex-1 overflow-hidden flex flex-col">
        <style jsx global>{`
          /* Custom scrollbar styles */
          ::-webkit-scrollbar {
            width: 8px;
            height: 8px;
          }

          ::-webkit-scrollbar-track {
            background: transparent;
          }

          ::-webkit-scrollbar-thumb {
            background: #4a5568;
            border-radius: 4px;
          }

          ::-webkit-scrollbar-thumb:hover {
            background: #718096;
          }

          /* Firefox scrollbar styles */
          * {
            scrollbar-width: thin;
            scrollbar-color: #4a5568 transparent;
          }
        `}</style>

        {messages.length === 0 ? (
          // Empty state with centered input
          <div className="flex-1 flex flex-col items-center justify-center px-4">
            <div className="text-center max-w-2xl mb-8">
              <h2 className="text-2xl font-bold mb-4 text-white">
                Welcome to Data Analysis Chat
              </h2>
              <p className="text-gray-300 mb-6">
                Upload a CSV file and start asking questions about your data.
                Our AI will help you analyze and visualize your information.
              </p>
              <div className="bg-[#2A2A2A] p-6 rounded-xl border border-[#3A3A3A] shadow-lg">
                <h3 className="text-sm font-semibold text-[#2A9FD6] mb-4">
                  Try these examples:
                </h3>
                <ul className="text-sm text-gray-300 space-y-2 text-left">
                  <li>• "What are the top 5 values in column X?"</li>
                  <li>• "Show me a summary of the data"</li>
                  <li>• "What's the correlation between columns A and B?"</li>
                </ul>
              </div>
            </div>

            {/* Centered input */}
            <div className="w-full max-w-2xl">
              <ChatInput
                onSend={handleSendMessage}
                loading={isStreaming}
                file={file}
                onFileChange={setFile}
              />
            </div>
          </div>
        ) : (
          // Chat with messages
          <>
            {/* Messages area - scrollable */}
            <div className="flex-1 overflow-y-auto">
              <MessageList messages={messages} isStreaming={isStreaming} />
            </div>

            {/* Input area - fixed at bottom */}
            <div className="flex-none border-t border-gray-700 bg-[#1A1A1A] py-4">
              <div className="max-w-5xl mx-auto px-4">
                <ChatInput
                  onSend={handleSendMessage}
                  loading={isStreaming}
                  file={file}
                  onFileChange={setFile}
                />
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
