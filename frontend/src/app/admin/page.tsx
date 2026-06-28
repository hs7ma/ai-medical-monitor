"use client";

import { useState, useEffect, useCallback } from "react";
import { useI18n } from "@/i18n/context";
import { api } from "@/lib/api";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input, Label, Select } from "@/components/ui/Input";
import { clsx } from "clsx";
import { useToast } from "@/components/ui/Toast";

export default function AdminPage() {
  const { t } = useI18n();
  const { showToast } = useToast();
  const [users, setUsers] = useState<any[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [newUser, setNewUser] = useState({ username: "", password: "", role: "nurse", full_name: "" });

  const load = useCallback(async () => { try { setUsers(await api.listUsers()); } catch {} }, []);
  useEffect(() => { load(); }, [load]);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try { await api.createUser(newUser); setNewUser({ username: "", password: "", role: "nurse", full_name: "" }); setShowForm(false); load(); } catch (err: any) { showToast({ type: "error", message: err.message }); }
  };

  const roleColor: Record<string, string> = { admin: "bg-purple-50 text-purple-600", doctor: "bg-accent-light text-accent", nurse: "bg-success-light text-success" };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-heading-md text-text">{t("nav.admin")}</h1>
          <p className="mt-0.5 text-xs text-text-muted">{users.length} users</p>
        </div>
        <Button onClick={() => setShowForm(!showForm)}>{showForm ? "Cancel" : "+ Add User"}</Button>
      </div>

      {showForm && (
        <Card className="animate-fade-in">
          <form onSubmit={handleCreate} className="grid grid-cols-1 gap-3 p-4 sm:grid-cols-2">
            <div><Label required>Username</Label><Input value={newUser.username} onChange={(e) => setNewUser({ ...newUser, username: e.target.value })} required /></div>
            <div><Label required>Password</Label><Input type="password" value={newUser.password} onChange={(e) => setNewUser({ ...newUser, password: e.target.value })} required /></div>
            <div><Label required>Full Name</Label><Input value={newUser.full_name} onChange={(e) => setNewUser({ ...newUser, full_name: e.target.value })} required /></div>
            <div><Label required>Role</Label><Select value={newUser.role} onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}><option value="nurse">Nurse</option><option value="doctor">Doctor</option><option value="admin">Admin</option></Select></div>
            <div className="sm:col-span-2 flex justify-end gap-2"><Button type="button" variant="ghost" onClick={() => setShowForm(false)}>Cancel</Button><Button type="submit">Create</Button></div>
          </form>
        </Card>
      )}

      <Card>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-left text-label uppercase text-text-secondary">
              <th className="px-4 py-2.5">User</th>
              <th className="px-4 py-2.5">Username</th>
              <th className="px-4 py-2.5">Role</th>
              <th className="px-4 py-2.5">Status</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id} className="border-b border-border last:border-0 hover:bg-surface/50 transition">
                <td className="px-4 py-2.5">
                  <div className="flex items-center gap-2">
                    <div className="flex h-6 w-6 items-center justify-center rounded bg-accent-light text-[10px] font-semibold text-accent">{u.full_name?.charAt(0)}</div>
                    <span className="font-medium text-text">{u.full_name}</span>
                  </div>
                </td>
                <td className="px-4 py-2.5 text-text-muted">@{u.username}</td>
                <td className="px-4 py-2.5"><span className={clsx("inline-block rounded px-1.5 py-0.5 text-[11px] font-medium capitalize", roleColor[u.role] || roleColor.nurse)}>{u.role}</span></td>
                <td className="px-4 py-2.5"><span className={clsx("flex items-center gap-1 text-[11px]", u.is_active ? "text-success" : "text-danger")}><span className={clsx("h-1 w-1 rounded-full", u.is_active ? "bg-success" : "bg-danger")} />{u.is_active ? "Active" : "Disabled"}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}
