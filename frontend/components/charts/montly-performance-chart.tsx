"use client";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

export function MonthlyPerformanceChart({ data }: { data: any[] }) {
  return (
    <div className="h-[400px]">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="month"
            tick={{ fontSize: 12 }}
            angle={-45}
            textAnchor="end"
          />
          <YAxis />
          <Tooltip
            formatter={(value: number) =>
              new Intl.NumberFormat("en-US", {
                style: "currency",
                currency: "USD",
              }).format(value)
            }
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="revenue"
            stroke="#4a90e2"
            name="Revenue"
            strokeWidth={2}
          />
          <Line
            type="monotone"
            dataKey="profit"
            stroke=" #66bb6a"
            name="Profit"
            strokeWidth={2}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
