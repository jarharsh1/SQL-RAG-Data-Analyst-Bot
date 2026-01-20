import React from 'react';

interface DataTableProps {
  data: Array<Record<string, any>>;
  columns: string[];
}

export default function DataTable({ data, columns }: DataTableProps) {
  if (!data || data.length === 0) {
    return (
      <div className="text-center py-8 text-gray-400">
        No data to display
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-700">
      <table className="w-full text-sm">
        <thead className="bg-slate-700/50">
          <tr>
            {columns.map((column) => (
              <th
                key={column}
                className="px-4 py-3 text-left font-semibold text-purple-300 uppercase tracking-wider"
              >
                {column}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-700">
          {data.map((row, rowIdx) => (
            <tr
              key={rowIdx}
              className="hover:bg-slate-700/30 transition-colors"
            >
              {columns.map((column) => (
                <td
                  key={column}
                  className="px-4 py-3 text-gray-300 whitespace-nowrap"
                >
                  {formatValue(row[column])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function formatValue(value: any): string {
  if (value === null || value === undefined) {
    return '—';
  }

  if (typeof value === 'number') {
    // Format large numbers with commas
    if (Math.abs(value) >= 1000) {
      return value.toLocaleString('en-US', {
        maximumFractionDigits: 2,
      });
    }
    return value.toString();
  }

  if (typeof value === 'boolean') {
    return value ? 'Yes' : 'No';
  }

  return String(value);
}
