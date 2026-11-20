export function formatIndianNumber(value: number): string {
  if (!Number.isFinite(value)) return "—";
  return new Intl.NumberFormat("en-IN", {
    maximumFractionDigits: 2,
  }).format(value);
}

export function formatCompactIndian(value: number): string {
  if (!Number.isFinite(value)) return "—";
  const magnitude = Math.abs(value);
  if (magnitude >= 1e7) return `${(value / 1e7).toFixed(2)} Cr`;
  if (magnitude >= 1e5) return `${(value / 1e5).toFixed(2)} L`;
  return formatIndianNumber(value);
}

export function formatLatency(value?: number): string {
  if (value === undefined || !Number.isFinite(value)) return "Unavailable";
  return `${formatIndianNumber(value)} ms`;
}
