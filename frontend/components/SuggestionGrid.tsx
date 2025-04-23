// components/ui/SuggestionGrid.tsx
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
    <div className={cn("grid gap-2", gridColumns[columns], className)}>
      {suggestions.map((suggestion, i) => (
        <Card
          key={i}
          clickable
          hoverable
          onClick={() => onSelect(suggestion)}
          className="text-left"
        >
          {suggestion}
        </Card>
      ))}
    </div>
  );
}
