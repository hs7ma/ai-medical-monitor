"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useI18n } from "@/i18n/context";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Input, Label } from "@/components/ui/Input";

export default function LoginPage() {
  const { t, locale, toggleLocale } = useI18n();
  const router = useRouter();
  const { setAuth, loadFromStorage } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadFromStorage();
    if (useAuth.getState().token) {
      router.push("/diagnosis");
    }
  }, [router, loadFromStorage]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const res = await api.login(username, password);
      setAuth(res.access_token, { username, role: res.role, full_name: res.full_name });
      router.push("/diagnosis");
    } catch (err: any) {
      setError(err?.message || t("login.error"));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="gradient-mesh flex min-h-screen items-center justify-center px-4 py-12 relative overflow-hidden">
      {/* Background Decorative Blur Orbs */}
      <div className="absolute top-1/4 left-1/4 h-96 w-96 rounded-full bg-accent/10 blur-3xl" />
      <div className="absolute bottom-1/4 right-1/4 h-96 w-96 rounded-full bg-brand-indigo/10 blur-3xl" />

      <div className="w-full max-w-md z-10">
        {/* Language switcher */}
        <div className="absolute top-4 right-4 z-20">
          <button
            onClick={toggleLocale}
            className="flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-semibold text-slate-300 backdrop-blur-md transition hover:bg-white/10 active:scale-95"
          >
            🌐 {locale === "ar" ? "English" : "العربية"}
          </button>
        </div>

        {/* Brand header */}
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-tr from-accent to-cyan-500 shadow-lg shadow-accent/20 animate-pulse">
            <svg className="h-7 w-7 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white font-outfit">{t("app.title")}</h1>
          <p className="mt-2 text-sm text-slate-400">{t("login.welcome")}</p>
        </div>

        {/* Card */}
        <div className="glass-card p-8 border border-white/10 bg-white/5 backdrop-blur-xl shadow-2xl relative">
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <Label htmlFor="username" className="text-slate-300 font-semibold text-[11px] uppercase tracking-wider">{t("login.username")}</Label>
              <div className="relative mt-1">
                <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-400">👤</span>
                <input
                  id="username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="admin"
                  required
                  className="w-full rounded-xl border border-white/10 bg-white/5 pl-9 pr-4 py-3 text-sm text-white placeholder-slate-500 transition-all duration-200 focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/25"
                />
              </div>
            </div>
            <div>
              <Label htmlFor="password" className="text-slate-300 font-semibold text-[11px] uppercase tracking-wider">{t("login.password")}</Label>
              <div className="relative mt-1">
                <span className="absolute inset-y-0 left-0 flex items-center pl-3 text-slate-400">🔑</span>
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••"
                  required
                  className="w-full rounded-xl border border-white/10 bg-white/5 pl-9 pr-4 py-3 text-sm text-white placeholder-slate-500 transition-all duration-200 focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/25"
                />
              </div>
            </div>

            {error && (
              <div className="rounded-xl bg-danger/10 border border-danger/20 px-4 py-3 text-xs text-danger flex items-center gap-2">
                <span>⚠️</span>
                <p className="font-medium">{error}</p>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full rounded-xl bg-gradient-to-r from-accent to-cyan-500 py-3 text-sm font-semibold text-white shadow-lg shadow-accent/25 transition-all duration-300 hover:from-accent-hover hover:to-cyan-600 hover:shadow-xl hover:shadow-accent/35 active:scale-[0.98] disabled:pointer-events-none disabled:opacity-50"
            >
              {loading ? (
                <div className="flex items-center justify-center gap-2">
                  <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  <span>...</span>
                </div>
              ) : (
                t("login.submit")
              )}
            </button>
          </form>
        </div>

        {/* Credentials hints */}
        <div className="mt-8 text-center">
          <p className="text-xs text-slate-500 font-semibold uppercase tracking-wider mb-2">الدخول التجريبي / Demo Accounts</p>
          <div className="flex flex-wrap justify-center gap-2">
            <span className="rounded-lg bg-slate-900/50 border border-white/5 px-2.5 py-1 text-xs text-slate-400 font-medium">admin : admin123</span>
            <span className="rounded-lg bg-slate-900/50 border border-white/5 px-2.5 py-1 text-xs text-slate-400 font-medium">doctor : doctor123</span>
            <span className="rounded-lg bg-slate-900/50 border border-white/5 px-2.5 py-1 text-xs text-slate-400 font-medium">nurse : nurse123</span>
          </div>
        </div>
      </div>
    </div>
  );
}
