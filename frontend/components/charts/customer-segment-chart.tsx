"use client";

import { ChartContainer, ChartTooltipContent } from "@/components/ui/chart";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import {
  CHART_COLORS,
  CHART_GRADIENTS,
  formatCurrency,
  chartConfig,
} from "@/lib/chart-utils";
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

interface CustomerSegmentChartProps {
  data: {
    segment: string;
    revenue: number;
    profit: number;
  }[];
}

export function CustomerSegmentChart({ data }: CustomerSegmentChartProps) {
  return (
    <Tabs defaultValue="bar" className="w-full">
      <div className="w-full space-y-4">
        <TabsList className="w-full flex justify-center">
          <TabsTrigger value="bar">Bar View</TabsTrigger>
          <TabsTrigger value="pie">Pie View</TabsTrigger>
        </TabsList>

        {/* Bar Chart View */}
        <TabsContent value="bar" className="w-full">
          <ChartContainer
            config={{
              revenue: { label: "Revenue", color: CHART_COLORS.primary },
              profit: { label: "Profit", color: CHART_COLORS.secondary },
            }}
            className="h-[300px] p-4"
          >
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={data}
                margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#2d3748" />
                <XAxis
                  dataKey="segment"
                  tick={{ fill: "#CBD5E0", fontSize: 12 }}
                  tickLine={false}
                  axisLine={{ stroke: "#4A5568" }}
                />
                <YAxis
                  tickFormatter={(value) => `Nrs ${value / 100000}L`}
                  tick={{ fill: "#CBD5E0", fontSize: 12 }}
                  tickLine={false}
                  axisLine={{ stroke: "#4A5568" }}
                />
                <Tooltip
                  content={
                    <ChartTooltipContent
                      formatter={(value, name) => [
                        formatCurrency(Number(value)),
                        name,
                      ]}
                    />
                  }
                />
                <Legend />
                <Bar dataKey="revenue" radius={[6, 6, 0, 0]} barSize={32}>
                  {data.map((_, index) => (
                    <Cell
                      key={`cell-revenue-${index}`}
                      fill={`url(#gradientRevenue-${index})`}
                    />
                  ))}
                </Bar>
                <Bar dataKey="profit" radius={[6, 6, 0, 0]} barSize={32}>
                  {data.map((_, index) => (
                    <Cell
                      key={`cell-profit-${index}`}
                      fill={`url(#gradientProfit-${index})`}
                    />
                  ))}
                </Bar>

                {/* Gradient Definitions */}
                <defs>
                  {data.map((_, index) => (
                    <linearGradient
                      key={`gradientRevenue-${index}`}
                      id={`gradientRevenue-${index}`}
                      x1="0"
                      y1="0"
                      x2="0"
                      y2="1"
                    >
                      <stop
                        offset="0%"
                        stopColor={
                          CHART_GRADIENTS[index % CHART_GRADIENTS.length][0]
                        }
                      />
                      <stop
                        offset="100%"
                        stopColor={
                          CHART_GRADIENTS[index % CHART_GRADIENTS.length][1]
                        }
                      />
                    </linearGradient>
                  ))}
                  {data.map((_, index) => (
                    <linearGradient
                      key={`gradientProfit-${index}`}
                      id={`gradientProfit-${index}`}
                      x1="0"
                      y1="0"
                      x2="0"
                      y2="1"
                    >
                      <stop
                        offset="0%"
                        stopColor={
                          CHART_GRADIENTS[
                            (index + 3) % CHART_GRADIENTS.length
                          ][0]
                        }
                      />
                      <stop
                        offset="100%"
                        stopColor={
                          CHART_GRADIENTS[
                            (index + 3) % CHART_GRADIENTS.length
                          ][1]
                        }
                      />
                    </linearGradient>
                  ))}
                </defs>
              </BarChart>
            </ResponsiveContainer>
          </ChartContainer>
        </TabsContent>

        {/* Pie Chart View */}
        <TabsContent value="pie" className="w-full">
          <ChartContainer
            config={{
              revenue: { label: "Revenue", color: CHART_COLORS.primary },
              profit: { label: "Profit", color: CHART_COLORS.secondary },
            }}
            className="h-[350px] p-4"
          >
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={data}
                  dataKey="revenue"
                  nameKey="segment"
                  cx="50%"
                  cy="50%"
                  outerRadius={120}
                  innerRadius={60}
                  paddingAngle={4}
                  label={({ name, percent }) =>
                    `${name} (${(percent * 100).toFixed(0)}%)`
                  }
                >
                  {data.map((_, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={
                        CHART_COLORS[
                          Object.keys(CHART_COLORS)[
                            index % Object.keys(CHART_COLORS).length
                          ] as keyof typeof CHART_COLORS
                        ]
                      }
                    />
                  ))}
                </Pie>
                <Tooltip
                  content={
                    <ChartTooltipContent
                      formatter={(value, name) => [
                        formatCurrency(Number(value)),
                        name,
                      ]}
                    />
                  }
                />
                <Legend verticalAlign="bottom" height={36} />
              </PieChart>
            </ResponsiveContainer>
          </ChartContainer>
        </TabsContent>
      </div>
    </Tabs>
  );
}
