import React from "react";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
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

type Props = {
  data: RawCategoryData[];
};

const COLORS = [
  "#8884d8",
  "#8dd1e1",
  "#ffc658",
  "#a4de6c",
  "#d0ed57",
  "#ff8042",
  "#82ca9d",
  "#ffbb28",
];

// Map for fixing misspelled categories
const CATEGORY_FIXES: Record<string, string> = {
  Clothng: "Clothing",
  Electrnics: "Electronics",
};

function normalizeCategory(name: string): string {
  return CATEGORY_FIXES[name] || name;
}

// Aggregate and normalize input data
function processData(data: RawCategoryData[]) {
  const grouped: Record<string, number> = {};

  data.forEach((item) => {
    const category = normalizeCategory(item.category);
    if (!grouped[category]) grouped[category] = 0;
    grouped[category] += item.revenue;
  });

  return Object.entries(grouped).map(([category, revenue]) => ({
    category,
    revenue,
  }));
}

export const CategoryPieChart: React.FC<Props> = ({ data }) => {
  const chartData = processData(data);

  return (
    <div className="w-full h-[400px] bg-background rounded-2xl shadow p-4">
      <h2 className="text-xl font-semibold text-center mb-4">
        Revenue by Product Category
      </h2>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={chartData}
            dataKey="revenue"
            nameKey="category"
            cx="50%"
            cy="50%"
            outerRadius={120}
            label={({ category }) => category}
            isAnimationActive
          >
            {chartData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={COLORS[index % COLORS.length]}
              />
            ))}
          </Pie>
          <Tooltip
            formatter={(value: number) => `$${value.toLocaleString()}`}
            contentStyle={{
              backgroundColor: "#1f2937",
              border: "none",
              color: "#fff",
            }}
          />
          <Legend verticalAlign="bottom" height={36} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
};
