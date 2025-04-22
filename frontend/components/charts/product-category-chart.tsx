import React from "react";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

// Define your own color palette for the pie chart
const COLORS = [
  "#8884d8",
  "#82ca9d",
  "#ffc658",
  "#ff7f50",
  "#00bcd4",
  "#a1887f",
];

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

const UnitsSoldPieChart = ({ data }: Props) => {
  return (
    <div className="w-full h-96 p-4 bg-white dark:bg-gray-900 rounded-2xl shadow-md">
      <h2 className="text-xl font-semibold text-center text-gray-800 dark:text-gray-200 mb-4">
        Units Sold by Category
      </h2>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            dataKey="unitsSold"
            nameKey="category"
            cx="50%"
            cy="50%"
            outerRadius={120}
            fill="#8884d8"
            label={({ category, unitsSold }) => `${category}: ${unitsSold}`}
          >
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={COLORS[index % COLORS.length]}
              />
            ))}
          </Pie>
          <Tooltip formatter={(value) => `${value} units`} />
          <Legend verticalAlign="bottom" height={36} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
};

export default UnitsSoldPieChart;
