"use client";

import React, { createContext, useContext, useState, useCallback, useRef, useEffect } from "react";
import { clsx } from "clsx";

/* ─── Types ─── */
type ModalType = "info" | "success" | "warning" | "error" | "confirm";

interface ModalData {
  type: ModalType;
  title?: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  onConfirm?: () => void;
  onCancel?: () => void;
}

interface ModalContextValue {
  showModal: (opts: ModalData) => void;
  showConfirm: (opts: {
    title?: string;
    message: string;
    confirmText?: string;
    cancelText?: string;
  }) => Promise<boolean>;
  showAlert: (opts: {
    type?: "info" | "success" | "warning" | "error";
    title?: string;
    message: string;
  }) => Promise<void>;
}

const ModalContext = createContext<ModalContextValue | null>(null);
export const useModal = () => {
  const ctx = useContext(ModalContext);
  if (!ctx) throw new Error("useModal must be used inside ModalProvider");
  return ctx;
};

/* ─── Icons ─── */
const modalIcons: Record<ModalType, React.ReactNode> = {
  info: (
    <div className="w-12 h-12 rounded-2xl bg-sky-100 dark:bg-sky-900/40 flex items-center justify-center">
      <svg className="w-6 h-6 text-sky-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
      </svg>
    </div>
  ),
  success: (
    <div className="w-12 h-12 rounded-2xl bg-emerald-100 dark:bg-emerald-900/40 flex items-center justify-center">
      <svg className="w-6 h-6 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    </div>
  ),
  warning: (
    <div className="w-12 h-12 rounded-2xl bg-amber-100 dark:bg-amber-900/40 flex items-center justify-center">
      <svg className="w-6 h-6 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
      </svg>
    </div>
  ),
  error: (
    <div className="w-12 h-12 rounded-2xl bg-red-100 dark:bg-red-900/40 flex items-center justify-center">
      <svg className="w-6 h-6 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
      </svg>
    </div>
  ),
  confirm: (
    <div className="w-12 h-12 rounded-2xl bg-violet-100 dark:bg-violet-900/40 flex items-center justify-center">
      <svg className="w-6 h-6 text-violet-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9.879 7.519c1.171-1.025 3.071-1.025 4.242 0 1.172 1.025 1.172 2.687 0 3.712-.203.179-.43.326-.67.442-.745.361-1.45.999-1.45 1.827v.75M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9 5.25h.008v.008H12v-.008z" />
      </svg>
    </div>
  ),
};

/* ─── Provider ─── */
export function ModalProvider({ children }: { children: React.ReactNode }) {
  const [modal, setModal] = useState<ModalData | null>(null);
  const [visible, setVisible] = useState(false);
  const resolveRef = useRef<((value: boolean) => void) | null>(null);

  useEffect(() => {
    if (modal) {
      requestAnimationFrame(() => setVisible(true));
    }
  }, [modal]);

  const close = useCallback((result: boolean) => {
    setVisible(false);
    setTimeout(() => {
      setModal(null);
      if (resolveRef.current) {
        resolveRef.current(result);
        resolveRef.current = null;
      }
    }, 300);
  }, []);

  const showModal = useCallback((opts: ModalData) => {
    setModal(opts);
  }, []);

  const showConfirm = useCallback(
    (opts: { title?: string; message: string; confirmText?: string; cancelText?: string }): Promise<boolean> => {
      return new Promise((resolve) => {
        resolveRef.current = resolve;
        setModal({
          type: "confirm",
          title: opts.title || "تأكيد",
          message: opts.message,
          confirmText: opts.confirmText || "تأكيد",
          cancelText: opts.cancelText || "إلغاء",
        });
      });
    },
    []
  );

  const showAlert = useCallback(
    (opts: { type?: "info" | "success" | "warning" | "error"; title?: string; message: string }): Promise<void> => {
      return new Promise((resolve) => {
        resolveRef.current = () => resolve();
        setModal({
          type: opts.type || "info",
          title: opts.title,
          message: opts.message,
          confirmText: "حسنًا",
        });
      });
    },
    []
  );

  // Handle Escape key
  useEffect(() => {
    if (!modal) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        if (modal.type === "confirm") {
          close(false);
        } else {
          close(true);
        }
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [modal, close]);

  return (
    <ModalContext.Provider value={{ showModal, showConfirm, showAlert }}>
      {children}

      {/* Modal Overlay */}
      {modal && (
        <div
          className={clsx(
            "fixed inset-0 z-[10000] flex items-center justify-center p-4 transition-all duration-300",
            visible ? "opacity-100" : "opacity-0"
          )}
        >
          {/* Backdrop */}
          <div
            className={clsx(
              "absolute inset-0 bg-slate-900/60 backdrop-blur-sm transition-opacity duration-300",
              visible ? "opacity-100" : "opacity-0"
            )}
            onClick={() => close(modal.type === "confirm" ? false : true)}
          />

          {/* Modal Card */}
          <div
            className={clsx(
              "relative w-full max-w-md overflow-hidden rounded-2xl border border-white/20 bg-white dark:bg-slate-900 shadow-2xl shadow-black/20 transition-all duration-300",
              visible
                ? "translate-y-0 scale-100 opacity-100"
                : "translate-y-4 scale-95 opacity-0"
            )}
            dir="auto"
          >
            {/* Top accent bar */}
            <div
              className={clsx(
                "h-1 w-full",
                modal.type === "success" && "bg-gradient-to-r from-emerald-400 to-teal-500",
                modal.type === "error" && "bg-gradient-to-r from-red-400 to-rose-500",
                modal.type === "warning" && "bg-gradient-to-r from-amber-400 to-orange-500",
                modal.type === "info" && "bg-gradient-to-r from-sky-400 to-blue-500",
                modal.type === "confirm" && "bg-gradient-to-r from-violet-400 to-purple-500"
              )}
            />

            {/* Content */}
            <div className="p-6">
              {/* Icon + Title */}
              <div className="flex items-start gap-4 mb-4">
                {modalIcons[modal.type]}
                <div className="flex-1 min-w-0 pt-1">
                  {modal.title && (
                    <h3 className="text-lg font-bold text-slate-800 dark:text-slate-100 mb-1">
                      {modal.title}
                    </h3>
                  )}
                  <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed whitespace-pre-wrap break-words max-h-[50vh] overflow-y-auto">
                    {modal.message}
                  </p>
                </div>
              </div>

              {/* Buttons */}
              <div className="flex items-center justify-end gap-3 mt-6">
                {modal.type === "confirm" && (
                  <button
                    onClick={() => close(false)}
                    className="px-5 py-2.5 rounded-xl text-sm font-medium text-slate-600 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700 transition-all duration-200 active:scale-[0.97]"
                  >
                    {modal.cancelText || "إلغاء"}
                  </button>
                )}
                <button
                  onClick={() => {
                    if (modal.type === "confirm") {
                      modal.onConfirm?.();
                      close(true);
                    } else {
                      close(true);
                    }
                  }}
                  className={clsx(
                    "px-5 py-2.5 rounded-xl text-sm font-medium text-white transition-all duration-200 active:scale-[0.97] shadow-lg",
                    modal.type === "success" && "bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 shadow-emerald-500/25",
                    modal.type === "error" && "bg-gradient-to-r from-red-500 to-rose-600 hover:from-red-600 hover:to-rose-700 shadow-red-500/25",
                    modal.type === "warning" && "bg-gradient-to-r from-amber-500 to-orange-600 hover:from-amber-600 hover:to-orange-700 shadow-amber-500/25",
                    modal.type === "info" && "bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-600 hover:to-blue-700 shadow-sky-500/25",
                    modal.type === "confirm" && "bg-gradient-to-r from-violet-500 to-purple-600 hover:from-violet-600 hover:to-purple-700 shadow-violet-500/25"
                  )}
                  autoFocus
                >
                  {modal.confirmText || "حسنًا"}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </ModalContext.Provider>
  );
}
