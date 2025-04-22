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
import { CategoryPieChart } from "../charts/montly-performance-chart";
import UnitsSoldPieChart from "../charts/product-category-chart";
import { CustomerSegmentChart } from "../charts/customer-segment-chart";
import { MonthlySalesChart } from "../charts/monthly-sales-chart";
import { TabsContent, TabsList, TabsTrigger, Tabs } from "../ui/tabs";
interface DataSummaryProps {
  data: any;
}

export default function DataSummary({ data }: DataSummaryProps) {
  // Handle different data formats from the backend
  const datasetInfo = data.dataset_info || {};
  const numericStats = data.numeric_stats || {};

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
        </CardContent>
        <CardContent className="pl-2">
          <UnitsSoldPieChart
            data={data.charts_data.product_category_performance}
          />
        </CardContent>
        <CardContent className="pl-2">
          <CustomerSegmentChart data={data.charts_data.customer_segments} />
        </CardContent>
        <CardContent className="pl-2">
          <MonthlySalesChart data={data.charts_data.monthly_performance} />
        </CardContent>
      </Card>

      {/* Shadcn Tabs for Chart Selection */}
      <Tabs
        defaultValue="product-category"
        className="bg-gray-800/50 p-3 rounded-lg border border-gray-800/50 mb-4"
      >
        <TabsList>
          <TabsTrigger value="product-category">
            Product Category Performance
          </TabsTrigger>
          <TabsTrigger value="customer-segment">Customer Segments</TabsTrigger>
          <TabsTrigger value="monthly-performance">
            Monthly Sales Performance
          </TabsTrigger>
        </TabsList>

        {/* Tab Content */}
        <TabsContent value="product-category">
          <CardContent className="pl-2">
            <UnitsSoldPieChart
              data={data.charts_data.product_category_performance}
            />
          </CardContent>
        </TabsContent>
        <TabsContent value="customer-segment">
          <CardContent className="pl-2">
            <CustomerSegmentChart data={data.charts_data.customer_segments} />
          </CardContent>
        </TabsContent>
        <TabsContent value="monthly-performance">
          <CardContent className="pl-2">
            <MonthlySalesChart data={data.charts_data.monthly_performance} />
          </CardContent>
        </TabsContent>
      </Tabs>

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
    </div>
  );
}
