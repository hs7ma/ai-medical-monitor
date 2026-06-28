"use client";

import { useState, useEffect, useCallback } from "react";
import { useI18n } from "@/i18n/context";
import { api } from "@/lib/api";
import { formatTime, formatDate } from "@/lib/vitals";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { clsx } from "clsx";
import { useToast } from "@/components/ui/Toast";

export default function AlertsPage() {
  const { t } = useI18n();
  const { showToast } = useToast();
  const [alerts, setAlerts] = useState<any[]>([]);
  const [filter, setFilter] = useState("active");
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => { try { setAlerts(await api.listAlerts(filter)); } catch {} finally { setLoading(false); } }, [filter]);
  useEffect(() => { setLoading(true); load(); }, [load]);

  const handleAck = async (id: number) => { try { await api.ackAlert(id); load(); } catch (err: any) { showToast({ type: "error", message: err.message }); } };

  const filters = [{ value: "active", label: t("alerts.active") }, { value: "acked", label: t("alerts.acked") }, { value: "all", label: t("alerts.all") }];
  const sevColor: Record<string, string> = { critical: "bg-danger-light text-danger", warning: "bg-warning-light text-warning", info: "bg-accent-light text-accent" };

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-heading-md text-text">{t("alerts.title")}</h1>
        <p className="mt-0.5 text-xs text-text-muted">{alerts.length} alerts</p>
      </div>

      <div className="inline-flex rounded-md border border-border bg-white p-0.5">
        {filters.map((f) => (
          <button key={f.value} onClick={() => setFilter(f.value)} className={clsx("rounded px-2.5 py-1 text-xs font-medium transition", filter === f.value ? "bg-text text-white" : "text-text-muted hover:text-text")}>{f.label}</button>
        ))}
      </div>

      {loading ? <Card><p className="py-8 text-center text-xs text-text-muted">Loading...</p></Card> :
       alerts.length === 0 ? <Card><p className="py-8 text-center text-xs text-text-muted">{t("alerts.noAlerts")}</p></Card> : (
        <Card>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left text-label uppercase text-text-secondary">
                <th className="px-4 py-2.5">{t("alerts.bed")}</th>
                <th className="px-4 py-2.5">{t("alerts.type")}</th>
                <th className="px-4 py-2.5">{t("alerts.severity")}</th>
                <th className="px-4 py-2.5">{t("alerts.message")}</th>
                <th className="px-4 py-2.5">{t("alerts.time")}</th>
                <th className="px-4 py-2.5 text-right">{t("alerts.status")}</th>
              </tr>
            </thead>
            <tbody>
              {alerts.map((a) => (
                <tr key={a.id} className="border-b border-border last:border-0 hover:bg-surface/50 transition">
                  <td className="px-4 py-2.5 font-mono text-xs text-text">{a.bed_id}</td>
                  <td className="px-4 py-2.5 text-text-secondary">{a.type}</td>
                  <td className="px-4 py-2.5"><span className={clsx("inline-block rounded px-1.5 py-0.5 text-[11px] font-medium capitalize", sevColor[a.severity] || sevColor.info)}>{a.severity}</span></td>
                  <td className="px-4 py-2.5 text-text">{a.message}</td>
                  <td className="px-4 py-2.5 text-[11px] text-text-muted">{formatDate(a.created_at)} {formatTime(a.created_at)}</td>
                  <td className="px-4 py-2.5 text-right">
                    {a.status === "acked" ? <span className="text-[11px] text-success">✓ {t("alerts.acked")}</span> : <Button className="px-2 py-0.5 text-[11px]" onClick={() => handleAck(a.id)}>{t("alerts.ack")}</Button>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}
