"use client";

import type React from "react";
import { useState, useRef } from "react";
import { Send, Paperclip, Loader2, Plus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import FileAttachment from "./FileAttachment";

import {
  TooltipProvider,
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "../ui/tooltip";

interface ChatInputProps {
  onSend: (message: string, file: File | null) => void;
  loading: boolean;
  file: File | null;
  onFileChange: (file: File | null) => void;
  onUploadFile: (file: File) => void;
}

export default function ChatInput({
  onSend,
  loading,
  file,
  onFileChange,
  onUploadFile,
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
    if (selectedFile) {
      if (!selectedFile.name.endsWith(".csv")) {
        alert("Only .csv files are allowed.");
        return;
      } else {
        onUploadFile(selectedFile);
        onFileChange(selectedFile);
      }
    }
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="relative mx-auto max-w-3xl max-h-[400px] bg-white border border-gray-300 shadow-md rounded-md p-4"
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
          className="min-h-[56px] max-h-[200px] custom-scrollbar w-full resize-none py-3 pr-24 bg-gray-50 text-gray-900 border border-gray-300 rounded-md placeholder:text-gray-500 focus:outline-none  focus-visible:ring-blue-300 "
          rows={1}
          disabled={loading}
        />

        <div className="absolute right-2 bottom-2 flex gap-1">
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  type="button"
                  size="icon"
                  variant="ghost"
                  className="h-8 w-8 rounded-full text-gray-500 hover:bg-gray-200 border-2"
                  onClick={() => fileInputRef.current?.click()}
                >
                  <Plus className="h-5 w-5" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Upload .csv file</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>

          <Button
            type="submit"
            size="icon"
            className="h-8 w-8  rounded-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-200 disabled:text-gray-400  "
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
        accept=".csv"
      />
    </form>
  );
}
