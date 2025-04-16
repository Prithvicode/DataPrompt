import { useEffect, useRef } from "react";
import { Message } from "./types";
import MessageBubble from "./MessageBubble";

interface MessageListProps {
  messages: Message[];
  isStreaming?: boolean;
  streamContent?: string;
}

export default function MessageList({
  messages,
  isStreaming = false,
  streamContent = "",
}: MessageListProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamContent]);

  if (!messages.length) {
    return (
      <div className="flex-1 flex items-center justify-center min-h-[400px] text-gray-400">
        <div className="text-center max-w-md px-4">
          <div className="mb-6">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-16 w-16 mx-auto text-[#2A9FD6]"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
              />
            </svg>
          </div>
          <h2 className="text-2xl font-bold mb-3 text-white">
            Welcome to Data Analysis Chat
          </h2>
          <p className="text-gray-300 mb-6">
            Upload a CSV file and start asking questions about your data. Our AI
            will help you analyze and visualize your information.
          </p>
          <div className="bg-[#2A2A2A] p-4 rounded-lg border border-[#3A3A3A]">
            <h3 className="text-sm font-semibold text-[#2A9FD6] mb-2">
              Try these examples:
            </h3>
            <ul className="text-sm text-gray-300 space-y-1">
              <li>• "What are the top 5 values in column X?"</li>
              <li>• "Show me a summary of the data"</li>
              <li>• "What's the correlation between columns A and B?"</li>
            </ul>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto py-6 scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
      <div className="max-w-5xl mx-auto px-4">
        {messages.map((message, index) => (
          <MessageBubble
            key={index}
            message={message}
            isStreaming={isStreaming && index === messages.length - 1}
            streamContent={
              isStreaming && index === messages.length - 1
                ? streamContent
                : undefined
            }
          />
        ))}
        <div ref={messagesEndRef} className="h-4" />
      </div>
    </div>
  );
}
