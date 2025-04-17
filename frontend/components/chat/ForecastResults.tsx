import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface ForecastResultsProps {
  data: any;
}

export default function ForecastResults({ data }: ForecastResultsProps) {
  if (!data) return null;

  return (
    <Card className="bg-gray-900 border-gray-800">
      <CardHeader className="pb-2">
        <CardTitle className="text-base text-blue-400">
          Forecast Results
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {Object.entries(data).map(([key, value]) => (
            <div key={key} className="grid grid-cols-2 gap-2">
              <div className="font-medium text-sm text-gray-300">{key}</div>
              <div className="text-sm text-gray-400">{String(value)}</div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

// import React from "react";

// interface ForecastResultsProps {
//   data: {
//     predictions: number[];
//     metrics: {
//       mse: number | null;
//       r2: number | null;
//     };
//     plot: string;
//   };
// }

// const ForecastResults: React.FC<ForecastResultsProps> = ({ data }) => {
//   return (
//     <div className="space-y-4">
//       <div className="bg-[#2A2A2A] rounded-lg p-4">
//         <h3 className="text-lg font-semibold text-[#2A9FD6] mb-4">
//           Forecast Results
//         </h3>

//         {/* Metrics */}
//         <div className="grid grid-cols-2 gap-4 mb-4">
//           <div className="bg-[#333333] p-3 rounded">
//             <p className="text-sm text-gray-400">Mean Squared Error</p>
//             <p className="text-xl font-semibold">
//               {data.metrics.mse ? data.metrics.mse.toFixed(2) : "N/A"}
//             </p>
//           </div>
//           <div className="bg-[#333333] p-3 rounded">
//             <p className="text-sm text-gray-400">R-squared Score</p>
//             <p className="text-xl font-semibold">
//               {data.metrics.r2 ? data.metrics.r2.toFixed(2) : "N/A"}
//             </p>
//           </div>
//         </div>

//         {/* Predictions Plot */}
//         <div className="mt-4">
//           <h4 className="text-md font-semibold mb-2">
//             Predictions Visualization
//           </h4>
//           <div className="bg-[#333333] p-4 rounded">
//             <img
//               src={`data:image/png;base64,${data.plot}`}
//               alt="Forecast Predictions"
//               className="w-full h-auto"
//             />
//           </div>
//         </div>

//         {/* Predictions List */}
//         <div className="mt-4">
//           <h4 className="text-md font-semibold mb-2">Predictions</h4>
//           <div className="bg-[#333333] p-4 rounded max-h-40 overflow-y-auto">
//             <div className="grid grid-cols-2 gap-2">
//               {data.predictions.map((prediction, index) => (
//                 <div key={index} className="text-sm">
//                   <span className="text-gray-400">Point {index + 1}:</span>{" "}
//                   <span className="font-medium">{prediction.toFixed(2)}</span>
//                 </div>
//               ))}
//             </div>
//           </div>
//         </div>
//       </div>
//     </div>
//   );
// };

// export default ForecastResults;
