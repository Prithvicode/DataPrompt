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
  intentType?: string; // new optional prop
}

export default function DataTable({ data, intentType }: DataTableProps) {
  if (!data || data.length === 0) return null;

  // Get column headers from the first row
  const headers = Object.keys(data[0]);

  return (
    <div className="rounded-md border border-gray-200 bg-white shadow-lg">
      {intentType && (
        <div className="px-4 pt-4 pb-2 border-b border-gray-200 bg-gray-50">
          <h2 className="text-lg font-semibold text-gray-800">
            <span className="text-blue-600 capitalize">{intentType}</span>
          </h2>
        </div>
      )}

      <div className="max-h-[400px] overflow-auto">
        <Table>
          <TableHeader className="sticky top-0 bg-gray-100 z-10">
            <UITableRow>
              {headers.map((header) => (
                <TableHead
                  key={header}
                  className="whitespace-nowrap text-gray-800 font-medium"
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
                className="border-gray-200 hover:bg-gray-100/50"
              >
                {headers.map((header) => (
                  <TableCell
                    key={`${rowIndex}-${header}`}
                    className="whitespace-nowrap text-gray-800"
                  >
                    {row[header] ?? "N/A"}
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
