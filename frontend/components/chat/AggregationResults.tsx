import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart } from "recharts";

interface AggregationResultsProps {
  data: any;
}

export default function AggregationResults({ data }: AggregationResultsProps) {
  // Handle different data formats from the backend
  const chartData = data.data || [];
  const groupByColumns = data.group_by_columns || [];
  const aggColumn = data.agg_column || "";
  const aggFunction = data.agg_function || "sum";
  const plots = data.plots || {};

  // If we have a base64 plot from the backend, display it
  if (plots.aggregation) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{`${
            aggFunction.charAt(0).toUpperCase() + aggFunction.slice(1)
          } of ${aggColumn} by ${groupByColumns.join(", ")}`}</CardTitle>
        </CardHeader>
        <CardContent>
          <img
            src={`data:image/png;base64,${plots.aggregation}`}
            alt="Aggregation plot"
            className="w-full rounded-md"
          />
        </CardContent>
      </Card>
    );
  }

  // If we have a visualization spec from the backend, use it
  if (data.visualization && data.visualization.type === "bar") {
    const { x, y, data: vizData, title, xLabel, yLabel } = data.visualization;

    return (
      <Card>
        <CardHeader>
          <CardTitle>
            {title ||
              `${
                aggFunction.charAt(0).toUpperCase() + aggFunction.slice(1)
              } of ${aggColumn} by ${groupByColumns.join(", ")}`}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[300px]">
            {/* <BarChart
              data={vizData}
              index={x}
              categories={[y]}
              colors={["blue"]}
              //   valueFormatter={(value) => value.toFixed(2)}
              showLegend={false}
              showGridLines={false}
            /> */}
          </div>
        </CardContent>
      </Card>
    );
  }

  // Fallback to a simple bar chart with the data we have
  if (chartData.length > 0 && groupByColumns.length > 0 && aggColumn) {
    const groupCol = groupByColumns[0];

    return (
      <Card>
        <CardHeader>
          <CardTitle>{`${
            aggFunction.charAt(0).toUpperCase() + aggFunction.slice(1)
          } of ${aggColumn} by ${groupCol}`}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[300px]">
            {/* <BarChart
              data={chartData}
              index={groupCol}
              categories={[aggColumn]}
              colors={["blue"]}
              valueFormatter={(value) => value.toFixed(2)}
              showLegend={false}
              showGridLines={false}
            /> */}
          </div>
        </CardContent>
      </Card>
    );
  }

  // If we don't have enough data for a chart, show a message
  return (
    <Card>
      <CardHeader>
        <CardTitle>Aggregation Results</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-gray-400">
          No visualization available for this aggregation.
        </p>
      </CardContent>
    </Card>
  );
}
