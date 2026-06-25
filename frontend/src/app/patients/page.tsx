"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useI18n } from "@/i18n/context";
import { api } from "@/lib/api";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input, Label, Select } from "@/components/ui/Input";

const emptyForm = { name: "", age: "", gender: "male", phone: "", room: "", diagnosis: "", notes: "" };

export default function PatientsPage() {
  const { t } = useI18n();
  const [patients, setPatients] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [newPatient, setNewPatient] = useState(emptyForm);
  const [createdId, setCreatedId] = useState<number | null>(null);

  const load = useCallback(async () => { try { setPatients(await api.listPatients()); } catch {} finally { setLoading(false); } }, []);
  useEffect(() => { load(); }, [load]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const payload: any = {
        name: newPatient.name,
        age: newPatient.age ? Number(newPatient.age) : null,
        gender: newPatient.gender,
        phone: newPatient.phone || null,
        room: newPatient.room || null,
        diagnosis: newPatient.diagnosis || null,
        notes: newPatient.notes || null,
      };
      const created = await api.createPatient(payload);
      setCreatedId(created.id);
      setNewPatient(emptyForm);
      setShowForm(false);
      load();
      setTimeout(() => setCreatedId(null), 5000);
    } catch (err: any) { alert(err?.message || "Failed to create patient"); }
  };

  if (loading) return <div className="py-8 text-center text-sm text-text-muted">Loading...</div>;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-heading-md text-text">{t("patients.title")}</h1>
          <p className="mt-0.5 text-xs text-text-muted">{patients.length} patients registered</p>
        </div>
        <Button onClick={() => setShowForm(!showForm)}>{showForm ? "Cancel" : `+ ${t("patients.addPatient")}`}</Button>
      </div>

      {createdId && (
        <div className="animate-fade-in rounded-lg border border-success/30 bg-success-light px-4 py-3 text-sm text-success">
          Patient registered successfully! ID: <span className="font-bold">#{createdId}</span>
          <Link href={`/patients/${createdId}`} className="mr-2 font-medium underline">View profile →</Link>
        </div>
      )}

      {showForm && (
        <Card className="animate-fade-in">
          <form onSubmit={handleCreate} className="grid grid-cols-1 gap-3 p-4 sm:grid-cols-2">
            <div className="sm:col-span-2">
              <h3 className="text-sm font-semibold text-text">Register New Patient</h3>
              <p className="mt-0.5 text-[11px] text-text-muted">A unique patient ID will be auto-generated upon registration</p>
            </div>
            <div><Label required>{t("patients.name")}</Label><Input value={newPatient.name} onChange={(e) => setNewPatient({ ...newPatient, name: e.target.value })} required placeholder="Full name" /></div>
            <div><Label>{t("patients.age")}</Label><Input type="number" value={newPatient.age} onChange={(e) => setNewPatient({ ...newPatient, age: e.target.value })} placeholder="Age in years" /></div>
            <div><Label>{t("patients.gender")}</Label><Select value={newPatient.gender} onChange={(e) => setNewPatient({ ...newPatient, gender: e.target.value })}><option value="male">Male</option><option value="female">Female</option></Select></div>
            <div><Label>Phone</Label><Input value={newPatient.phone} onChange={(e) => setNewPatient({ ...newPatient, phone: e.target.value })} placeholder="Contact number" /></div>
            <div><Label>Room</Label><Input value={newPatient.room} onChange={(e) => setNewPatient({ ...newPatient, room: e.target.value })} placeholder="Room number" /></div>
            <div><Label>{t("patients.diagnosis")}</Label><Input value={newPatient.diagnosis} onChange={(e) => setNewPatient({ ...newPatient, diagnosis: e.target.value })} placeholder="Initial diagnosis" /></div>
            <div className="sm:col-span-2"><Label>Notes</Label><Input value={newPatient.notes} onChange={(e) => setNewPatient({ ...newPatient, notes: e.target.value })} placeholder="Additional notes (allergies, medications, etc.)" /></div>
            <div className="sm:col-span-2 flex justify-end gap-2"><Button type="button" variant="ghost" onClick={() => setShowForm(false)}>Cancel</Button><Button type="submit">Register Patient</Button></div>
          </form>
        </Card>
      )}

      {patients.length === 0 ? (
        <Card><p className="py-8 text-center text-sm text-text-muted">{t("patients.noPatients")}</p></Card>
      ) : (
        <Card>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border text-left text-label uppercase text-text-secondary">
                <th className="px-4 py-2.5">ID</th>
                <th className="px-4 py-2.5">{t("patients.name")}</th>
                <th className="px-4 py-2.5">{t("patients.age")}</th>
                <th className="px-4 py-2.5">{t("patients.gender")}</th>
                <th className="px-4 py-2.5">Room</th>
                <th className="px-4 py-2.5">{t("patients.diagnosis")}</th>
                <th className="px-4 py-2.5 text-right">{t("patients.actions")}</th>
              </tr>
            </thead>
            <tbody>
              {patients.map((p) => (
                <tr key={p.id} className="border-b border-border last:border-0 hover:bg-surface/50 transition">
                  <td className="px-4 py-2.5"><span className="rounded bg-accent-light px-1.5 py-0.5 text-[10px] font-bold text-accent">#{p.id}</span></td>
                  <td className="px-4 py-2.5">
                    <div className="flex items-center gap-2">
                      <div className="flex h-6 w-6 items-center justify-center rounded bg-accent-light text-[10px] font-semibold text-accent">{p.name?.charAt(0)}</div>
                      <span className="font-medium text-text">{p.name}</span>
                    </div>
                  </td>
                  <td className="px-4 py-2.5 text-text">{p.age ?? "—"}</td>
                  <td className="px-4 py-2.5 text-text-secondary capitalize">{p.gender ?? "—"}</td>
                  <td className="px-4 py-2.5 text-text-secondary">{p.room ?? "—"}</td>
                  <td className="px-4 py-2.5 text-text-secondary">{p.diagnosis ?? "—"}</td>
                  <td className="px-4 py-2.5 text-right"><Link href={`/patients/${p.id}`} className="text-xs font-medium text-accent hover:underline">{t("patients.viewDetails")}</Link></td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}
