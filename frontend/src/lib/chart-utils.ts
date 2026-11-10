type ChartDatum = Record<string, string | number | boolean | null>;

export type ChartInfo =
  | { chartType: "none" }
  | { chartType: "kpi"; kpiLabel: string; kpiValue: string | number | boolean | null }
  | {
      chartType: "bar" | "line";
      categoryKey: string;
      dataKey: string;
      data: ChartDatum[];
    };

export function detectChartType(
  columns: string[],
  rows: (string | number | boolean | null)[][]
): ChartInfo {
  if (columns.length === 1 && rows.length === 1) {
    return {
      chartType: "kpi",
      kpiLabel: columns[0],
      kpiValue: rows[0][0],
    };
  }

  if (columns.length < 2 || rows.length === 0) return { chartType: "none" };

  const numericColumnIndex = columns.findIndex((_, index) =>
    rows.some((row) => typeof row[index] === "number")
  );
  if (numericColumnIndex < 0) return { chartType: "none" };

  const categoryColumnIndex = columns.findIndex(
    (_, index) => index !== numericColumnIndex
  );
  const categoryKey = columns[categoryColumnIndex];
  const dataKey = columns[numericColumnIndex];
  const data = rows.map((row) => {
    const datum: ChartDatum = {};
    columns.forEach((column, index) => {
      datum[column] = row[index];
    });
    return datum;
  });
  const isTemporal = /date|year|month|time|quarter/i.test(categoryKey);

  return {
    chartType: isTemporal ? "line" : "bar",
    categoryKey,
    dataKey,
    data,
  };
}
