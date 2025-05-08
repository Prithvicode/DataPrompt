import type { Message } from "./types";
import { cn } from "@/lib/utils";
import { User, Bot } from "lucide-react";
import FileAttachment from "./FileAttachment";
import { Loader } from "../Loader";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import "highlight.js/styles/github.css";

import markdownComponents from "./MarkDownComponent";

interface MessageListProps {
  messages: Message[];
  isStreaming: boolean;
  streamContent: string;
}

export default function MessageList({
  messages,
  isStreaming,
  streamContent,
}: MessageListProps) {
  const formatErrorMessage = (content: string) => {
    return (
      <div className="rounded-md p-3 text-red-700 whitespace-pre-wrap">
        {content}
      </div>
    );
  };

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      {messages.map((message, index) => {
        const isLastMessage = index === messages.length - 1;
        const isUser = message.role === "user";
        const isAssistant = message.role === "assistant";
        const showStreamingContent =
          isLastMessage && isAssistant && isStreaming;

        return (
          <div
            key={index}
            className={cn(
              "flex gap-4 w-full",
              isUser ? "flex-row-reverse" : "flex-row"
            )}
          >
            {/* Avatar */}
            <div
              className={cn(
                "flex-shrink-0 rounded-full w-8 h-8 flex items-center justify-center",
                isAssistant
                  ? "bg-blue-200 text-blue-600"
                  : "bg-gray-300 text-gray-700"
              )}
            >
              {isAssistant ? (
                <Bot className="h-5 w-5" />
              ) : (
                <User className="h-5 w-5" />
              )}
            </div>

            {/* Message content */}
            <div
              className={cn(
                "space-y-2 max-w-[80%]",
                isUser ? "items-end" : "items-start"
              )}
            >
              {/* Sender name */}
              <div
                className={cn(
                  "font-medium",
                  isUser ? "text-right" : "text-left"
                )}
              >
                {isAssistant ? "DataPrompt" : "You"}
              </div>

              {/* File attachment */}
              {message.file && (
                <div className={cn(isUser ? "ml-auto" : "mr-auto")}>
                  <FileAttachment file={message.file} showRemove={false} />
                </div>
              )}

              {/* Message bubble */}
              <div
                className={cn(
                  "rounded-lg p-3",
                  isUser
                    ? "bg-blue-100 ml-auto text-blue-800"
                    : message.error
                    ? "bg-red-100 border border-red-500"
                    : "bg-gray-200 mr-auto text-gray-800"
                )}
              >
                {showStreamingContent ? (
                  <div className="flex flex-col gap-1">
                    <div className="prose prose-sm leading-relaxed max-w-none">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        rehypePlugins={[rehypeHighlight]}
                        components={markdownComponents}
                      >
                        {streamContent}
                      </ReactMarkdown>
                    </div>
                    <div className="flex justify-end items-center gap-2">
                      <span className="text-sm text-gray-600">Thinking</span>
                      <span className="h-2 w-2 rounded-full bg-gray-400 animate-ping" />
                    </div>
                  </div>
                ) : typeof message.content === "string" ? (
                  message.error ? (
                    formatErrorMessage(message.content)
                  ) : (
                    <div className="prose prose-sm max-w-none">
                      <ReactMarkdown
                        remarkPlugins={[remarkGfm]}
                        rehypePlugins={[rehypeHighlight]}
                        components={markdownComponents}
                      >
                        {message.content}
                      </ReactMarkdown>
                    </div>
                  )
                ) : (
                  <span>{message.content}</span>
                )}
              </div>

              {/* Loader */}
              {isStreaming && isAssistant && isLastMessage && (
                <Loader loading={isStreaming} />
              )}

              {/* Timestamp */}
              <div
                className={cn(
                  "text-xs text-gray-500",
                  isUser ? "text-right" : "text-left"
                )}
              >
                {new Date(message.timestamp).toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
