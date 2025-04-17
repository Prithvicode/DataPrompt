import type { TableRow } from "./types";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow as UITableRow,
} from "@/components/ui/table";

interface DataTableProps {
  data: TableRow[];
}

export default function DataTable({ data }: DataTableProps) {
  if (!data || data.length === 0) return null;

  // Get column headers from the first row
  const headers = Object.keys(data[0]);

  return (
    <div className="rounded-md border border-gray-800 bg-gray-900">
      <div className="max-h-[400px] overflow-auto">
        <Table>
          <TableHeader className="sticky top-0 bg-gray-800 z-10">
            <UITableRow>
              {headers.map((header) => (
                <TableHead
                  key={header}
                  className="whitespace-nowrap text-gray-300 font-medium"
                >
                  {header}
                </TableHead>
              ))}
            </UITableRow>
          </TableHeader>
          <TableBody>
            {data.map((row, rowIndex) => (
              <UITableRow
                key={rowIndex}
                className="border-gray-800 hover:bg-gray-800/50"
              >
                {headers.map((header) => (
                  <TableCell
                    key={`${rowIndex}-${header}`}
                    className="whitespace-nowrap text-gray-300"
                  >
                    {row[header]}
                  </TableCell>
                ))}
              </UITableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}

// import { TableRow } from "./types";

// interface DataTableProps {
//   data: TableRow[];
// }

// export default function DataTable({ data }: DataTableProps) {
//   if (!data.length) return null;

//   return (
//     <div className="mt-6 overflow-x-auto bg-[#3C3C3C] border border-[#444444] rounded-2xl">
//       <table className="min-w-full border-collapse text-gray-300">
//         <thead>
//           <tr className="bg-[#444444]">
//             {Object.keys(data[0]).map((key) => (
//               <th
//                 key={key}
//                 className="px-6 py-3 text-left font-medium text-gray-400"
//               >
//                 {key}
//               </th>
//             ))}
//           </tr>
//         </thead>
//         <tbody>
//           {data.map((row, index) => (
//             <tr key={index} className="bg-[#3C3C3C]">
//               {Object.values(row).map((value, idx) => (
//                 <td
//                   key={idx}
//                   className="px-6 py-4 border-t border-[#444444] text-sm"
//                 >
//                   {value !== null ? value : "N/A"}
//                 </td>
//               ))}
//             </tr>
//           ))}
//         </tbody>
//       </table>
//     </div>
//   );
// }
