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
import { BarChart, Database } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../ui/tabs";
import { CategoryPieChart } from "../charts/montly-performance-chart";
import UnitsSoldPieChart from "../charts/product-category-chart";
import { CustomerSegmentChart } from "../charts/customer-segment-chart";
import { MonthlySalesChart } from "../charts/monthly-sales-chart";

interface DataSummaryProps {
  data: any;
}

export default function DataSummary({ data }: DataSummaryProps) {
  const datasetInfo = data.dataset_info || {};
  const numericStats = data.numeric_stats || {};

  return (
    <div className="space-y-4 text-gray-100 p-2 custom-scrollbar">
      {/* Dataset Overview */}
      <Card className="bg-gray-900 border border-gray-800">
        <CardHeader className="pb-1">
          <div className="flex items-center gap-2">
            <Database className="h-4 w-4 text-blue-400" />
            <CardTitle className="text-base">Dataset Overview</CardTitle>
          </div>
        </CardHeader>
        <CardContent className="grid grid-cols-2 gap-2 pt-2">
          {[
            { label: "Rows", value: datasetInfo.rows || 0 },
            { label: "Columns", value: datasetInfo.columns || 0 },
            {
              label: "Numeric Columns",
              value: datasetInfo.numeric_columns?.length || 0,
            },
            {
              label: "Categorical Columns",
              value: datasetInfo.categorical_columns?.length || 0,
            },
          ].map((item) => (
            <div
              key={item.label}
              className="bg-gray-800/50 p-3 rounded-lg border border-gray-700 hover:border-blue-500/30 transition-colors"
            >
              <div className="text-xs text-gray-400">{item.label}</div>
              <div className="text-lg font-semibold">{item.value}</div>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Tabs for Charts */}
      <Tabs
        defaultValue="product-category"
        className="bg-gray-900 border border-gray-800 rounded-lg"
      >
        <TabsList className="grid grid-cols-3 gap-1 p-1 bg-gray-800 rounded-lg">
          <TabsTrigger value="product-category">Category</TabsTrigger>
          <TabsTrigger value="customer-segment">Segments</TabsTrigger>
          <TabsTrigger value="monthly-performance">Monthly</TabsTrigger>
        </TabsList>

        <TabsContent value="product-category">
          <CardContent className="pt-3">
            <UnitsSoldPieChart
              data={data.charts_data.product_category_performance}
            />
          </CardContent>
        </TabsContent>
        <TabsContent value="customer-segment">
          <CardContent className="pt-3">
            <CustomerSegmentChart data={data.charts_data.customer_segments} />
          </CardContent>
        </TabsContent>
        <TabsContent value="monthly-performance">
          <CardContent className="pt-3">
            <MonthlySalesChart data={data.charts_data.monthly_performance} />
          </CardContent>
        </TabsContent>
      </Tabs>

      {/* Numeric Stats Table */}
      {Object.keys(numericStats).length > 0 && (
        <Card className="bg-gray-900 border border-gray-800">
          <CardHeader className="pb-1">
            <div className="flex items-center gap-2">
              <BarChart className="h-4 w-4 text-blue-400" />
              <CardTitle className="text-base">Numeric Stats</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="pt-2">
            <div className="overflow-x-auto rounded-lg border border-gray-800">
              <Table>
                <TableHeader className="bg-gray-800/50">
                  <TableRow className="hover:bg-transparent border-gray-800">
                    {["Column", "Mean", "Min", "Max", "Std Dev"].map((head) => (
                      <TableHead
                        key={head}
                        className="text-gray-300 text-right first:text-left"
                      >
                        {head}
                      </TableHead>
                    ))}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {Object.entries(numericStats).map(
                    ([col, stats]: [string, any], i) => (
                      <TableRow
                        key={col}
                        className={`hover:bg-gray-800/30 border-gray-800 ${
                          i % 2 === 0 ? "bg-gray-900" : "bg-gray-900/50"
                        }`}
                      >
                        <TableCell className="text-gray-200 font-medium">
                          {col}
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
    </div>
  );
}
