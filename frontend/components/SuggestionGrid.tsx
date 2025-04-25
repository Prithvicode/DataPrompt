"use client";

import { cn } from "@/lib/utils";
import { Card } from "./CardComponent";

interface SuggestionGridProps {
  suggestions: string[];
  onSelect: (suggestion: string) => void;
  columns?: 1 | 2 | 3 | 4;
  className?: string;
}

export function SuggestionGrid({
  suggestions,
  onSelect,
  columns = 2,
  className,
}: SuggestionGridProps) {
  const gridColumns = {
    1: "grid-cols-1",
    2: "grid-cols-1 sm:grid-cols-2",
    3: "grid-cols-1 sm:grid-cols-3",
    4: "grid-cols-1 sm:grid-cols-2 md:grid-cols-4",
  };

  return (
    <div className={cn("grid gap-4", gridColumns[columns], className)}>
      {suggestions.map((suggestion, i) => (
        <Card
          key={i}
          clickable
          hoverable
          onClick={() => onSelect(suggestion)}
          className="shadow-sm hover:shadow-lg text-left border border-gray-200 rounded-lg transition-all duration-300 ease-in-out hover:bg-gray-50"
        >
          <p className="text-gray-800 p-3">{suggestion}</p>
        </Card>
      ))}
    </div>
  );
}
