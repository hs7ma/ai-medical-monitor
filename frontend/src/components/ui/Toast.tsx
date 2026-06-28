"use client";

import React, { createContext, useContext, useState, useCallback, useRef, useEffect } from "react";
import { clsx } from "clsx";

/* ─── Types ─── */
type ToastType = "success" | "error" | "warning" | "info";

interface ToastItem {
  id: number;
  type: ToastType;
  title?: string;
  message: string;
  duration?: number;
  progress: number;
  exiting?: boolean;
}

interface ToastContextValue {
  showToast: (opts: { type?: ToastType; title?: string; message: string; duration?: number }) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);
export const useToast = () => {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used inside ToastProvider");
  return ctx;
};

/* ─── Icons ─── */
const icons: Record<ToastType, React.ReactNode> = {
  success: (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  error: (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
    </svg>
  ),
  warning: (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
    </svg>
  ),
  info: (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
    </svg>
  ),
};

/* ─── Color scheme ─── */
const colorMap: Record<ToastType, { bg: string; border: string; icon: string; bar: string }> = {
  success: {
    bg: "bg-emerald-50/95 dark:bg-emerald-950/90",
    border: "border-emerald-200/60 dark:border-emerald-800/60",
    icon: "text-emerald-600 dark:text-emerald-400",
    bar: "bg-emerald-500",
  },
  error: {
    bg: "bg-red-50/95 dark:bg-red-950/90",
    border: "border-red-200/60 dark:border-red-800/60",
    icon: "text-red-600 dark:text-red-400",
    bar: "bg-red-500",
  },
  warning: {
    bg: "bg-amber-50/95 dark:bg-amber-950/90",
    border: "border-amber-200/60 dark:border-amber-800/60",
    icon: "text-amber-600 dark:text-amber-400",
    bar: "bg-amber-500",
  },
  info: {
    bg: "bg-sky-50/95 dark:bg-sky-950/90",
    border: "border-sky-200/60 dark:border-sky-800/60",
    icon: "text-sky-600 dark:text-sky-400",
    bar: "bg-sky-500",
  },
};

/* ─── Single Toast Component ─── */
function ToastCard({ toast, onDismiss }: { toast: ToastItem; onDismiss: (id: number) => void }) {
  const colors = colorMap[toast.type];

  return (
    <div
      className={clsx(
        "pointer-events-auto relative w-[380px] max-w-[calc(100vw-2rem)] overflow-hidden rounded-xl border shadow-2xl shadow-black/10 backdrop-blur-xl transition-all duration-500 ease-out",
        colors.bg,
        colors.border,
        toast.exiting
          ? "translate-x-[120%] opacity-0 scale-95"
          : "translate-x-0 opacity-100 scale-100 animate-toast-in"
      )}
      role="alert"
      dir="auto"
    >
      {/* Content */}
      <div className="flex items-start gap-3 px-4 py-3.5">
        {/* Icon */}
        <div className={clsx("mt-0.5 shrink-0", colors.icon)}>
          {icons[toast.type]}
        </div>

        {/* Text */}
        <div className="flex-1 min-w-0">
          {toast.title && (
            <p className="text-sm font-semibold text-slate-800 dark:text-slate-100 mb-0.5">
              {toast.title}
            </p>
          )}
          <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed whitespace-pre-wrap break-words">
            {toast.message}
          </p>
        </div>

        {/* Close */}
        <button
          onClick={() => onDismiss(toast.id)}
          className="shrink-0 mt-0.5 rounded-lg p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 hover:bg-black/5 dark:hover:bg-white/10 transition-colors"
          aria-label="Close"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Progress bar */}
      <div className="absolute bottom-0 left-0 right-0 h-[3px] bg-black/5 dark:bg-white/5">
        <div
          className={clsx("h-full transition-all duration-100 ease-linear rounded-full", colors.bar)}
          style={{ width: `${toast.progress}%` }}
        />
      </div>
    </div>
  );
}

/* ─── Provider ─── */
let idCounter = 0;

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const timersRef = useRef<Map<number, NodeJS.Timeout>>(new Map());
  const progressRef = useRef<Map<number, NodeJS.Timeout>>(new Map());

  const dismiss = useCallback((id: number) => {
    // First set exiting for animation
    setToasts((prev) => prev.map((t) => (t.id === id ? { ...t, exiting: true } : t)));
    // Clear timers
    const timer = timersRef.current.get(id);
    if (timer) { clearTimeout(timer); timersRef.current.delete(id); }
    const prog = progressRef.current.get(id);
    if (prog) { clearInterval(prog); progressRef.current.delete(id); }
    // Remove after animation
    setTimeout(() => setToasts((prev) => prev.filter((t) => t.id !== id)), 400);
  }, []);

  const showToast = useCallback(
    ({ type = "info", title, message, duration = 6000 }: { type?: ToastType; title?: string; message: string; duration?: number }) => {
      const id = ++idCounter;
      const newToast: ToastItem = { id, type, title, message, duration, progress: 100, exiting: false };
      setToasts((prev) => [...prev.slice(-4), newToast]); // max 5

      // Progress countdown
      const interval = 50;
      const step = (interval / duration) * 100;
      const progressTimer = setInterval(() => {
        setToasts((prev) =>
          prev.map((t) => {
            if (t.id !== id) return t;
            const next = t.progress - step;
            return { ...t, progress: Math.max(0, next) };
          })
        );
      }, interval);
      progressRef.current.set(id, progressTimer);

      // Auto dismiss
      const timer = setTimeout(() => dismiss(id), duration);
      timersRef.current.set(id, timer);
    },
    [dismiss]
  );

  // Clean up on unmount
  useEffect(() => {
    const timers = timersRef.current;
    const progress = progressRef.current;
    return () => {
      timers.forEach((t) => clearTimeout(t));
      progress.forEach((t) => clearInterval(t));
    };
  }, []);

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      {/* Toast container - top left for RTL */}
      <div className="fixed top-4 left-4 z-[9999] flex flex-col gap-3 pointer-events-none" dir="auto">
        {toasts.map((t) => (
          <ToastCard key={t.id} toast={t} onDismiss={dismiss} />
        ))}
      </div>
    </ToastContext.Provider>
  );
}
