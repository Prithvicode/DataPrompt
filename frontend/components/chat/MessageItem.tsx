import { Message } from "./types";

interface MessageItemProps {
  message: Message;
  isStreaming?: boolean;
}

export default function MessageItem({
  message,
  isStreaming = false,
}: MessageItemProps) {
  return (
    <div
      className={`flex items-start space-x-3 ${
        message.role === "user" ? "justify-end" : "justify-start"
      }`}
    >
      {message.role === "assistant" && (
        <div className="w-8 h-8 rounded-full bg-[#2A9FD6] flex items-center justify-center">
          <span className="text-sm">AI</span>
        </div>
      )}
      <div
        className={`max-w-[80%] p-4 rounded-2xl ${
          message.role === "user"
            ? "bg-[#2A9FD6] text-white"
            : "bg-[#3C3C3C] text-gray-300"
        }`}
      >
        <pre className="whitespace-pre-wrap font-sans">
          {message.content}
          {isStreaming && <span className="animate-pulse">▋</span>}
        </pre>
        {!isStreaming && (
          <div className="text-xs opacity-50 mt-1">
            {message.timestamp.toLocaleTimeString()}
          </div>
        )}
      </div>
      {message.role === "user" && (
        <div className="w-8 h-8 rounded-full bg-[#444444] flex items-center justify-center">
          <span className="text-sm">U</span>
        </div>
      )}
    </div>
  );
}
