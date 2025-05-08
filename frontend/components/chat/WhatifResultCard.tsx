import React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { BarChart3 } from "lucide-react";

interface WhatIfResultCardProps {
  value: number;
  note?: string;
}

const WhatIfResultCard: React.FC<WhatIfResultCardProps> = ({ value, note }) => {
  return (
    <Card className="relative overflow-hidden rounded-2xl border border-gray-300 shadow-lg bg-white hover:shadow-xl transition-shadow">
      {/* Decorative gradient stripe */}
      <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-green-400 via-green-500 to-green-600" />

      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-lg font-semibold text-gray-900 flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-green-600" />
          What-If Result
        </CardTitle>
      </CardHeader>

      <CardContent className="pt-0">
        <h2 className="text-xl font-semibold mb-3">Predicted Revenue: </h2>
        <p className="text-5xl font-extrabold text-black">
          Nrs{" "}
          {value.toLocaleString("en-IN", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
          })}
        </p>
        {note && (
          <p className="text-sm mt-3 text-gray-700">
            What-if scenario based on:{" "}
            <span className="text-green-600 text-lg italic">"{note}"</span>
          </p>
        )}
      </CardContent>
    </Card>
  );
};

export default WhatIfResultCard;
