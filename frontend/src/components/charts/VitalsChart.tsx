"use client";

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from "recharts";

interface VitalsChartProps {
  data: { time: string; value: number }[];
  color: string;
  label: string;
  unit: string;
  minNormal?: number;
  maxNormal?: number;
  domain?: [number, number];
}

export function VitalsChart({ data, color, label, unit, minNormal, maxNormal, domain }: VitalsChartProps) {
  return (
    <div className="h-44 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 4, right: 12, left: -16, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" vertical={false} />
          <XAxis dataKey="time" stroke="#9ca3af" fontSize={10} tickLine={false} axisLine={{ stroke: "#e5e7eb" }} />
          <YAxis stroke="#9ca3af" fontSize={10} domain={domain || ["auto", "auto"]} tickLine={false} axisLine={false} />
          <Tooltip
            contentStyle={{ backgroundColor: "#fff", border: "1px solid #e5e7eb", borderRadius: 6, fontSize: 12, boxShadow: "0 2px 8px rgb(0 0 0 / 0.06)" }}
            labelStyle={{ color: "#6b7280", fontSize: 11 }}
            formatter={(v: number) => [`${v} ${unit}`, label]}
          />
          {minNormal !== undefined && <ReferenceLine y={minNormal} stroke="#d1d5db" strokeDasharray="4 4" />}
          {maxNormal !== undefined && <ReferenceLine y={maxNormal} stroke="#d1d5db" strokeDasharray="4 4" />}
          <Line type="monotone" dataKey="value" stroke={color} strokeWidth={2} dot={false} isAnimationActive={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
