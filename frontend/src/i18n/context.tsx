"use client";

import React, { createContext, useContext, useState, useCallback, useEffect } from "react";
import en from "@/i18n/en/common.json";
import ar from "@/i18n/ar/common.json";

type Locale = "ar" | "en";
type Dict = typeof en;

const dictionaries: Record<Locale, Dict> = { en, ar };

interface I18nContextValue {
  locale: Locale;
  dir: "rtl" | "ltr";
  t: (path: string) => string;
  setLocale: (l: Locale) => void;
  toggleLocale: () => void;
}

const I18nContext = createContext<I18nContextValue | null>(null);

export function I18nProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>("ar");

  useEffect(() => {
    const saved = typeof window !== "undefined" ? localStorage.getItem("locale") : null;
    if (saved === "ar" || saved === "en") {
      setLocaleState(saved);
    }
  }, []);

  useEffect(() => {
    if (typeof document !== "undefined") {
      document.documentElement.lang = locale;
      document.documentElement.dir = locale === "ar" ? "rtl" : "ltr";
    }
  }, [locale]);

  const setLocale = useCallback((l: Locale) => {
    setLocaleState(l);
    if (typeof window !== "undefined") localStorage.setItem("locale", l);
  }, []);

  const toggleLocale = useCallback(() => {
    setLocale(locale === "ar" ? "en" : "ar");
  }, [locale, setLocale]);

  const t = useCallback(
    (path: string): string => {
      const keys = path.split(".");
      let val: unknown = dictionaries[locale];
      for (const k of keys) {
        if (val && typeof val === "object" && k in (val as Record<string, unknown>)) {
          val = (val as Record<string, unknown>)[k];
        } else {
          return path;
        }
      }
      return typeof val === "string" ? val : path;
    },
    [locale]
  );

  return (
    <I18nContext.Provider
      value={{ locale, dir: locale === "ar" ? "rtl" : "ltr", t, setLocale, toggleLocale }}
    >
      {children}
    </I18nContext.Provider>
  );
}

export function useI18n() {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useI18n must be used within I18nProvider");
  return ctx;
}
