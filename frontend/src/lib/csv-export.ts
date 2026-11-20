function escapeCSVCell(value: string | number | boolean | null): string {
  if (value === null || value === undefined) return "";
  const text = String(value);
  return /[",\r\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
}

export function exportToCSV(
  columns: string[],
  rows: (string | number | boolean | null)[][],
  filename: string
): void {
  const csv = [columns, ...rows]
    .map((row) => row.map(escapeCSVCell).join(","))
    .join("\r\n");
  const blob = new Blob(["\uFEFF", csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}
