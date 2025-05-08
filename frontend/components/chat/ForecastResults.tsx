import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface ForecastResultsProps {
  data: any;
}

export default function ForecastResults({ data }: ForecastResultsProps) {
  const chartData = data || [];
  const title = data?.target_column
    ? `Forecast for ${data.target_column}`
    : "Forecast Resultsss";
  const historicalData = chartData.filter((d: any) => d.type === "historical");
  const forecastData = chartData.filter((d: any) => d.type === "forecast");
  // Merge sorted data for x-axis continuity
  const combinedData = [...historicalData, ...forecastData].sort(
    (a, b) => new Date(a.Date).getTime() - new Date(b.Date).getTime()
  );
  return (
    <Card className="bg-white text-gray-900 shadow-sm">
      <CardHeader>
        <CardTitle className="text-lg font-semibold">{title}</CardTitle>
      </CardHeader>
      <CardContent className="pr-4">
        <div className="h-[300px] -mr-4">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart
              data={combinedData}
              margin={{ top: 20, right: 50, bottom: 40, left: 50 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis
                dataKey="Date"
                stroke="#6b7280"
                tickFormatter={(str) =>
                  new Date(str).toLocaleDateString("en-US", {
                    month: "short",
                    year: "2-digit",
                  })
                }
                label={{
                  value: "Date",
                  position: "insideBottom",
                  offset: -5,
                  fill: "#6b7280",
                }}
              />
              <YAxis
                stroke="#6b7280"
                tickFormatter={(val) => `${val.toFixed(0)}`}
                label={{
                  value: data?.target_column || "Revenue",
                  angle: -90,
                  position: "insideLeft",
                  fill: "#6b7280",
                  offset: -5,
                }}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "#f9fafb",
                  borderColor: "#d1d5db",
                  borderRadius: "0.5rem",
                  boxShadow: "0 2px 10px rgba(0,0,0,0.05)",
                }}
                labelStyle={{
                  color: "#111827",
                  fontWeight: "500",
                }}
                itemStyle={{
                  color: "#1f2937",
                }}
                labelFormatter={(label) =>
                  new Date(label).toLocaleDateString("en-US", {
                    month: "long",
                    year: "numeric",
                  })
                }
                formatter={(value: number) => [
                  `Nrs.${value.toFixed(2)}`,
                  data?.target_column || "Revenue",
                ]}
              />
              <Line
                type="monotone"
                dataKey={(d) =>
                  d.type === "historical" ? d.PredictedRevenue : null
                }
                stroke="#10b981"
                strokeWidth={2}
                dot={{ r: 3 }}
                name="Historical"
              />

              <Line
                type="monotone"
                dataKey={(d) =>
                  d.type === "forecast" ? d.PredictedRevenue : null
                }
                stroke="#f59e0b"
                strokeWidth={2}
                dot={{ r: 3 }}
                name="Forecast"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
