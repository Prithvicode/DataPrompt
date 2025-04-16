import { useState } from "react";
import { Message } from "./types";
import { ClipboardIcon, CheckIcon } from "./Icons";

interface MessageBubbleProps {
  message: Message;
  isStreaming?: boolean;
  streamContent?: string;
}

export default function MessageBubble({
  message,
  isStreaming = false,
  streamContent,
}: MessageBubbleProps) {
  const [isCopied, setIsCopied] = useState(false);

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setIsCopied(true);
      setTimeout(() => setIsCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy text: ", err);
    }
  };

  return (
    <div
      className={`group flex items-start gap-x-4 py-6 ${
        message.role === "user" ? "bg-transparent" : "bg-[#2A2A2A]"
      }`}
    >
      <div className="flex-shrink-0">
        {message.role === "assistant" ? (
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#2A9FD6] to-[#1E8BC0] flex items-center justify-center shadow-md">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-5 w-5 text-white"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
              />
            </svg>
          </div>
        ) : (
          <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#444444] to-[#333333] flex items-center justify-center shadow-md">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-5 w-5 text-white"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
              />
            </svg>
          </div>
        )}
      </div>

      <div className="flex-1 min-w-0">
        <div className="prose prose-invert max-w-none">
          <div className="bg-[#2A2A2A] rounded-lg p-4 shadow-sm border border-[#3A3A3A]">
            <pre className="whitespace-pre-wrap font-sans text-base text-gray-200">
              {streamContent || message.content}
              {isStreaming && <span className="animate-pulse">▋</span>}
            </pre>
          </div>
        </div>

        {!isStreaming && (
          <div className="mt-2 flex items-center gap-x-2 text-xs text-gray-400">
            <span>{message.timestamp.toLocaleTimeString()}</span>
            {message.role === "assistant" && (
              <button
                onClick={copyToClipboard}
                className="opacity-0 group-hover:opacity-100 transition-opacity duration-200 p-1 hover:bg-[#3C3C3C] rounded"
                title="Copy to clipboard"
              >
                {isCopied ? <CheckIcon /> : <ClipboardIcon />}
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
