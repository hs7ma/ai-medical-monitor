"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useI18n } from "@/i18n/context";
import { api } from "@/lib/api";
import { useWebSocket } from "@/lib/socket";
import { getVitalStatus, statusColor } from "@/lib/vitals";
import { Card } from "@/components/ui/Card";
import { VitalBadge } from "@/components/vitals/VitalBadge";

interface BedVitals { spo2: number | null; heart_rate: number | null; temperature: number | null; }
interface BedsState { [bedId: string]: BedVitals; }

export default function DashboardPage() {
  const { t } = useI18n();
  const [beds, setBeds] = useState<any[]>([]);
  const [vitals, setVitals] = useState<BedsState>({});
  const [loading, setLoading] = useState(true);

  const loadBeds = useCallback(async () => {
    try { setBeds(await api.listBeds()); } catch {} finally { setLoading(false); }
  }, []);

  useEffect(() => {
    loadBeds();
  }, [loadBeds]);

  useWebSocket((msg) => {
    if (msg.type === "vitals") {
      const d = msg.data;
      setVitals((prev) => ({ ...prev, [d.bed_id]: { spo2: d.spo2 ?? null, heart_rate: d.heart_rate ?? null, temperature: d.temperature ?? null } }));
    }
  });

  const getOverallStatus = (v: BedVitals): string => {
    const s = [getVitalStatus("spo2", v.spo2), getVitalStatus("hr", v.heart_rate), getVitalStatus("temp", v.temperature)];
    if (s.includes("critical")) return "critical";
    if (s.includes("warning")) return "warning";
    if (s.includes("normal")) return "normal";
    return "no-data";
  };

  if (loading) return <div className="py-8 text-center text-text-muted text-sm">Loading...</div>;

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-heading-md text-text">{t("dashboard.title")}</h1>
        <p className="mt-0.5 text-xs text-text-muted">Real-time patient monitoring</p>
      </div>

      {beds.length === 0 ? (
        <Card><p className="py-8 text-center text-sm text-text-muted">{t("dashboard.noBeds")}</p></Card>
      ) : (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {beds.map((bed) => {
            const v = vitals[bed.id] || { spo2: null, heart_rate: null, temperature: null };
            const overall = getOverallStatus(v);
            return (
              <Link key={bed.id} href={`/beds/${bed.id}`}>
                <div className="card-hover p-4">
                  <div className="mb-3 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: statusColor[overall] }} />
                      <span className="text-sm font-semibold text-text">{bed.id}</span>
                      {bed.room && <span className="text-xs text-text-muted">{bed.room}</span>}
                    </div>
                    <span className="text-xs text-text-muted">→</span>
                  </div>
                  {bed.status === "occupied" ? (
                    <div className="grid grid-cols-3 gap-2">
                      <VitalBadge label={t("vitals.spo2")} value={v.spo2} unit="%" status={getVitalStatus("spo2", v.spo2)} />
                      <VitalBadge label={t("vitals.heartRate")} value={v.heart_rate} unit="bpm" status={getVitalStatus("hr", v.heart_rate)} />
                      <VitalBadge label={t("vitals.temperature")} value={v.temperature} unit="°C" status={getVitalStatus("temp", v.temperature)} />
                    </div>
                  ) : (
                    <div className="rounded-md bg-surface py-3 text-center text-xs text-text-muted">{t("dashboard.available")}</div>
                  )}
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
