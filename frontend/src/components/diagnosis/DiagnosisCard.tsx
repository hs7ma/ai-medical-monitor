"use client";

import { useI18n } from "@/i18n/context";
import { clsx } from "clsx";

interface DiagnosisResult {
  primary_diagnosis: string;
  differential_diagnoses?: string[];
  severity: string;
  confidence: string;
  findings?: string[];
  possible_causes?: string[];
  recommendations?: string[];
  additional_tests?: string[];
  red_flags?: string[];
  follow_up_questions?: string[];
}

const severityMap: Record<
  string,
  { color: string; bg: string; border: string; labelBg: string }
> = {
  low: {
    color: "text-emerald-700",
    bg: "bg-emerald-50",
    border: "border-emerald-200/60",
    labelBg: "bg-emerald-500",
  },
  moderate: {
    color: "text-amber-700",
    bg: "bg-amber-50",
    border: "border-amber-200/60",
    labelBg: "bg-amber-500",
  },
  high: {
    color: "text-orange-700",
    bg: "bg-orange-50",
    border: "border-orange-200/60",
    labelBg: "bg-orange-500",
  },
  critical: {
    color: "text-rose-700",
    bg: "bg-rose-50",
    border: "border-rose-200/60",
    labelBg: "bg-rose-500",
  },
};

const confidenceMap: Record<string, string> = {
  low: "bg-slate-100 text-slate-700 border-slate-200/60",
  medium: "bg-blue-50 text-blue-700 border-blue-200/60",
  high: "bg-indigo-50 text-indigo-700 border-indigo-200/60",
};

export function DiagnosisCard({ result }: { result: DiagnosisResult }) {
  const { t } = useI18n();
  const sev = severityMap[result.severity] || severityMap.moderate;
  const confClass = confidenceMap[result.confidence] || confidenceMap.medium;

  const List = ({ items, markerColor }: { items?: string[]; markerColor?: string }) => {
    if (!items || items.length === 0) return null;
    return (
      <ul className="mt-2 space-y-1.5 pl-1">
        {items.map((item, i) => (
          <li key={i} className="flex items-start gap-2.5 text-xs text-text-secondary leading-relaxed">
            <span
              className={clsx(
                "mt-2 h-1.5 w-1.5 shrink-0 rounded-full",
                markerColor || "bg-slate-300"
              )}
            />
            <span>{item}</span>
          </li>
        ))}
      </ul>
    );
  };

  return (
    <div className="animate-slide-up rounded-2xl border border-slate-200 bg-white shadow-md shadow-slate-100/40 overflow-hidden w-full">
      {/* Header */}
      <div className="border-b border-slate-100 bg-slate-50/50 px-5 py-3.5 flex items-center justify-between">
        <h3 className="text-xs font-bold text-text flex items-center gap-2">
          <span className="text-base">📋</span> {t("diagnosis.diagnosisResult")}
        </h3>
        <div className="flex gap-2">
          <span
            className={clsx(
              "inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider",
              sev.bg,
              sev.color,
              sev.border
            )}
          >
            <span className={clsx("h-1.5 w-1.5 rounded-full animate-pulse", sev.labelBg)} />
            {t(`diagnosis.severityLevels.${result.severity}`)}
          </span>
          <span
            className={clsx(
              "inline-flex items-center rounded-lg border px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider",
              confClass
            )}
          >
            {t("diagnosis.confidence")}: {t(`diagnosis.confidenceLevels.${result.confidence}`)}
          </span>
        </div>
      </div>

      <div className="p-5 space-y-5">
        {/* Primary Diagnosis Callout */}
        <div className="bg-slate-50/70 border border-slate-100/80 rounded-xl p-4">
          <p className="text-[10px] font-bold uppercase tracking-wider text-text-muted">{t("diagnosis.primaryDiagnosis")}</p>
          <p className="mt-1 text-base font-bold text-text">{result.primary_diagnosis}</p>
        </div>

        {/* 2-Column Responsive Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
          {/* Column 1: Clinical Findings, Differential Diagnoses, Causes */}
          <div className="space-y-5">
            {result.differential_diagnoses && result.differential_diagnoses.length > 0 && (
              <Section title={t("diagnosis.differentialDiagnoses")} icon="🔍">
                <List items={result.differential_diagnoses} markerColor="bg-indigo-500/60" />
              </Section>
            )}

            {result.findings && result.findings.length > 0 && (
              <Section title={t("diagnosis.findings")} icon="⚡">
                <List items={result.findings} markerColor="bg-accent/60" />
              </Section>
            )}

            {result.possible_causes && result.possible_causes.length > 0 && (
              <Section title={t("diagnosis.possibleCauses")} icon="🧠">
                <List items={result.possible_causes} />
              </Section>
            )}
          </div>

          {/* Column 2: Red Flags, Recommendations, Tests */}
          <div className="space-y-5 border-t md:border-t-0 md:border-l border-slate-100 md:pl-6 pt-5 md:pt-0">
            {result.red_flags && result.red_flags.length > 0 && (
              <div className="rounded-xl border border-rose-200 bg-rose-50/50 p-4">
                <p className="text-[10px] font-bold uppercase tracking-wider text-rose-700 flex items-center gap-1.5 font-bold">
                  <span>🚨</span> {t("diagnosis.redFlags")}
                </p>
                <ul className="mt-2.5 space-y-1.5 pl-1">
                  {result.red_flags.map((item, i) => (
                    <li key={i} className="flex items-start gap-2.5 text-xs text-rose-950 font-medium leading-relaxed">
                      <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-rose-500 animate-pulse" />
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {result.recommendations && result.recommendations.length > 0 && (
              <Section title={t("diagnosis.recommendations")} icon="✅">
                <List items={result.recommendations} markerColor="bg-emerald-500/60" />
              </Section>
            )}

            {result.additional_tests && result.additional_tests.length > 0 && (
              <Section title={t("diagnosis.additionalTests")} icon="🧪">
                <List items={result.additional_tests} markerColor="bg-amber-500/60" />
              </Section>
            )}
          </div>
        </div>

        {/* Disclaimer */}
        <div className="pt-4 flex items-start gap-2.5 rounded-xl bg-slate-50 border border-slate-100 px-4 py-3">
          <span className="text-sm text-text-muted mt-0.5">⚠️</span>
          <p className="text-[11px] font-medium text-text-muted leading-relaxed">{t("diagnosis.disclaimer")}</p>
        </div>
      </div>
    </div>
  );
}

function Section({
  title,
  icon,
  children,
}: {
  title: string;
  icon?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="pt-2">
      <p className="text-[10px] font-bold uppercase tracking-wider text-text-muted flex items-center gap-1.5">
        {icon && <span>{icon}</span>} {title}
      </p>
      {children}
    </div>
  );
}
