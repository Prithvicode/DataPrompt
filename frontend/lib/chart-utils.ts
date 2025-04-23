// Modern color palette with carefully selected colors
export const CHART_COLORS = {
  primary: "#8B5CF6", // Purple
  secondary: "#10B981", // Emerald
  tertiary: "#F59E0B", // Amber
  quaternary: "#3B82F6", // Blue
  quinary: "#EC4899", // Pink
  senary: "#6366F1", // Indigo
};

export const CHART_GRADIENTS = [
  ["#C084FC", "#8B5CF6"], // Purple gradient
  ["#34D399", "#10B981"], // Green gradient
  ["#FBBF24", "#F59E0B"], // Amber gradient
  ["#60A5FA", "#3B82F6"], // Blue gradient
  ["#F472B6", "#EC4899"], // Pink gradient
  ["#818CF8", "#6366F1"], // Indigo gradient
];

// Formatter for currency values
export const formatCurrency = (value: number) =>
  `Nrs ${value.toLocaleString("en-IN", { maximumFractionDigits: 0 })}`;

// Common chart styles
export const chartConfig = {
  tooltip: {
    contentStyle: {
      backgroundColor: "rgba(17, 24, 39, 0.95)",
      borderColor: "rgba(75, 85, 99, 0.3)",
      borderRadius: "0.5rem",
      padding: "0.75rem",
      boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.2)",
      border: "none",
    },
  },
  responsiveContainer: {
    className: "w-full h-full min-h-[300px]",
  },
};
