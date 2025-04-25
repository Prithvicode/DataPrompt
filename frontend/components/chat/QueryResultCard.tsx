import React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { BarChart3, FileSearch, Search } from "lucide-react";

interface QueryResultCardProps {
  value: number;
  note?: string;
  currency?: string; // Optional currency, e.g., "$"
}

const QueryResultCard: React.FC<QueryResultCardProps> = ({ value, note }) => {
  return (
    <Card className="relative overflow-hidden rounded-2xl border border-gray-300 shadow-lg bg-white hover:shadow-xl transition-shadow">
      {/* Decorative gradient stripegit */}
      <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-400 via-blue-500 to-blue-600" />

      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <Search className="w-5 h-5 text-blue-600" />
          Query Result
        </CardTitle>
      </CardHeader>

      <CardContent className="pt-0">
        <p className="text-5xl font-extrabold text-black">
          {value.toLocaleString(undefined, {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
          })}
        </p>
        {note && (
          <p className="text-sm mt-3 text-gray-700">
            Query result based on prompt:{" "}
            <span className="text-blue-500 text-lg italic">"{note}"</span>
          </p>
        )}
      </CardContent>
    </Card>
  );
};

export default QueryResultCard;
