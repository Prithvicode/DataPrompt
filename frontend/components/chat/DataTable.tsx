import { TableRow } from "./types";

interface DataTableProps {
  data: TableRow[];
}

export default function DataTable({ data }: DataTableProps) {
  if (!data.length) return null;

  return (
    <div className="mt-6 overflow-x-auto bg-[#3C3C3C] border border-[#444444] rounded-2xl">
      <table className="min-w-full border-collapse text-gray-300">
        <thead>
          <tr className="bg-[#444444]">
            {Object.keys(data[0]).map((key) => (
              <th
                key={key}
                className="px-6 py-3 text-left font-medium text-gray-400"
              >
                {key}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, index) => (
            <tr key={index} className="bg-[#3C3C3C]">
              {Object.values(row).map((value, idx) => (
                <td
                  key={idx}
                  className="px-6 py-4 border-t border-[#444444] text-sm"
                >
                  {value !== null ? value : "N/A"}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
