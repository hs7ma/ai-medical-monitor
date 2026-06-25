"use client";

import { useState, useEffect, useCallback } from "react";
import { useParams } from "next/navigation";
import { useI18n } from "@/i18n/context";
import { api } from "@/lib/api";
import { useWebSocket } from "@/lib/socket";
import { getVitalStatus, formatTime } from "@/lib/vitals";
import { Card, CardHeader } from "@/components/ui/Card";
import { VitalBadge } from "@/components/vitals/VitalBadge";
import { VitalsChart } from "@/components/charts/VitalsChart";

export default function BedDetailPage() {
  const { t } = useI18n();
  const params = useParams();
  const bedId = params.id as string;
  const [history, setHistory] = useState<any[]>([]);
  const [live, setLive] = useState({ spo2: 0, heart_rate: 0, temperature: 0 });
  const [minutes, setMinutes] = useState(60);
  const [loading, setLoading] = useState(true);

  const loadHistory = useCallback(async () => {
    try { setHistory(await api.getBedVitals(bedId, minutes)); } catch {} finally { setLoading(false); }
  }, [bedId, minutes]);

  useEffect(() => {
    loadHistory();
  }, [loadHistory, bedId]);

  useWebSocket((msg) => {
    if (msg.type === "vitals" && msg.data.bed_id === bedId) {
      const d = msg.data;
      setLive({ spo2: d.spo2 ?? 0, heart_rate: d.heart_rate ?? 0, temperature: d.temperature ?? 0 });
    }
  });

  const spo2Data = history.map((h) => ({ time: formatTime(h.time), value: h.spo2 }));
  const hrData = history.map((h) => ({ time: formatTime(h.time), value: h.heart_rate }));
  const tempData = history.map((h) => ({ time: formatTime(h.time), value: h.temperature }));

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-heading-md text-text">{t("bed.title")} <span className="text-accent">{bedId}</span></h1>
          <p className="mt-0.5 text-xs text-text-muted">Real-time vital signs</p>
        </div>
        <select value={minutes} onChange={(e) => setMinutes(Number(e.target.value))} className="input-base w-auto">
          <option value={60}>{t("bed.lastHour")}</option>
          <option value={360}>{t("bed.last6Hours")}</option>
          <option value={1440}>{t("bed.last24Hours")}</option>
        </select>
      </div>

      <div className="grid grid-cols-3 gap-2">
        <VitalBadge label={t("vitals.spo2")} value={live.spo2 || null} unit="%" status={getVitalStatus("spo2", live.spo2)} />
        <VitalBadge label={t("vitals.heartRate")} value={live.heart_rate || null} unit="bpm" status={getVitalStatus("hr", live.heart_rate)} />
        <VitalBadge label={t("vitals.temperature")} value={live.temperature || null} unit="°C" status={getVitalStatus("temp", live.temperature)} />
      </div>

      <Card>
        <CardHeader title={t("bed.history")} subtitle={`${history.length} readings`} />
        <div className="p-4">
          {loading ? <p className="py-6 text-center text-xs text-text-muted">Loading...</p> :
           history.length === 0 ? <p className="py-6 text-center text-xs text-text-muted">{t("bed.noData")}</p> :
           <div className="space-y-5">
             <ChartSection title={t("vitals.spo2")} unit="%"><VitalsChart data={spo2Data} color="#0ea5e9" label={t("vitals.spo2")} unit="%" domain={[80, 100]} /></ChartSection>
             <ChartSection title={t("vitals.heartRate")} unit="bpm"><VitalsChart data={hrData} color="#ef4444" label={t("vitals.heartRate")} unit="bpm" domain={[40, 140]} /></ChartSection>
             <ChartSection title={t("vitals.temperature")} unit="°C"><VitalsChart data={tempData} color="#f59e0b" label={t("vitals.temperature")} unit="°C" domain={[35, 40]} /></ChartSection>
           </div>}
        </div>
      </Card>
    </div>
  );
}

function ChartSection({ title, unit, children }: { title: string; unit: string; children: React.ReactNode }) {
  return (
    <div>
      <div className="mb-1 flex items-center justify-between">
        <h4 className="text-xs font-medium text-text">{title}</h4>
        <span className="text-[10px] text-text-muted">{unit}</span>
      </div>
      {children}
    </div>
  );
}
