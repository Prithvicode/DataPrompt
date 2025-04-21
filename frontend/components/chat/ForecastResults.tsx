import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LineChart } from "recharts";

interface ForecastResultsProps {
  data: any;
}

export default function ForecastResults({ data }: ForecastResultsProps) {
  // Handle different data formats from the backend
  const chartData = data.data || [];
  const metrics = data.metrics || {};
  const title = data.target_column
    ? `Forecast for ${data.target_column}`
    : "Forecast Results";
  const plots = data.plots || {};

  // If we have a base64 plot from the backend, display it
  if (plots.forecast) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
        </CardHeader>
        <CardContent>
          <img
            src={`data:image/png;base64,${plots.forecast}`}
            alt="Forecast plot"
            className="w-full rounded-md"
          />
          {Object.keys(metrics).length > 0 && (
            <div className="mt-4 grid grid-cols-2 gap-2">
              {metrics.r2 !== undefined && (
                <div className="bg-gray-800 p-3 rounded-md">
                  <div className="text-sm text-gray-400">R² Score</div>
                  <div className="text-lg font-semibold">
                    {(metrics.r2 * 100).toFixed(1)}%
                  </div>
                </div>
              )}
              {metrics.mse !== undefined && (
                <div className="bg-gray-800 p-3 rounded-md">
                  <div className="text-sm text-gray-400">
                    Mean Squared Error
                  </div>
                  <div className="text-lg font-semibold">
                    {metrics.mse.toFixed(2)}
                  </div>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    );
  }

  // If we have a visualization spec from the backend, use it
  if (data.visualization && data.visualization.type === "line") {
    const { x, y, data: vizData } = data.visualization;

    return (
      <Card>
        <CardHeader>
          <CardTitle>{data.visualization.title || title}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[300px]">
            {/* <LineChart
              data={vizData}
              index={x}
              categories={[y]}
              colors={["blue"]}
              valueFormatter={(value) => value.toFixed(2)}
              showLegend={false}
              showGridLines={false}
            /> */}
          </div>
          {Object.keys(metrics).length > 0 && (
            <div className="mt-4 grid grid-cols-2 gap-2">
              {metrics.r2 !== undefined && (
                <div className="bg-gray-800 p-3 rounded-md">
                  <div className="text-sm text-gray-400">R² Score</div>
                  <div className="text-lg font-semibold">
                    {(metrics.r2 * 100).toFixed(1)}%
                  </div>
                </div>
              )}
              {metrics.mse !== undefined && (
                <div className="bg-gray-800 p-3 rounded-md">
                  <div className="text-sm text-gray-400">
                    Mean Squared Error
                  </div>
                  <div className="text-lg font-semibold">
                    {metrics.mse.toFixed(2)}
                  </div>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    );
  }

  // Fallback to a simple line chart with the data we have
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[300px]">
          {/* <LineChart
            data={chartData}
            index="period" // Assuming the data has a period field
            categories={["value"]} // Assuming the data has a value field
            colors={["blue"]}
            valueFormatter={(value) => value.toFixed(2)}
            showLegend={false}
            showGridLines={false}
          /> */}
        </div>
        {Object.keys(metrics).length > 0 && (
          <div className="mt-4 grid grid-cols-2 gap-2">
            {metrics.r2 !== undefined && (
              <div className="bg-gray-800 p-3 rounded-md">
                <div className="text-sm text-gray-400">R² Score</div>
                <div className="text-lg font-semibold">
                  {(metrics.r2 * 100).toFixed(1)}%
                </div>
              </div>
            )}
            {metrics.mse !== undefined && (
              <div className="bg-gray-800 p-3 rounded-md">
                <div className="text-sm text-gray-400">Mean Squared Error</div>
                <div className="text-lg font-semibold">
                  {metrics.mse.toFixed(2)}
                </div>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
