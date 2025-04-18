import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";

interface DataSummaryProps {
  data: any;
}

export default function DataSummary({ data }: DataSummaryProps) {
  // Handle different data formats from the backend
  const datasetInfo = data.dataset_info || {};
  const numericStats = data.numeric_stats || {};
  const categoricalStats = data.categorical_stats || {};
  const dateStats = data.date_stats || {};
  const plots = data.plots || {};

  return (
    <div className="space-y-4">
      <Card className="dark">
        {" "}
        {/* Card component likely handles its own dark background */}
        <CardHeader>
          <CardTitle>Dataset Overview</CardTitle>{" "}
          {/* Text color likely inherited */}
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-2">
            <div className="bg-gray-800 p-3 rounded-md">
              {" "}
              {/* Background fits dark theme */}
              <div className="text-sm text-gray-400">Rows</div>{" "}
              {/* Label text color consistent */}
              <div className="text-lg font-semibold">
                {" "}
                {/* Value text color likely inherited (gray-100) */}
                {datasetInfo.rows || 0}
              </div>
            </div>
            <div className="bg-gray-800 p-3 rounded-md">
              <div className="text-sm text-gray-400">Columns</div>
              <div className="text-lg font-semibold">
                {datasetInfo.columns || 0}
              </div>
            </div>
            <div className="bg-gray-800 p-3 rounded-md">
              <div className="text-sm text-gray-400">Numeric Columns</div>
              <div className="text-lg font-semibold">
                {datasetInfo.numeric_columns?.length || 0}
              </div>
            </div>
            <div className="bg-gray-800 p-3 rounded-md">
              <div className="text-sm text-gray-400">Categorical Columns</div>
              <div className="text-lg font-semibold">
                {datasetInfo.categorical_columns?.length || 0}
              </div>
            </div>
          </div>

          {/* Display column types chart if available */}
          {plots.column_types && <div className="mt-4">{/* Image */}</div>}

          {/* Display missing values chart if available */}
          {plots.missing_values && (
            <div className="mt-4">
              <h3 className="text-sm font-medium mb-2">Missing Values</h3>{" "}
              {/* Text color likely inherited */}
              {/* Image */}
            </div>
          )}
        </CardContent>
      </Card>

      {Object.keys(numericStats).length > 0 && (
        <Card className="dark ">
          {" "}
          {/* Card component likely handles its own dark background */}
          <CardHeader>
            <CardTitle>Numeric Statistics</CardTitle>{" "}
            {/* Text color likely inherited */}
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto custom">
              <Table>
                {" "}
                {/* Table component likely styled for dark theme */}
                <TableHeader>
                  <TableRow>
                    <TableHead>Column</TableHead>{" "}
                    {/* Text color likely inherited */}
                    <TableHead className="text-right">Mean</TableHead>
                    <TableHead className="text-right">Min</TableHead>
                    <TableHead className="text-right">Max</TableHead>
                    <TableHead className="text-right">Std Dev</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {Object.entries(numericStats).map(
                    ([column, stats]: [string, any]) => (
                      <TableRow key={column}>
                        {" "}
                        {/* Row background likely dark/alternating */}
                        <TableCell className="font-medium">
                          {column}
                        </TableCell>{" "}
                        {/* Text color likely inherited */}
                        <TableCell className="text-right">
                          {stats.mean?.toFixed(2) || "N/A"}
                        </TableCell>
                        <TableCell className="text-right">
                          {stats.min?.toFixed(2) || "N/A"}
                        </TableCell>
                        <TableCell className="text-right">
                          {stats.max?.toFixed(2) || "N/A"}
                        </TableCell>
                        <TableCell className="text-right">
                          {stats.std?.toFixed(2) || "N/A"}
                        </TableCell>
                      </TableRow>
                    )
                  )}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      )}

      {Object.keys(categoricalStats).length > 0 && (
        <Card>
          {" "}
          {/* Card component likely handles its own dark background */}
          <CardHeader>
            <CardTitle>Categorical Statistics</CardTitle>{" "}
            {/* Text color likely inherited */}
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Object.entries(categoricalStats).map(
                ([column, stats]: [string, any]) => (
                  <div key={column}>
                    <h3 className="font-medium mb-2">{column}</h3>{" "}
                    {/* Text color likely inherited */}
                    <div className="bg-blue-800 p-3 rounded-md">
                      {" "}
                      {/* Accent background color */}
                      <div className="text-sm text-gray-400">
                        Unique Values
                      </div>{" "}
                      {/* Label text color consistent */}
                      <div className="text-lg font-semibold">
                        {" "}
                        {/* Value text color likely inherited (gray-100) */}
                        {stats.unique_values || "N/A"}
                      </div>
                    </div>
                    {stats.top_values &&
                      Object.keys(stats.top_values).length > 0 && (
                        <div className="mt-2">
                          <div className="text-sm text-gray-400 mb-1">
                            {" "}
                            {/* Label text color consistent */}
                            Top Values
                          </div>
                          <div className="grid grid-cols-2 gap-2">
                            {Object.entries(stats.top_values)
                              .slice(0, 4)
                              .map(([value, count]: [string, any]) => (
                                <div
                                  key={value}
                                  className="bg-gray-800 p-2 rounded-md flex justify-between" // Background fits dark theme
                                >
                                  <span className="truncate max-w-[70%]">
                                    {" "}
                                    {/* Text color likely inherited */}
                                    {value}
                                  </span>
                                  <span className="text-gray-400">{count}</span>{" "}
                                  {/* Count text color consistent */}
                                </div>
                              ))}
                          </div>
                        </div>
                      )}
                  </div>
                )
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {Object.keys(dateStats).length > 0 && (
        <Card>
          {" "}
          {/* Card component likely handles its own dark background */}
          <CardHeader>
            <CardTitle>Date Statistics</CardTitle>{" "}
            {/* Text color likely inherited */}
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Object.entries(dateStats).map(
                ([column, stats]: [string, any]) => (
                  <div key={column}>
                    <h3 className="font-medium mb-2">{column}</h3>{" "}
                    {/* Text color likely inherited */}
                    <div className="grid grid-cols-2 gap-2">
                      <div className="bg-gray-800 p-3 rounded-md">
                        {" "}
                        {/* Background fits dark theme */}
                        <div className="text-sm text-gray-400">
                          Min Date
                        </div>{" "}
                        {/* Label text color consistent */}
                        <div className="text-lg font-semibold">
                          {" "}
                          {/* Value text color likely inherited (gray-100) */}
                          {stats.min_date || "N/A"}
                        </div>
                      </div>
                      <div className="bg-gray-800 p-3 rounded-md col-span-2">
                        {" "}
                        {/* Background fits dark theme */}
                        <div className="text-sm text-gray-400">
                          Date Range (days)
                        </div>
                        <div className="text-lg font-semibold">
                          {stats.range_days || "N/A"}
                        </div>
                      </div>
                    </div>
                  </div>
                )
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
