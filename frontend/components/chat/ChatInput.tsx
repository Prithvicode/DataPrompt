"use client";

import type React from "react";
import { useState, useRef } from "react";
import { Send, Paperclip, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import FileAttachment from "./FileAttachment";

interface ChatInputProps {
  onSend: (message: string, file: File | null) => void;
  loading: boolean;
  file: File | null;
  onFileChange: (file: File | null) => void;
}

export default function ChatInput({
  onSend,
  loading,
  file,
  onFileChange,
}: ChatInputProps) {
  const [message, setMessage] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() || file) {
      onSend(message, file);
      setMessage("");
      onFileChange(null);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0] || null;
    onFileChange(selectedFile);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="relative mx-auto max-w-3xl max-h-[400px] border border-accent-foreground rounded-md p-2"
    >
      {file && (
        <div className="mb-2">
          <FileAttachment
            file={{
              name: file.name,
              type: file.type,
              size: file.size,
            }}
            onRemove={() => onFileChange(null)}
          />
        </div>
      )}

      <div className="relative flex items-center">
        <Textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={file ? "Add a message..." : "Ask about your data..."}
          className="min-h-[56px]  max-h-[200px] custom-scrollbar w-full resize-none py-3 pr-24 bg-gray-800 border-gray-700 focus-visible:ring-blue-500 text-white placeholder:text-gray-400"
          rows={1}
          disabled={loading}
        />

        <div className="absolute right-2 bottom-2 flex gap-1">
          <Button
            type="button"
            size="icon"
            variant="ghost"
            className="h-8 w-8 rounded-full text-gray-400 hover:text-white hover:bg-gray-700"
            onClick={() => fileInputRef.current?.click()}
            title="Attach file"
          >
            <Paperclip className="h-5 w-5" />
          </Button>

          <Button
            type="submit"
            size="icon"
            className="h-8 w-8 rounded-full bg-blue-600 hover:bg-blue-700 text-white disabled:bg-gray-700 disabled:text-gray-400"
            disabled={loading || (!message.trim() && !file)}
          >
            {loading ? (
              <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
              <Send className="h-5 w-5" />
            )}
          </Button>
        </div>
      </div>

      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        className="hidden"
        accept=".csv,.xlsx,.json"
      />
    </form>
  );
}

// import { useState, useRef } from "react";
// import { AttachmentIcon, SendIcon } from "./Icons";

// interface ChatInputProps {
//   onSend: (prompt: string) => void;
//   loading: boolean;
//   file: File | null;
//   onFileChange: (file: File | null) => void;
// }

// export default function ChatInput({
//   onSend,
//   loading,
//   file,
//   onFileChange,
// }: ChatInputProps) {
//   const [prompt, setPrompt] = useState("");
//   const textareaRef = useRef<HTMLTextAreaElement>(null);

//   const handleSubmit = (e: React.FormEvent | React.KeyboardEvent) => {
//     e.preventDefault();
//     if (prompt.trim() && !loading) {
//       onSend(prompt);
//       setPrompt("");
//     }
//   };

//   const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
//     if (e.key === "Enter" && !e.shiftKey) handleSubmit(e);
//   };

//   const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
//     onFileChange(e.target.files?.[0] || null);
//   };

//   const resizeTextarea = () => {
//     const textarea = textareaRef.current;
//     if (textarea) {
//       textarea.style.height = "auto";
//       textarea.style.height = Math.min(textarea.scrollHeight, 200) + "px";
//     }
//   };

//   const isSendDisabled = loading || !prompt.trim();

//   return (
//     <div className="bg-gradient-to-t from-[#1A1A1A] to-transparent pt-6 pb-4">
//       <form onSubmit={handleSubmit} className="max-w-5xl mx-auto px-4">
//         <div className="relative flex items-end bg-[#2A2A2A] rounded-xl border border-[#3A3A3A] shadow-lg">
//           <textarea
//             ref={textareaRef}
//             rows={1}
//             value={prompt}
//             onChange={(e) => {
//               setPrompt(e.target.value);
//               resizeTextarea();
//             }}
//             onKeyDown={handleKeyDown}
//             disabled={loading}
//             placeholder={
//               loading
//                 ? "AI is thinking..."
//                 : file
//                 ? "Ask a question about your data..."
//                 : "Upload a CSV file first..."
//             }
//             className="flex-1 max-h-[200px] p-4 pr-20 bg-transparent text-white placeholder-gray-400 resize-none focus:outline-none disabled:opacity-50 rounded-xl"
//           />

//           <div className="absolute bottom-2 right-2 flex items-center gap-x-2">
//             <input
//               type="file"
//               id="fileUpload"
//               onChange={handleFileChange}
//               className="hidden"
//               disabled={loading}
//               accept=".csv"
//             />
//             <label
//               htmlFor="fileUpload"
//               className={`p-2 rounded-md ${
//                 loading
//                   ? "text-gray-500 cursor-not-allowed"
//                   : file
//                   ? "text-[#2A9FD6] hover:text-white hover:bg-[#2A9FD6]"
//                   : "text-gray-400 hover:text-white hover:bg-[#3A3A3A] cursor-pointer"
//               }`}
//               title={file ? "Change file" : "Upload CSV file"}
//             >
//               <AttachmentIcon />
//             </label>

//             <button
//               type="submit"
//               disabled={isSendDisabled}
//               title="Send message"
//               className={`p-2 rounded-md ${
//                 isSendDisabled
//                   ? "text-gray-500 cursor-not-allowed"
//                   : "text-[#2A9FD6] hover:text-white hover:bg-[#2A9FD6]"
//               }`}
//             >
//               {loading ? (
//                 <div className="w-5 h-5 border-2 border-current border-t-transparent rounded-full animate-spin" />
//               ) : (
//                 <SendIcon />
//               )}
//             </button>
//           </div>
//         </div>

//         <div className="mt-3 px-4 py-2 bg-[#2A2A2A] rounded-lg text-sm text-gray-300 border border-[#3A3A3A] flex items-center justify-between">
//           {file ? (
//             <>
//               <div className="flex items-center truncate">
//                 <svg
//                   className="h-5 w-5 mr-2 text-[#2A9FD6]"
//                   fill="none"
//                   stroke="currentColor"
//                   viewBox="0 0 24 24"
//                 >
//                   <path
//                     strokeLinecap="round"
//                     strokeLinejoin="round"
//                     strokeWidth={2}
//                     d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414V19a2 2 0 01-2 2z"
//                   />
//                 </svg>
//                 <span className="truncate max-w-[200px] sm:max-w-[300px] md:max-w-[400px]">
//                   {file.name}
//                 </span>
//               </div>
//               <button
//                 onClick={() => onFileChange(null)}
//                 className="text-gray-400 hover:text-white p-1 rounded-full hover:bg-[#3A3A3A]"
//               >
//                 <svg
//                   className="h-4 w-4"
//                   fill="none"
//                   stroke="currentColor"
//                   viewBox="0 0 24 24"
//                 >
//                   <path
//                     strokeLinecap="round"
//                     strokeLinejoin="round"
//                     strokeWidth={2}
//                     d="M6 18L18 6M6 6l12 12"
//                   />
//                 </svg>
//               </button>
//             </>
//           ) : (
//             <>
//               <svg
//                 className="h-5 w-5 mr-2 text-yellow-500"
//                 fill="none"
//                 stroke="currentColor"
//                 viewBox="0 0 24 24"
//               >
//                 <path
//                   strokeLinecap="round"
//                   strokeLinejoin="round"
//                   strokeWidth={2}
//                   d="M12 9v2m0 4h.01M5.062 21h13.876c1.54 0 2.5-1.667 1.73-3L13.73 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.722 3z"
//                 />
//               </svg>
//               <span>Please upload a CSV file to analyze</span>
//             </>
//           )}
//         </div>
//       </form>
//     </div>
//   );
// }
