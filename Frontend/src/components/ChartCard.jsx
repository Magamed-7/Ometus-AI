import { useState } from "react";
import { useT } from "../lib/i18n.jsx";
import Card from "./Card.jsx";

// У каждого графика есть таблица-двойник. Это не украшение: график на canvas
// скринридер не читает вообще, а по цифрам иногда нужно свериться точно.
export default function ChartCard({ title, hint, columns, rows, height = 280, children }) {
  const t = useT();
  const [asTable, setAsTable] = useState(false);
  const empty = !rows || rows.length === 0;

  return (
    <Card className="p-md">
      <div className="mb-md flex flex-wrap items-start justify-between gap-sm">
        <div>
          <h3 className="text-body-lg font-bold text-on-surface">{title}</h3>
          {hint && <p className="text-label-md text-on-surface-variant">{hint}</p>}
        </div>
        <button
          type="button"
          onClick={() => setAsTable((prev) => !prev)}
          aria-pressed={asTable}
          className="flex items-center gap-xs rounded-full border border-outline-variant px-sm py-1.5 text-label-md font-semibold text-on-surface-variant transition-colors hover:bg-surface-container"
        >
          <span aria-hidden="true" className="material-symbols-outlined text-base">
            {asTable ? "monitoring" : "table_rows"}
          </span>
          {asTable ? t("analytics.showChart") : t("analytics.showTable")}
        </button>
      </div>

      {empty ? (
        <p className="py-lg text-center text-body-md text-on-surface-variant">
          {t("analytics.noData")}
        </p>
      ) : asTable ? (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-body-md">
            <thead>
              <tr className="border-b border-outline-variant text-label-md text-on-surface-variant">
                {columns.map((column) => (
                  <th key={column} scope="col" className="py-2 pr-md font-semibold">
                    {column}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, index) => (
                <tr key={index} className="border-b border-outline-variant/50 text-on-surface">
                  {row.map((cell, cellIndex) => (
                    <td key={cellIndex} className="py-2 pr-md">
                      {cell}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div style={{ height }}>{children}</div>
      )}
    </Card>
  );
}
