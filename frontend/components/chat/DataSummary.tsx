interface DataSummaryProps {
  data: Record<string, any>;
}

export default function DataSummary({ data }: DataSummaryProps) {
  if (!data || !data.summary_stats) return null;

  return (
    <div className="mt-6 p-6 bg-[#3C3C3C] border border-[#444444] rounded-2xl">
      <h3 className="text-xl font-bold mb-4 text-[#2A9FD6]">Data Summary</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {Object.entries(data.summary_stats).map(([column, stats]) => (
          <div key={column} className="space-y-2">
            <h4 className="font-semibold text-gray-300">{column}</h4>
            <ul className="list-disc pl-5 space-y-1">
              {typeof stats === "object" && stats !== null
                ? Object.entries(stats).map(([key, value]) => (
                    <li key={key} className="text-sm text-gray-400">
                      {key}: {value !== null ? value : "N/A"}
                    </li>
                  ))
                : String(stats)}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
}
