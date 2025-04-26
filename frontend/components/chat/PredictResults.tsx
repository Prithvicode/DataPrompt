import { Card, CardContent } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export const PredictionResults = ({
  data,
  mae,
  r2,
  visualization,
}: {
  data: any[];
  mae: number;
  r2: number;
  visualization?: {
    type: string;
    data: any[];
    x: string;
    y: string[] | string;
    title: string;
    xLabel: string;
    yLabel: string;
  };
}) => {
  return (
    <div className="space-y-6 p-4">
      <Card className="bg-white shadow-lg rounded-2xl border border-gray-200">
        <CardContent className="p-4">
          <div className="text-2xl font-semibold text-gray-900">
            Model Evaluation
          </div>
          <div className="text-base mt-2 text-gray-700">
            <p>
              MAE (Mean Absolute Error):{" "}
              <span className="font-semibold text-green-500">
                {mae.toFixed(2)}
              </span>
            </p>
            <p>
              R² Score:{" "}
              <span className="font-semibold text-blue-500">
                {r2.toFixed(4)}
              </span>
            </p>
          </div>
        </CardContent>
      </Card>

      {visualization &&
        Array.isArray(visualization.y) &&
        visualization.y.length >= 2 &&
        visualization.data?.length > 0 && (
          <Tabs defaultValue="chart" className="w-full">
            <TabsList className="bg-gray-100 p-1 rounded-xl mb-2">
              <TabsTrigger
                value="chart"
                className="text-gray-900 hover:bg-gray-200"
              >
                Chart
              </TabsTrigger>
              <TabsTrigger
                value="table"
                className="text-gray-900 hover:bg-gray-200"
              >
                Table
              </TabsTrigger>
            </TabsList>

            <TabsContent value="chart">
              <Card className="bg-white shadow-lg rounded-2xl border border-gray-200">
                <CardContent className="p-4">
                  <div className="text-2xl font-semibold text-gray-900 mb-4">
                    {visualization.title}
                  </div>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={visualization.data}>
                      <XAxis dataKey={visualization.x} stroke="#666" />
                      <YAxis stroke="#666" />
                      <Tooltip />
                      <Legend />
                      <Line
                        type="monotone"
                        dataKey={visualization.y[0]}
                        stroke="#3B82F6"
                        strokeWidth={2}
                        name="Actual Revenue"
                      />
                      <Line
                        type="monotone"
                        dataKey={visualization.y[1]}
                        stroke="#F97316"
                        strokeWidth={2}
                        name="Predicted Revenue"
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="table">
              <Card className="bg-white shadow-lg rounded-2xl overflow-auto border border-gray-200">
                <CardContent className="p-4">
                  <div className="text-2xl font-semibold text-gray-900 mb-4">
                    Prediction Details
                  </div>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="bg-gray-100">Order ID</TableHead>
                        <TableHead className="bg-gray-100">Product</TableHead>
                        <TableHead className="bg-gray-100">Region</TableHead>
                        <TableHead className="bg-gray-100">Revenue</TableHead>
                        <TableHead className="bg-gray-100">Predicted</TableHead>
                        <TableHead className="bg-gray-100">Error</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {data.map((row, i) => (
                        <TableRow key={i} className="hover:bg-gray-50">
                          <TableCell>{row.OrderID}</TableCell>
                          <TableCell>{row.ProductName}</TableCell>
                          <TableCell>{row.Region}</TableCell>
                          <TableCell className="text-gray-700">
                            Nrs.{row.ActualRevenue.toFixed(2)}
                          </TableCell>
                          <TableCell className="text-orange-500">
                            Nrs.{row.PredictedRevenue.toFixed(2)}
                          </TableCell>
                          <TableCell
                            className={
                              row.PredictionError > 0
                                ? "text-red-500"
                                : "text-green-500"
                            }
                          >
                            {row.PredictionError.toFixed(2)}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        )}
    </div>
  );
};

export default PredictionResults;
