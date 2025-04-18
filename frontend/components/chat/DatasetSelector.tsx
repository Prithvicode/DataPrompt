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
        className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-gray-800 hover:bg-gray-700 transition-colors text-sm"
      >
        <span className="max-w-[150px] truncate">
          {activeDataset ? activeDataset.filename : "Select dataset"}
        </span>
        {isOpen ? (
          <ChevronUp className="h-4 w-4" />
        ) : (
          <ChevronDown className="h-4 w-4" />
        )}
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-1 w-64 bg-gray-800 rounded-md shadow-lg z-10 py-1">
          {datasets.map((dataset) => (
            <button
              key={dataset.id}
              onClick={() => {
                onSelect(dataset.id);
                setIsOpen(false);
              }}
              className={`w-full text-left px-4 py-2 text-sm hover:bg-gray-700 transition-colors flex flex-col ${
                dataset.id === activeDatasetId ? "bg-gray-700" : ""
              }`}
            >
              <span className="font-medium truncate">{dataset.filename}</span>
              <span className="text-xs text-gray-400">
                {dataset.row_count} rows • {dataset.columns.length} columns
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
