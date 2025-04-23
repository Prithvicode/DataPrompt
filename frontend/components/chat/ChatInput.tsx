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
