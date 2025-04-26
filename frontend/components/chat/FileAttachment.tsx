"use client";

import { File, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { formatFileSize } from "@/lib/utils";

interface FileAttachmentProps {
  file: {
    name: string;
    type: string;
    size: number;
  };
  onRemove?: () => void;
  showRemove?: boolean;
}

export default function FileAttachment({
  file,
  onRemove,
  showRemove = true,
}: FileAttachmentProps) {
  // Get file extension
  const extension = file.name.split(".").pop()?.toUpperCase() || "";

  return (
    <div className="flex items-center gap-2 p-2 bg-white border border-gray-300 rounded-md w-fit max-w-full shadow-sm shadow-blue-400">
      <div className="flex-shrink-0 w-8 h-8 bg-gray-200 rounded flex items-center justify-center text-gray-600">
        <File className="h-4 w-4" />
      </div>

      <div className="min-w-0 flex-1">
        <p
          className="text-sm font-medium text-gray-800 truncate"
          title={file.name}
        >
          {file.name}
        </p>
        <p className="text-xs text-gray-500">
          {extension} • {formatFileSize(file.size)}
        </p>
      </div>

      {showRemove && onRemove && (
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={onRemove}
          className="h-6 w-6 p-0 rounded-full text-gray-500 hover:bg-gray-200"
        >
          <span className="sr-only">Remove file</span>
          <X className="h-4 w-4" />
        </Button>
      )}
    </div>
  );
}
