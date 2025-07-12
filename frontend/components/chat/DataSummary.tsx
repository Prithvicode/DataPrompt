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
import {
  BarChart,
  Database,
  AlertCircle,
  Calendar,
  Map,
  Tag,
  Users,
} from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../ui/tabs";
import { MonthlyPerformanceChart } from "../charts/montly-performance-chart";
import { ProductPerformanceChart } from "../charts/product-performance-chart";
import { RegionalSalesChart } from "../charts/regional-sales-chart";
import { CustomerSegmentChart } from "../charts/customer-segment-chart";
import { PromotionImpactChart } from "../charts/promotional-impact-chart";
import { DailyOrdersChart } from "../charts/daily-orders-chart";

interface DataSummaryProps {
  data: {
    overview: any;
    insights: any;
    visual_data: any;
  };
}

export default function DataSummary({ data }: DataSummaryProps) {
  const { overview, insights, visual_data } = data;

  return (
    <div className="space-y-4 text-gray-800 p-2 custom-scrollbar">
      {/* Dataset Overview */}
      <Card className="bg-white border border-gray-200">
        <CardHeader className="pb-1">
          <div className="flex items-center gap-2">
            <Database className="h-4 w-4 text-blue-500" />
            <CardTitle className="text-base">Dataset Overview</CardTitle>
          </div>
        </CardHeader>
        <CardContent className="grid grid-cols-3 gap-2 pt-2">
          {[
            { label: "Total Records", value: overview?.total_records || 0 },
            { label: "Total Columns", value: overview?.total_columns || 0 },
            { label: "Duplicates", value: overview?.duplicate_records || 0 },
            {
              label: "Missing Values",
              value: Object.values(overview?.missing_data || {}).reduce(
                (a: number, b) => a + (b as number),
                0
              ),
            },
            {
              label: "Numeric Columns",
              value: Object.values(overview?.data_types || {}).filter((type) =>
                ["int64", "float64"].includes(type as string)
              ).length,
            },
            {
              label: "Categorical Columns",
              value: Object.values(overview?.data_types || {}).filter(
                (type) => (type as string) === "object"
              ).length,
            },
          ].map((item) => (
            <div
              key={item.label}
              className="bg-gray-100 p-3 rounded-lg border border-gray-300 hover:border-blue-500/30 transition-colors"
            >
              <div className="text-xs text-gray-500">{item.label}</div>
              <div className="text-lg font-semibold">{item.value}</div>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Main Insights Tabs */}
      <Tabs
        defaultValue="monthly"
        className="bg-white border border-gray-200 rounded-lg"
      >
        <TabsList className="grid grid-cols-4 gap-1 p-1 bg-gray-100 rounded-lg">
          <TabsTrigger value="monthly" className="flex items-center gap-1">
            <Calendar className="h-4 w-4" /> Monthly
          </TabsTrigger>
          <TabsTrigger value="products" className="flex items-center gap-1">
            <Tag className="h-4 w-4" /> Products
          </TabsTrigger>
          <TabsTrigger value="regions" className="flex items-center gap-1">
            <Map className="h-4 w-4" /> Regions
          </TabsTrigger>
          <TabsTrigger value="customers" className="flex items-center gap-1">
            <Users className="h-4 w-4" /> Customers
          </TabsTrigger>
        </TabsList>

        <TabsContent value="monthly">
          <CardContent className="pt-3">
            <MonthlyPerformanceChart data={visual_data?.monthly_performance} />
          </CardContent>
        </TabsContent>

        <TabsContent value="products">
          <CardContent className="pt-3">
            <ProductPerformanceChart data={visual_data?.product_performance} />
          </CardContent>
        </TabsContent>

        <TabsContent value="regions">
          <CardContent className="pt-3">
            <RegionalSalesChart data={visual_data?.regional_performance} />
          </CardContent>
        </TabsContent>

        <TabsContent value="customers">
          <CardContent className="pt-3">
            <CustomerSegmentChart data={visual_data?.customer_segments} />
          </CardContent>
        </TabsContent>
      </Tabs>

      {/* Secondary Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {visual_data?.promotion_impact && (
          <Card className="bg-white border border-gray-200">
            <CardHeader className="pb-1">
              <div className="flex items-center gap-2">
                <AlertCircle className="h-4 w-4 text-purple-500" />
                <CardTitle className="text-base">Promotion Impact</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="pt-2">
              <PromotionImpactChart data={visual_data.promotion_impact} />
            </CardContent>
          </Card>
        )}

        {visual_data?.daily_orders && (
          <Card className="bg-white border border-gray-200">
            <CardHeader className="pb-1">
              <div className="flex items-center gap-2">
                <Calendar className="h-4 w-4 text-green-500" />
                <CardTitle className="text-base">Daily Order Trends</CardTitle>
              </div>
            </CardHeader>
            <CardContent className="pt-2">
              <DailyOrdersChart data={visual_data.daily_orders} />
            </CardContent>
          </Card>
        )}
      </div>

      {/* Numeric Statistics Table */}
      {insights?.key_metrics && (
        <Card className="bg-white border border-gray-200">
          <CardHeader className="pb-1">
            <div className="flex items-center gap-2">
              <BarChart className="h-4 w-4 text-blue-500" />
              <CardTitle className="text-base">Numeric Statistics</CardTitle>
            </div>
          </CardHeader>
          <CardContent className="pt-2">
            <div className="overflow-x-auto rounded-lg border border-gray-200">
              <Table>
                <TableHeader className="bg-gray-100">
                  <TableRow>
                    {["Metric", "Mean", "Min", "Max", "Std Dev"].map(
                      (header) => (
                        <TableHead key={header} className="text-gray-700">
                          {header}
                        </TableHead>
                      )
                    )}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {Object.entries(insights.key_metrics).map(
                    ([metric, stats]: [string, any]) => (
                      <TableRow key={metric}>
                        <TableCell className="font-medium">{metric}</TableCell>
                        <TableCell>{stats.mean?.toFixed(2)}</TableCell>
                        <TableCell>{stats.min?.toFixed(2)}</TableCell>
                        <TableCell>{stats.max?.toFixed(2)}</TableCell>
                        <TableCell>{stats.std?.toFixed(2)}</TableCell>
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
