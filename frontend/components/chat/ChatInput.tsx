import { useState, useRef } from "react";
import { AttachmentIcon, SendIcon } from "./Icons";

interface ChatInputProps {
  onSend: (prompt: string) => void;
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
  const [prompt, setPrompt] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (prompt.trim() && !loading) {
      onSend(prompt);
      setPrompt("");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const adjustTextareaHeight = () => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = "auto";
      textarea.style.height = Math.min(textarea.scrollHeight, 200) + "px";
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const uploadedFile = e.target.files ? e.target.files[0] : null;
    onFileChange(uploadedFile);
  };

  return (
    <div className="bg-gradient-to-t from-[#1A1A1A] to-transparent pt-6 pb-4">
      <form onSubmit={handleSubmit} className="max-w-5xl mx-auto px-4">
        <div className="relative flex items-end bg-[#2A2A2A] rounded-xl border border-[#3A3A3A] shadow-lg">
          <textarea
            ref={textareaRef}
            rows={1}
            placeholder={
              loading
                ? "AI is thinking..."
                : file
                ? "Ask a question about your data..."
                : "Upload a CSV file first..."
            }
            value={prompt}
            onChange={(e) => {
              setPrompt(e.target.value);
              adjustTextareaHeight();
            }}
            onKeyDown={handleKeyDown}
            disabled={loading || !file}
            className="flex-1 max-h-[200px] p-4 pr-20 bg-transparent text-white placeholder-gray-400 resize-none focus:outline-none disabled:opacity-50 rounded-xl"
          />

          <div className="absolute bottom-2 right-2 flex items-center gap-x-2">
            <input
              type="file"
              onChange={handleFileChange}
              className="hidden"
              id="fileUpload"
              disabled={loading}
              accept=".csv"
            />
            <label
              htmlFor="fileUpload"
              className={`p-2 rounded-md transition-colors duration-200 ${
                loading
                  ? "text-gray-500 cursor-not-allowed"
                  : file
                  ? "text-[#2A9FD6] hover:text-white hover:bg-[#2A9FD6]"
                  : "text-gray-400 hover:text-white hover:bg-[#3A3A3A] cursor-pointer"
              }`}
              title={file ? "Change file" : "Upload CSV file"}
            >
              <AttachmentIcon />
            </label>

            <button
              type="submit"
              disabled={loading || !prompt.trim() || !file}
              className={`p-2 rounded-md transition-colors duration-200 ${
                loading || !prompt.trim() || !file
                  ? "text-gray-500 cursor-not-allowed"
                  : "text-[#2A9FD6] hover:text-white hover:bg-[#2A9FD6]"
              }`}
              title="Send message"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-current border-t-transparent rounded-full animate-spin" />
              ) : (
                <SendIcon />
              )}
            </button>
          </div>
        </div>

        {file ? (
          <div className="mt-3 px-4 py-2 bg-[#2A2A2A] rounded-lg text-sm text-gray-300 flex items-center justify-between border border-[#3A3A3A]">
            <div className="flex items-center">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-5 w-5 mr-2 text-[#2A9FD6]"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
              <span className="truncate max-w-[200px] sm:max-w-[300px] md:max-w-[400px]">
                {file.name}
              </span>
            </div>
            <button
              type="button"
              onClick={() => onFileChange(null)}
              className="ml-2 text-gray-400 hover:text-white p-1 rounded-full hover:bg-[#3A3A3A]"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-4 w-4"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
        ) : (
          <div className="mt-3 px-4 py-2 bg-[#2A2A2A] rounded-lg text-sm text-gray-300 flex items-center border border-[#3A3A3A]">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-5 w-5 mr-2 text-yellow-500"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
            <span>Please upload a CSV file to analyze</span>
          </div>
        )}
      </form>
    </div>
  );
}
