"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import { BarChart, PieChart, Calendar, Database } from "lucide-react";

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
    <div className="space-y-6 text-gray-100 custom-scrollbar">
      <Card className="bg-gray-900 border-gray-800 shadow-md dark">
        <CardHeader className="pb-2">
          <div className="flex items-center gap-2">
            <Database className="h-5 w-5 text-blue-400" />
            <CardTitle>Dataset Overview</CardTitle>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-gray-800/50 p-4 rounded-lg border border-gray-800/50 hover:border-blue-500/30 transition-colors">
              <div className="text-sm text-gray-400 mb-1">Rows</div>
              <div className="text-xl font-semibold">
                {datasetInfo.rows || 0}
              </div>
            </div>
            <div className="bg-gray-800/50 p-4 rounded-lg border border-gray-800/50 hover:border-blue-500/30 transition-colors">
              <div className="text-sm text-gray-400 mb-1">Columns</div>
              <div className="text-xl font-semibold">
                {datasetInfo.columns || 0}
              </div>
            </div>
            <div className="bg-gray-800/50 p-4 rounded-lg border border-gray-800/50 hover:border-blue-500/30 transition-colors">
              <div className="text-sm text-gray-400 mb-1">Numeric Columns</div>
              <div className="text-xl font-semibold">
                {datasetInfo.numeric_columns?.length || 0}
              </div>
            </div>
            <div className="bg-gray-800/50 p-4 rounded-lg border border-gray-800/50 hover:border-blue-500/30 transition-colors">
              <div className="text-sm text-gray-400 mb-1">
                Categorical Columns
              </div>
              <div className="text-xl font-semibold">
                {datasetInfo.categorical_columns?.length || 0}
              </div>
            </div>
          </div>

          {/* Display column types chart if available */}
          {plots.column_types && (
            <div className="mt-6 bg-gray-800/30 p-4 rounded-lg border border-gray-800">
              <h3 className="text-sm font-medium mb-3 text-gray-300 flex items-center gap-2">
                <PieChart className="h-4 w-4 text-blue-400" />
                Column Types Distribution
              </h3>
              {/* Image would go here */}
              <div className="h-40 bg-gray-800/50 rounded-md flex items-center justify-center text-gray-500">
                Column types visualization
              </div>
            </div>
          )}

          {/* Display missing values chart if available */}
          {plots.missing_values && (
            <div className="mt-4 bg-gray-800/30 p-4 rounded-lg border border-gray-800">
              <h3 className="text-sm font-medium mb-3 text-gray-300 flex items-center gap-2">
                <BarChart className="h-4 w-4 text-blue-400" />
                Missing Values
              </h3>
              {/* Image would go here */}
              <div className="h-40 bg-gray-800/50 rounded-md flex items-center justify-center text-gray-500">
                Missing values visualization
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {Object.keys(numericStats).length > 0 && (
        <Card className=" dark bg-gray-900 border-gray-800 shadow-md">
          <CardHeader className="pb-2">
            <div className="flex items-center gap-2">
              <BarChart className="h-5 w-5 text-blue-400" />
              <CardTitle>Numeric Statistics</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto rounded-lg border border-gray-800">
              <Table>
                <TableHeader className="bg-gray-800/50">
                  <TableRow className="hover:bg-transparent border-gray-800">
                    <TableHead className="text-gray-300">Column</TableHead>
                    <TableHead className="text-right text-gray-300">
                      Mean
                    </TableHead>
                    <TableHead className="text-right text-gray-300">
                      Min
                    </TableHead>
                    <TableHead className="text-right text-gray-300">
                      Max
                    </TableHead>
                    <TableHead className="text-right text-gray-300">
                      Std Dev
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {Object.entries(numericStats).map(
                    ([column, stats]: [string, any], index) => (
                      <TableRow
                        key={column}
                        className={`hover:bg-gray-800/30 border-gray-800 ${
                          index % 2 === 0 ? "bg-gray-900" : "bg-gray-900/50"
                        }`}
                      >
                        <TableCell className="font-medium text-gray-200">
                          {column}
                        </TableCell>
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
        <Card className="bg-gray-900 border-gray-800 shadow-md">
          <CardHeader className="pb-2">
            <div className="flex items-center gap-2">
              <PieChart className="h-5 w-5 text-blue-400" />
              <CardTitle>Categorical Statistics</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {Object.entries(categoricalStats).map(
                ([column, stats]: [string, any]) => (
                  <div
                    key={column}
                    className="bg-gray-800/30 p-4 rounded-lg border border-gray-800"
                  >
                    <h3 className="font-medium mb-3 text-gray-200">{column}</h3>
                    <div className="bg-blue-900/30 p-4 rounded-lg border border-blue-900/30 mb-4">
                      <div className="text-sm text-gray-400 mb-1">
                        Unique Values
                      </div>
                      <div className="text-xl font-semibold">
                        {stats.unique_values || "N/A"}
                      </div>
                    </div>

                    {stats.top_values &&
                      Object.keys(stats.top_values).length > 0 && (
                        <div>
                          <div className="text-sm text-gray-400 mb-2">
                            Top Values
                          </div>
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                            {Object.entries(stats.top_values)
                              .slice(0, 4)
                              .map(([value, count]: [string, any], index) => (
                                <div
                                  key={value}
                                  className="bg-gray-800/70 p-3 rounded-lg border border-gray-800 flex justify-between items-center hover:border-blue-500/30 transition-colors"
                                >
                                  <span className="truncate max-w-[70%] text-gray-200">
                                    {value}
                                  </span>
                                  <span className="text-blue-400 font-medium bg-blue-400/10 px-2 py-0.5 rounded-md">
                                    {count}
                                  </span>
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
        <Card className="bg-gray-900 border-gray-800 shadow-md">
          <CardHeader className="pb-2">
            <div className="flex items-center gap-2">
              <Calendar className="h-5 w-5 text-blue-400" />
              <CardTitle>Date Statistics</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {Object.entries(dateStats).map(
                ([column, stats]: [string, any]) => (
                  <div
                    key={column}
                    className="bg-gray-800/30 p-4 rounded-lg border border-gray-800"
                  >
                    <h3 className="font-medium mb-3 text-gray-200">{column}</h3>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      <div className="bg-gray-800/70 p-4 rounded-lg border border-gray-800 hover:border-blue-500/30 transition-colors">
                        <div className="text-sm text-gray-400 mb-1">
                          Min Date
                        </div>
                        <div className="text-lg font-semibold">
                          {stats.min_date || "N/A"}
                        </div>
                      </div>
                      <div className="bg-gray-800/70 p-4 rounded-lg border border-gray-800 hover:border-blue-500/30 transition-colors">
                        <div className="text-sm text-gray-400 mb-1">
                          Max Date
                        </div>
                        <div className="text-lg  font-semibold">
                          {stats.max_date || "N/A"}
                        </div>
                      </div>
                      <div className="bg-gray-800/70 p-4 rounded-lg border border-gray-800 hover:border-blue-500/30 transition-colors sm:col-span-2">
                        <div className="text-sm text-gray-400 mb-1">
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
