"use client";

import { ChartContainer, ChartTooltipContent } from "@/components/ui/chart";
import { CHART_COLORS, formatCurrency, chartConfig } from "@/lib/chart-utils";
import {
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

type RawCategoryData = {
  category: string;
  revenue: number;
  profit: number;
  unitsSold: number;
  orders: number;
  avgOrderValue: number;
  profitPerUnit: number;
};

interface Props {
  data: RawCategoryData[];
}

// Map for fixing misspelled categories
const CATEGORY_FIXES: Record<string, string> = {
  Clothng: "Clothing",
  Electrnics: "Electronics",
};

const normalizeCategory = (name: string): string =>
  CATEGORY_FIXES[name] || name;

// Aggregate and normalize input data
function processData(data: RawCategoryData[]) {
  const grouped: Record<string, number> = {};
  data.forEach((item) => {
    const category = normalizeCategory(item.category);
    grouped[category] = (grouped[category] || 0) + item.unitsSold;
  });
  return Object.entries(grouped).map(([category, unitsSold]) => ({
    category,
    unitsSold,
  }));
}

export default function UnitsSoldPieChart({ data }: Props) {
  const chartData = processData(data);

  return (
    <div className="w-full animate-fade-in">
      <ChartContainer
        config={Object.fromEntries(
          chartData.map((item, index) => [
            item.category,
            {
              label: item.category,
              color:
                CHART_COLORS[
                  Object.keys(CHART_COLORS)[
                    index % Object.keys(CHART_COLORS).length
                  ] as keyof typeof CHART_COLORS
                ],
            },
          ])
        )}
        className="h-[350px] p-4"
      >
        <ResponsiveContainer {...chartConfig.responsiveContainer}>
          <PieChart>
            <Pie
              data={chartData}
              dataKey="unitsSold"
              nameKey="category"
              cx="50%"
              cy="50%"
              outerRadius={120}
              innerRadius={60}
              paddingAngle={4}
              label={({ name, value }) => `${name}: ${value.toLocaleString()}`}
            >
              {chartData.map((_, index) => (
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
                    `${value.toLocaleString()} units`,
                    name,
                  ]}
                />
              }
            />
            <Legend verticalAlign="bottom" height={36} />
          </PieChart>
        </ResponsiveContainer>
      </ChartContainer>
    </div>
  );
}
