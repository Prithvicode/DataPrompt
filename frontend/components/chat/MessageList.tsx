import type { Message } from "./types";
import { cn } from "@/lib/utils";
import { User, Bot } from "lucide-react";
import FileAttachment from "./FileAttachment";

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
    if (
      content.startsWith("Please upload a file") ||
      content.includes("Error:")
    ) {
      return (
        <div className="bg-red-900/20 border border-red-800/50 rounded-md p-3 text-red-200">
          <div className="font-medium text-red-300 mb-1">Error</div>
          {content}
        </div>
      );
    }
    return content;
  };

  return (
    <div className="space-y-6 max-w-3xl mx-auto ">
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
                  ? "bg-blue-900/30 text-blue-400"
                  : "bg-gray-800 text-gray-300"
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

              {/* File attachment if present */}
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
                    ? "bg-blue-950 text-white ml-auto"
                    : "text-gray-200 mr-auto"
                )}
              >
                {showStreamingContent ? (
                  <>
                    {streamContent || "..."}
                    <div className="typing-indicator mt-1 inline-flex">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  </>
                ) : typeof message.content === "string" &&
                  message.content.includes("Error") ? (
                  formatErrorMessage(message.content)
                ) : (
                  message.content
                )}
              </div>

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

// import { useEffect, useRef } from "react";
// import { Message } from "./types";
// import MessageBubble from "./MessageBubble";

// interface MessageListProps {
//   messages: Message[];
//   isStreaming?: boolean;
//   streamContent?: string;
// }

// export default function MessageList({
//   messages,
//   isStreaming = false,
//   streamContent = "",
// }: MessageListProps) {
//   const messagesEndRef = useRef<HTMLDivElement>(null);

//   const scrollToBottom = () => {
//     messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
//   };

//   useEffect(() => {
//     scrollToBottom();
//   }, [messages, streamContent]);

//   // if (!messages.length) {
//   //   return (
//   //     <div className="flex-1 flex items-center justify-center min-h-[400px] text-gray-400">
//   //       <div className="text-center max-w-md px-4">
//   //         <div className="mb-6">
//   //           <svg
//   //             xmlns="http://www.w3.org/2000/svg"
//   //             className="h-16 w-16 mx-auto text-[#2A9FD6]"
//   //             fill="none"
//   //             viewBox="0 0 24 24"
//   //             stroke="currentColor"
//   //           >
//   //             <path
//   //               strokeLinecap="round"
//   //               strokeLinejoin="round"
//   //               strokeWidth={1.5}
//   //               d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
//   //             />
//   //           </svg>
//   //         </div>
//   //         <h2 className="text-2xl font-bold mb-3 text-white">
//   //           Welcome to Data Analysis Chat
//   //         </h2>
//   //         <p className="text-gray-300 mb-6">
//   //           Upload a CSV file and start asking questions about your data. Our AI
//   //           will help you analyze and visualize your information.
//   //         </p>
//   //         <div className="bg-[#2A2A2A] p-4 rounded-lg border border-[#3A3A3A]">
//   //           <h3 className="text-sm font-semibold text-[#2A9FD6] mb-2">
//   //             Try these examples:
//   //           </h3>
//   //           <ul className="text-sm text-gray-300 space-y-1">
//   //             <li>• "What are the top 5 values in column X?"</li>
//   //             <li>• "Show me a summary of the data"</li>
//   //             <li>• "What's the correlation between columns A and B?"</li>
//   //           </ul>
//   //         </div>
//   //       </div>
//   //     </div>
//   //   );
//   // }

//   return (
//     <div className="flex-1 overflow-y-auto py-6 scrollbar-thin scrollbar-thumb-gray-700 scrollbar-track-transparent">
//       <div className="max-w-5xl mx-auto px-4">
//         {messages.map((message, index) => (
//           <MessageBubble
//             key={index}
//             message={message}
//             isStreaming={isStreaming && index === messages.length - 1}
//             streamContent={
//               isStreaming && index === messages.length - 1
//                 ? streamContent
//                 : undefined
//             }
//           />
//         ))}
//         <div ref={messagesEndRef} className="h-4" />
//       </div>
//     </div>
//   );
// }
