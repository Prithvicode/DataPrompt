"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ChartContainer, ChartTooltipContent } from "@/components/ui/chart";

interface CustomerSegmentChartProps {
  data: {
    segment: string;
    revenue: number;
    profit: number;
  }[];
}

// Nepali Rupees formatter
const formatNrs = (value: number) =>
  `Nrs ${value.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;

// Random but consistent color palette
const chartColors = [
  "#6366F1", // Indigo
  "#10B981", // Emerald
  "#F59E0B", // Amber
  "#EF4444", // Red
  "#3B82F6", // Blue
  "#8B5CF6", // Violet
];

export function CustomerSegmentChart({ data }: CustomerSegmentChartProps) {
  return (
    <div className="grid gap-6">
      {/* Pie Chart */}
      <ChartContainer
        config={{
          Online: { label: "Online", color: chartColors[0] },
          Retail: { label: "Retail", color: chartColors[1] },
          Wholesale: { label: "Wholesale", color: chartColors[2] },
        }}
        className="h-[300px]"
      >
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              dataKey="revenue"
              nameKey="segment"
              cx="50%"
              cy="50%"
              outerRadius={100}
              innerRadius={60}
              paddingAngle={2}
              label={({ name, percent }) =>
                `${name} (${(percent * 100).toFixed(0)}%)`
              }
            >
              {data.map((_, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={chartColors[index % chartColors.length]}
                />
              ))}
            </Pie>
            <Tooltip
              content={
                <ChartTooltipContent
                  formatter={(value, name) => [formatNrs(Number(value)), name]}
                />
              }
            />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </ChartContainer>

      {/* Bar Chart */}
      <ChartContainer
        config={{
          revenue: { label: "Revenue", color: chartColors[0] },
          profit: { label: "Profit", color: chartColors[1] },
        }}
        className="h-[250px]"
      >
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data}
            margin={{ top: 10, right: 10, left: 10, bottom: 20 }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              vertical={false}
              className="stroke-muted"
            />
            <XAxis
              dataKey="segment"
              tick={{ fontSize: 12 }}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              tickFormatter={(value) => `Nrs ${value / 100000}L`}
              tick={{ fontSize: 12 }}
              tickLine={false}
              axisLine={false}
            />
            <Tooltip
              content={
                <ChartTooltipContent
                  formatter={(value, name) => [formatNrs(Number(value)), name]}
                />
              }
            />
            <Legend />
            <Bar
              dataKey="revenue"
              fill={chartColors[0]}
              radius={[4, 4, 0, 0]}
              barSize={30}
            />
            <Bar
              dataKey="profit"
              fill={chartColors[1]}
              radius={[4, 4, 0, 0]}
              barSize={30}
            />
          </BarChart>
        </ResponsiveContainer>
      </ChartContainer>
    </div>
  );
}
