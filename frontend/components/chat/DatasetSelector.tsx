"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import type { DatasetInfo } from "./types";

interface DatasetSelectorProps {
  datasets: DatasetInfo[];
  activeDatasetId: string | null;
  onSelect: (datasetId: string) => void;
}

export default function DatasetSelector({
  datasets,
  activeDatasetId,
  onSelect,
}: DatasetSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);

  const activeDataset = datasets.find((d) => d.id === activeDatasetId);

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-white hover:bg-gray-100 transition-colors text-sm text-gray-800 border border-blue-300"
      >
        <span className="max-w-[150px] truncate">
          {activeDataset ? activeDataset.filename : "Select dataset"}
        </span>
        {isOpen ? (
          <ChevronUp className="h-4 w-4 text-gray-600" />
        ) : (
          <ChevronDown className="h-4 w-4 text-gray-600" />
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-1 w-64 bg-white rounded-md shadow-lg z-10 py-1 border border-gray-300">
          {datasets.map((dataset) => (
            <button
              key={dataset.id}
              onClick={() => {
                onSelect(dataset.id);
                setIsOpen(false);
              }}
              className={`w-full text-left px-4 py-2 text-sm hover:bg-gray-100 transition-colors flex flex-col ${
                dataset.id === activeDatasetId ? "bg-gray-200" : ""
              }`}
            >
              <span className="font-medium truncate">{dataset.filename}</span>
              <span className="text-xs text-gray-500">
                {dataset.row_count} rows • {dataset.columns.length} columns
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
