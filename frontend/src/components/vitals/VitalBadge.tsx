"use client";

import { clsx } from "clsx";

export function VitalBadge({ label, value, unit, status }: {
  label: string;
  value: string | number | null;
  unit?: string;
  status: string;
}) {
  const colors: Record<string, { bg: string; text: string; dot: string }> = {
    normal: { bg: "bg-success-light", text: "text-success", dot: "bg-success" },
    warning: { bg: "bg-warning-light", text: "text-warning", dot: "bg-warning" },
    critical: { bg: "bg-danger-light", text: "text-danger", dot: "bg-danger" },
    "no-data": { bg: "bg-surface", text: "text-text-muted", dot: "bg-text-muted" },
  };
  const c = colors[status] || colors["no-data"];
  return (
    <div className={clsx("rounded-xl border border-border p-3", c.bg)}>
      <div className="flex items-center gap-1 text-[10px] font-medium uppercase tracking-wider text-text-secondary">
        <span className={clsx("h-1 w-1 rounded-full", c.dot)} />
        {label}
      </div>
      <div className={clsx("mt-1 text-xl font-bold tabular-nums", c.text)}>
        {value !== null && value !== undefined && value !== "" ? value : "—"}
        {unit && value ? <span className="ml-0.5 text-xs font-normal opacity-70">{unit}</span> : null}
      </div>
    </div>
  );
}
