"use client";
import {
  ComposedChart,
  Bar,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

export function PromotionImpactChart({ data }: { data: any[] }) {
  return (
    <div className="h-[300px]">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart
          data={data}
          margin={{ top: 20, right: 40, left: 0, bottom: 40 }}
        >
          <XAxis
            dataKey="promotion_applied"
            tickFormatter={(value) =>
              value ? "With Promotion" : "Without Promotion"
            }
            tick={{ fontSize: 12 }}
          />
          <YAxis yAxisId="left" tick={{ fontSize: 12 }} />
          <YAxis
            yAxisId="right"
            orientation="right"
            tickFormatter={(value) => `${value}%`}
            tick={{ fontSize: 12 }}
          />
          <Tooltip
            formatter={(value: number, name: string) =>
              name === "Profit Margin (%)"
                ? `${value.toFixed(2)}%`
                : new Intl.NumberFormat("en-US", {
                    style: "currency",
                    currency: "USD",
                    maximumFractionDigits: 0,
                  }).format(value)
            }
          />
          <Legend />
          <Bar
            yAxisId="left"
            dataKey="profit"
            fill="#66bb6a" // Green for profit
            name="Profit"
            radius={[4, 4, 0, 0]}
          />
          <Bar
            yAxisId="left"
            dataKey="units_sold"
            fill="#4a90e2" // Blue for units sold
            name="Units Sold"
            radius={[4, 4, 0, 0]}
          />
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="average_profit_margin_percent"
            stroke="#f57c00" // Bright orange for margin
            name="Profit Margin (%)"
            strokeWidth={2}
            dot={{ r: 3 }}
            activeDot={{ r: 5 }}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
