"use client";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

export function RegionalSalesChart({ data }: { data: any[] }) {
  return (
    <div className="h-[300px]">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          margin={{ top: 20, right: 30, left: 0, bottom: 40 }}
        >
          <XAxis
            dataKey="region"
            tick={{ fontSize: 12 }}
            angle={-30}
            textAnchor="end"
          />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip
            formatter={(value: number) =>
              new Intl.NumberFormat("en-US", {
                style: "currency",
                currency: "USD",
                maximumFractionDigits: 0,
              }).format(value)
            }
          />
          <Legend />
          <Bar
            dataKey="revenue"
            fill="#4a90e2" // Stronger blue for revenue
            name="Revenue"
            radius={[4, 4, 0, 0]}
          />
          <Bar
            dataKey="profit"
            fill="#66bb6a" // Balanced green for profit
            name="Profit"
            radius={[4, 4, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
