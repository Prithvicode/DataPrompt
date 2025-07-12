"use client";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

export function DailyOrdersChart({ data }: { data: any[] }) {
  return (
    <div className="h-[300px]">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart
          data={data}
          margin={{ top: 20, right: 30, left: 0, bottom: 40 }}
        >
          <XAxis
            dataKey="date"
            tick={{ fontSize: 12 }}
            tickLine={false}
            axisLine={false}
          />
          <YAxis tick={{ fontSize: 12 }} tickLine={false} axisLine={false} />
          <Tooltip
            formatter={(value: number) =>
              new Intl.NumberFormat("en-US").format(value)
            }
          />
          <Area
            type="monotone"
            dataKey="orders"
            stroke="#0288d1" // Deep sky blue
            fill="#0288d1"
            fillOpacity={0.25}
            name="Daily Orders"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
