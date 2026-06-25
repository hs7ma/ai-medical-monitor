"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useI18n } from "@/i18n/context";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/vitals";
import { Card, CardHeader } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input, Label, Select } from "@/components/ui/Input";
import { FileUploader } from "@/components/uploads/FileUploader";
import { getVitalStatus, statusColor } from "@/lib/vitals";
import { clsx } from "clsx";

const fileTypeIcons: Record<string, string> = { pdf: "PDF", image: "IMG" };
const emptyVitals = { spo2: "", heart_rate: "", temperature: "", source: "manual" };

export default function PatientDetailPage() {
  const { t } = useI18n();
  const params = useParams();
  const patientId = Number(params.id);
  const [patient, setPatient] = useState<any>(null);
  const [files, setFiles] = useState<any[]>([]);
  const [vitals, setVitals] = useState<any[]>([]);
  const [latestVital, setLatestVital] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [extracting, setExtracting] = useState<number | null>(null);
  const [vitalsForm, setVitalsForm] = useState(emptyVitals);
  const [submittingVitals, setSubmittingVitals] = useState(false);
  const [showVitalsForm, setShowVitalsForm] = useState(false);

  const loadAll = useCallback(async () => {
    try {
      const [p, f, v] = await Promise.all([
        api.getPatient(patientId),
        api.listUploads(patientId),
        api.getVitals(patientId, 20),
      ]);
      setPatient(p);
      setFiles(f);
      setVitals(v);
      setLatestVital(v[0] || null);
    } catch {} finally { setLoading(false); }
  }, [patientId]);

  useEffect(() => { loadAll(); }, [loadAll]);

  const handleDelete = async (fileId: number) => { if (!confirm(t("uploads.deleteConfirm"))) return; try { await api.deleteFile(fileId); loadAll(); } catch (err: any) { alert(err.message); } };
  const handleExtract = async (fileId: number) => { setExtracting(fileId); try { const res = await api.extractText(fileId); alert(res.extracted_text || "(empty)"); } catch (err: any) { alert(err.message); } finally { setExtracting(null); } };

  const handleVitalsSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmittingVitals(true);
    try {
      await api.submitVitals(patientId, {
        spo2: vitalsForm.spo2 ? parseFloat(vitalsForm.spo2) : null,
        heart_rate: vitalsForm.heart_rate ? parseFloat(vitalsForm.heart_rate) : null,
        temperature: vitalsForm.temperature ? parseFloat(vitalsForm.temperature) : null,
        source: vitalsForm.source,
      });
      setVitalsForm(emptyVitals);
      setShowVitalsForm(false);
      loadAll();
    } catch (err: any) { alert(err?.message || "Failed to submit vitals"); } finally { setSubmittingVitals(false); }
  };

  if (loading) return <div className="py-8 text-center text-sm text-text-muted">Loading...</div>;
  if (!patient) return <div className="py-8 text-center text-sm text-text-muted">Patient not found</div>;

  const spo2Status = latestVital?.spo2 ? getVitalStatus("spo2", latestVital.spo2) : "no-data";
  const hrStatus = latestVital?.heart_rate ? getVitalStatus("hr", latestVital.heart_rate) : "no-data";
  const tempStatus = latestVital?.temperature ? getVitalStatus("temp", latestVital.temperature) : "no-data";

  return (
    <div className="space-y-4">
      {/* Patient header */}
      <Card className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded bg-accent-light text-sm font-bold text-accent">{patient.name?.charAt(0)}</div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-base font-semibold text-text">{patient.name}</h1>
                <span className="rounded bg-accent-light px-1.5 py-0.5 text-[10px] font-bold text-accent">#{patient.id}</span>
              </div>
              <div className="mt-0.5 flex items-center gap-2 text-xs text-text-muted">
                <span>{patient.age}y</span><span>·</span><span className="capitalize">{patient.gender}</span>
                {patient.room && <><span>·</span><span>Room {patient.room}</span></>}
                <span>·</span><span>{patient.diagnosis || "—"}</span>
              </div>
              {patient.phone && <p className="mt-0.5 text-[11px] text-text-muted">Phone: {patient.phone}</p>}
              {patient.notes && <p className="mt-1 text-[11px] text-text-secondary">{patient.notes}</p>}
            </div>
          </div>
          <Link href={`/diagnosis`} className="shrink-0">
            <Button variant="ghost" className="text-xs">Start Diagnosis →</Button>
          </Link>
        </div>
      </Card>

      {/* Latest vitals */}
      <Card>
        <CardHeader title="Latest Vital Signs" subtitle={latestVital ? formatDate(latestVital.created_at) : "No readings yet"}>
          <Button variant="ghost" className="text-xs" onClick={() => setShowVitalsForm(!showVitalsForm)}>+ Add Reading</Button>
        </CardHeader>
        <div className="p-4">
          {showVitalsForm && (
            <form onSubmit={handleVitalsSubmit} className="mb-4 grid grid-cols-1 gap-3 rounded-lg border border-border bg-surface p-3 sm:grid-cols-4">
              <div><Label>SpO2 (%)</Label><Input type="number" step="0.1" value={vitalsForm.spo2} onChange={(e) => setVitalsForm({ ...vitalsForm, spo2: e.target.value })} placeholder="95" /></div>
              <div><Label>Heart Rate (bpm)</Label><Input type="number" value={vitalsForm.heart_rate} onChange={(e) => setVitalsForm({ ...vitalsForm, heart_rate: e.target.value })} placeholder="72" /></div>
              <div><Label>Temp (°C)</Label><Input type="number" step="0.1" value={vitalsForm.temperature} onChange={(e) => setVitalsForm({ ...vitalsForm, temperature: e.target.value })} placeholder="36.8" /></div>
              <div><Label>Source</Label><Select value={vitalsForm.source} onChange={(e) => setVitalsForm({ ...vitalsForm, source: e.target.value })}><option value="manual">Manual</option><option value="sensor">Sensor (ESP32)</option><option value="nurse">Nurse Reading</option></Select></div>
              <div className="sm:col-span-4 flex justify-end gap-2"><Button type="button" variant="ghost" onClick={() => setShowVitalsForm(false)}>Cancel</Button><Button type="submit" disabled={submittingVitals}>{submittingVitals ? "Saving..." : "Save Reading"}</Button></div>
            </form>
          )}

          {latestVital ? (
            <>
              <div className="grid grid-cols-3 gap-3">
                <VitalCard label="SpO2" value={latestVital.spo2} unit="%" status={spo2Status} />
                <VitalCard label="Heart Rate" value={latestVital.heart_rate} unit="bpm" status={hrStatus} />
                <VitalCard label="Temperature" value={latestVital.temperature} unit="°C" status={tempStatus} />
              </div>
              <p className="mt-3 text-[11px] text-text-muted">Source: {latestVital.source}</p>

              {vitals.length > 1 && (
                <div className="mt-4">
                  <p className="mb-2 text-xs font-medium uppercase text-text-muted">Recent Readings ({vitals.length})</p>
                  <div className="space-y-1 max-h-40 overflow-y-auto">
                    {vitals.map((v) => (
                      <div key={v.id} className="flex items-center justify-between rounded bg-surface/50 px-3 py-1.5 text-xs">
                        <span className="text-text-muted">{formatDate(v.created_at)}</span>
                        <span className="flex gap-3">
                          <span className={clsx("font-medium", spo2Color(v.spo2))}>{v.spo2 ? `${v.spo2}%` : "—"}</span>
                          <span className={clsx("font-medium", hrColor(v.heart_rate))}>{v.heart_rate ? `${v.heart_rate}bpm` : "—"}</span>
                          <span className={clsx("font-medium", tempColor(v.temperature))}>{v.temperature ? `${v.temperature}°C` : "—"}</span>
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          ) : (
            <p className="py-6 text-center text-xs text-text-muted">No vital signs recorded yet. Click "Add Reading" to input sensor data.</p>
          )}
        </div>
      </Card>

      {/* File upload */}
      <Card>
        <CardHeader title={t("uploads.upload")} />
        <div className="p-4"><FileUploader patientId={patientId} onUploaded={loadAll} /></div>
      </Card>

      {/* Files list */}
      <Card>
        <CardHeader title={t("uploads.title")} subtitle={`${files.length} files`} />
        {files.length === 0 ? <p className="px-4 py-8 text-center text-xs text-text-muted">{t("uploads.noFiles")}</p> : (
          <div className="divide-y divide-border">
            {files.map((f) => (
              <div key={f.id} className="flex items-center gap-3 px-4 py-2.5 hover:bg-surface/50 transition">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded bg-surface text-[10px] font-bold text-text-muted">{fileTypeIcons[f.file_type] || "?"}</div>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium text-text">{f.file_name}</p>
                  <p className="text-[11px] text-text-muted">{f.category} · {formatDate(f.created_at)}</p>
                </div>
                <div className="flex shrink-0 items-center gap-0.5">
                  <a href={api.fileUrl(f.id)} target="_blank" rel="noreferrer" className="rounded p-1.5 text-text-muted hover:bg-surface hover:text-text transition" title={t("uploads.view")}>
                    <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path strokeLinecap="round" strokeLinejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg>
                  </a>
                  <button onClick={() => handleExtract(f.id)} disabled={extracting === f.id} className="rounded p-1.5 text-text-muted hover:bg-surface hover:text-text transition disabled:opacity-50" title={t("uploads.extract")}>
                    <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                  </button>
                  <button onClick={() => handleDelete(f.id)} className="rounded p-1.5 text-text-muted hover:bg-danger-light hover:text-danger transition" title={t("uploads.delete")}>
                    <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>
    </div>
  );
}

function VitalCard({ label, value, unit, status }: { label: string; value: number | null; unit: string; status: string }) {
  const color = statusColor[status] || "#9ca3af";
  return (
    <div className="rounded-lg border border-border bg-white p-3 text-center">
      <p className="text-[10px] uppercase tracking-wide text-text-muted">{label}</p>
      <p className="mt-1 text-2xl font-bold" style={{ color }}>{value !== null && value !== undefined ? value : "—"}</p>
      <p className="text-[10px] text-text-muted">{unit}</p>
      <div className="mt-1.5 flex justify-center">
        <span className="h-1.5 w-1.5 rounded-full" style={{ backgroundColor: color }} />
      </div>
    </div>
  );
}

function spo2Color(v: number | null) {
  if (v === null || v === undefined) return "text-text-muted";
  if (v < 90) return "text-danger";
  if (v < 95) return "text-warning";
  return "text-success";
}
function hrColor(v: number | null) {
  if (v === null || v === undefined) return "text-text-muted";
  if (v < 50 || v > 110) return "text-danger";
  if (v < 60 || v > 100) return "text-warning";
  return "text-success";
}
function tempColor(v: number | null) {
  if (v === null || v === undefined) return "text-text-muted";
  if (v > 38) return "text-danger";
  if (v > 37.2) return "text-warning";
  return "text-success";
}
