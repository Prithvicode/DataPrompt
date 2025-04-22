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

interface MonthlySalesChartProps {
  data: {
    date: string;
    revenue: number;
    profit: number;
    unitsSold: number;
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
  "#F472B6", // Pink
  "#34D399", // Teal
  "#FB923C", // Orange
  "#EAB308", // Yellow
  "#F87171", // Light Red
];

export function MonthlySalesChart({ data }: MonthlySalesChartProps) {
  return (
    <div className="grid gap-6">
      {/* Pie Chart: Revenue distribution across months */}
      <ChartContainer
        config={{
          "2021-03": { label: "March 2021", color: chartColors[0] },
          "2022-11": { label: "November 2022", color: chartColors[1] },
          "2023-01": { label: "January 2023", color: chartColors[2] },
          "2023-03": { label: "March 2023", color: chartColors[3] },
          "2023-05": { label: "May 2023", color: chartColors[4] },
          "2023-06": { label: "June 2023", color: chartColors[5] },
          "2023-11": { label: "November 2023", color: chartColors[6] },
          "2024-03": { label: "March 2024", color: chartColors[7] },
          "2024-06": { label: "June 2024", color: chartColors[8] },
          "2024-08": { label: "August 2024", color: chartColors[9] },
          "2024-09": { label: "September 2024", color: chartColors[10] },
          "2024-12": { label: "December 2024", color: chartColors[11] },
        }}
        className="h-[300px]"
      >
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              dataKey="revenue"
              nameKey="date"
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

      {/* Bar Chart: Revenue & Profit over months */}
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
              dataKey="date"
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
