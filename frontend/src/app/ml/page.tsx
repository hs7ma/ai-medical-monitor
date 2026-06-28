"use client";

import { useState } from "react";
import { useI18n } from "@/i18n/context";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Input, Label, Select } from "@/components/ui/Input";
import { Card } from "@/components/ui/Card";

const defaults = {
  age: 50,
  sex: 1,
  cp: 0,
  trestbps: 120,
  chol: 200,
  fbs: 0,
  restecg: 0,
  thalach: 150,
  exang: 0,
  oldpeak: 0,
  slope: 1,
  ca: 0,
  thal: 0,
};

export default function MLPredictionPage() {
  const { t, locale } = useI18n();
  const [features, setFeatures] = useState<any>(defaults);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const update = (key: string, value: string) => {
    setFeatures((prev: any) => ({
      ...prev,
      [key]: value === "" ? 0 : parseFloat(value),
    }));
  };

  const handlePredict = async () => {
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const res = await api.predictHeart(features);
      if (res.available === false) {
        setError(res.detail || "Model not available");
      } else if (res.can_predict === false) {
        setError(locale === "ar" ? res.message_ar : res.message_en);
      } else {
        setResult(res);
      }
    } catch (err: any) {
      setError(err?.message || "Prediction failed");
    } finally {
      setLoading(false);
    }
  };

  const riskColors: Record<string, { ring: string; text: string; bg: string; border: string }> = {
    high: {
      ring: "#ef4444",
      text: "text-rose-700",
      bg: "bg-rose-50/50",
      border: "border-rose-200/60",
    },
    moderate: {
      ring: "#f59e0b",
      text: "text-amber-700",
      bg: "bg-amber-50/50",
      border: "border-amber-200/60",
    },
    low: {
      ring: "#3b82f6",
      text: "text-blue-700",
      bg: "bg-blue-50/50",
      border: "border-blue-200/60",
    },
    normal: {
      ring: "#10b981",
      text: "text-emerald-700",
      bg: "bg-emerald-50/50",
      border: "border-emerald-200/60",
    },
  };

  const riskLabels: Record<string, string> = {
    high: "High Risk",
    moderate: "Moderate Risk",
    low: "Low Risk",
    normal: "Normal",
  };

  const fields: {
    key: string;
    label: string;
    type?: string;
    options?: { value: string; label: string }[];
  }[] = [
    { key: "age", label: "العمر / Age", type: "number" },
    {
      key: "sex",
      label: "الجنس / Sex",
      options: [
        { value: "1", label: "ذكر / Male" },
        { value: "0", label: "أنثى / Female" },
      ],
    },
    {
      key: "cp",
      label: "نوع ألم الصدر / Chest Pain Type",
      options: [
        { value: "0", label: "Typical Angina" },
        { value: "1", label: "Atypical Angina" },
        { value: "2", label: "Non-anginal" },
        { value: "3", label: "Asymptomatic" },
      ],
    },
    { key: "trestbps", label: "ضغط الدم الانقباضي (Resting BP)", type: "number" },
    { key: "chol", label: "الكوليسترول (Cholesterol)", type: "number" },
    {
      key: "fbs",
      label: "سكر الدم الصائم > 120 (Fasting BS)",
      options: [
        { value: "0", label: "لا / No" },
        { value: "1", label: "نعم / Yes" },
      ],
    },
    {
      key: "restecg",
      label: "تخطيط القلب أثناء الراحة (Resting ECG)",
      options: [
        { value: "0", label: "طبيعي / Normal" },
        { value: "1", label: "ST abnormality" },
        { value: "2", label: "LVH" },
      ],
    },
    { key: "thalach", label: "أقصى معدل ضربات قلب (Max HR)", type: "number" },
    {
      key: "exang",
      label: "ألم صدر ناتج عن المجهود (Exercise Angina)",
      options: [
        { value: "0", label: "لا / No" },
        { value: "1", label: "نعم / Yes" },
      ],
    },
    { key: "oldpeak", label: "انخفاض ST (Oldpeak)", type: "number" },
    {
      key: "slope",
      label: "ميل قطاع ST Slope",
      options: [
        { value: "0", label: "Downsloping" },
        { value: "1", label: "Flat" },
        { value: "2", label: "Upsloping" },
      ],
    },
    { key: "ca", label: "الأوعية الدموية الرئيسية (Vessels 0-4)", type: "number" },
    {
      key: "thal",
      label: "الثلاسيميا (Thalassemia)",
      options: [
        { value: "0", label: "طبيعي / Normal" },
        { value: "1", label: "Fixed defect" },
        { value: "2", label: "Reversible defect" },
        { value: "3", label: "Reversible" },
      ],
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-gradient-to-r from-slate-900 to-indigo-950 p-6 rounded-2xl text-white shadow-md shadow-slate-100/10">
        <div>
          <h1 className="text-xl font-bold tracking-tight font-outfit">التنبؤ بأمراض القلب عبر التعلم الآلي</h1>
          <p className="mt-1.5 text-xs text-slate-300">
            نموذج HistGradientBoosting + معايرة - دقة 85.5% (AUC 0.93)، مدرب على 2,138 سجل طبي
          </p>
        </div>
        <div className="flex items-center gap-2 rounded-xl bg-white/10 px-3 py-1.5 backdrop-blur-md border border-white/5 self-start md:self-auto">
          <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-200">النموذج جاهز للعمل</span>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Features Input Panel */}
        <Card className="rounded-2xl border-slate-200 bg-white/70 backdrop-blur-md shadow-sm">
          <div className="p-6">
            <h2 className="mb-4 text-xs font-bold uppercase tracking-wider text-text-secondary flex items-center gap-1.5">
              <span>🧬</span> البيانات والمؤشرات الحيوية للمريض
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {fields.map((f) => (
                <div key={f.key} className="space-y-1">
                  <Label className="text-[11px] font-bold text-text-secondary">{f.label}</Label>
                  {f.options ? (
                    <Select
                      value={String(features[f.key])}
                      onChange={(e) => update(f.key, e.target.value)}
                      className="rounded-xl border-slate-200/80 bg-white"
                    >
                      {f.options.map((o) => (
                        <option key={o.value} value={o.value}>
                          {o.label}
                        </option>
                      ))}
                    </Select>
                  ) : (
                    <Input
                      type={f.type || "text"}
                      value={features[f.key]}
                      onChange={(e) => update(f.key, e.target.value)}
                      className="rounded-xl border-slate-200/80 bg-white"
                    />
                  )}
                </div>
              ))}
            </div>
            <div className="mt-6 flex gap-2.5">
              <button
                onClick={handlePredict}
                disabled={loading}
                className="flex-1 rounded-xl bg-gradient-to-r from-accent to-cyan-500 py-3 text-sm font-semibold text-white shadow-md shadow-accent/15 transition-all hover:from-accent-hover hover:to-cyan-600 active:scale-[0.98] disabled:opacity-50 disabled:pointer-events-none"
              >
                {loading ? "جاري التنبؤ..." : "بدء التنبؤ والتحليل"}
              </button>
              <button
                onClick={() => {
                  setFeatures(defaults);
                  setResult(null);
                  setError("");
                }}
                className="rounded-xl border border-slate-200 bg-slate-50 px-5 py-3 text-sm font-semibold text-text-secondary transition hover:bg-slate-100 hover:text-text active:scale-[0.98]"
              >
                إعادة ضبط
              </button>
            </div>
            {error && (
              <div className="mt-4 rounded-xl bg-danger/10 border border-danger/20 px-4 py-3 text-xs text-danger flex items-center gap-2">
                <span>⚠️</span>
                <p className="font-semibold">{error}</p>
              </div>
            )}
          </div>
        </Card>

        {/* Prediction Results Panel */}
        {result ? (
          <Card className="rounded-2xl border-slate-200 bg-white shadow-sm overflow-hidden animate-slide-up">
            <div className="border-b border-slate-100 bg-slate-50/50 px-6 py-4 flex items-center justify-between">
              <h2 className="text-xs font-bold uppercase tracking-wider text-text flex items-center gap-1.5">
                <span>📊</span> نتيجة التنبؤ السريري للنموذج
              </h2>
            </div>
            <div className="p-6 space-y-6">
              {/* Radial Gauge and Severity */}
              <div className="flex flex-col sm:flex-row items-center justify-around gap-6">
                <RadialProgress
                  value={result.risk_score * 100}
                  color={riskColors[result.risk_level]?.ring || "#94a3b8"}
                />

                <div className="text-center sm:text-right space-y-1">
                  <p className="text-[10px] font-bold uppercase tracking-wider text-text-muted">{locale === "ar" ? "الاستنتاج" : "Conclusion"}</p>
                  <p className="text-base font-bold text-text">{locale === "ar" ? (result.prediction_label || result.prediction_label_en) : (result.prediction_label_en || result.prediction_label)}</p>
                  <div className="mt-2.5">
                    <span
                      className={`inline-flex items-center gap-1.5 rounded-lg border px-3 py-1 text-xs font-bold uppercase tracking-wider ${
                        riskColors[result.risk_level]?.bg
                      } ${riskColors[result.risk_level]?.text} ${
                        riskColors[result.risk_level]?.border
                      }`}
                    >
                      {locale === "ar" ? "مستوى الخطر: " : "Risk Level: "}{locale === "ar" ? (result.risk_level_ar || result.risk_level) : (result.risk_level || result.risk_level_ar)}
                    </span>
                  </div>
                </div>
              </div>

              {/* Top Contributing Features */}
              <div className="space-y-3 pt-4 border-t border-slate-100">
                <p className="text-[10px] font-bold uppercase tracking-wider text-text-muted">
                  {locale === "ar" ? "أهم العوامل الحيوية المساهمة في الاحتمالية" : "Top Contributing Factors"}
                </p>
                <div className="space-y-3">
                  {result.top_features?.map((tf: any, i: number) => {
                    const pct = tf.importance * 100;
                    return (
                      <div key={i} className="space-y-1">
                        <div className="flex items-center justify-between text-xs">
                          <span className="font-semibold text-text-secondary">{locale === "ar" ? (tf.feature || tf.feature_en) : (tf.feature_en || tf.feature)}</span>
                          <span className="font-bold text-accent">{pct.toFixed(1)}%</span>
                        </div>
                        <div className="h-2 w-full rounded-full bg-slate-100 overflow-hidden">
                          <div
                            className="h-full rounded-full bg-accent transition-all duration-500"
                            style={{ width: `${pct}%` }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Model Specifications */}
              <div className="rounded-xl bg-slate-50 border border-slate-100 px-4 py-3 text-[11px] text-text-muted flex flex-wrap gap-x-4 gap-y-1 justify-between items-center">
                <span>{locale === "ar" ? "النموذج: " : "Model: "}{result.model_name}</span>
                <span>{locale === "ar" ? "حجم التدريب: " : "Training size: "}{result.training_size?.toLocaleString()} {locale === "ar" ? "سجل" : "records"}</span>
                <span className="font-semibold text-text-secondary">{locale === "ar" ? "الدقة: " : "Accuracy: "}{(result.model_accuracy * 100).toFixed(1)}% | AUC: {(result.model_auc * 100).toFixed(1)}%</span>
              </div>
            </div>
          </Card>
        ) : (
          <div className="rounded-2xl border border-dashed border-slate-200 flex flex-col items-center justify-center p-8 text-center bg-slate-50/30">
            <div className="flex h-14 w-14 items-center justify-center rounded-full bg-slate-100 text-slate-400 mb-3 text-xl">
              ⚙️
            </div>
            <p className="text-sm font-semibold text-text-secondary">انتظار البيانات</p>
            <p className="mt-1 text-xs text-text-muted max-w-xs">
              أدخل قيم العوامل الحيوية للمريض في النموذج الأيسر واضغط على زر التنبؤ لعرض التحليل البياني هنا.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

function RadialProgress({ value, color }: { value: number; color: string }) {
  const radius = 60;
  const stroke = 8;
  const normalizedRadius = radius - stroke * 2;
  const circumference = normalizedRadius * 2 * Math.PI;
  const strokeDashoffset = circumference - (value / 100) * circumference;

  return (
    <div className="relative flex items-center justify-center">
      <svg height={radius * 2} width={radius * 2} className="transform -rotate-90">
        <circle
          stroke="#f1f5f9"
          fill="transparent"
          strokeWidth={stroke}
          r={normalizedRadius}
          cx={radius}
          cy={radius}
        />
        <circle
          stroke={color}
          fill="transparent"
          strokeWidth={stroke}
          strokeDasharray={circumference + " " + circumference}
          style={{ strokeDashoffset }}
          strokeLinecap="round"
          r={normalizedRadius}
          cx={radius}
          cy={radius}
          className="transition-all duration-500 ease-out"
        />
      </svg>
      <div className="absolute flex flex-col items-center">
        <span className="text-xl font-bold text-text font-outfit">{value.toFixed(1)}%</span>
        <span className="text-[9px] text-text-muted font-bold uppercase tracking-wider mt-0.5">نسبة الخطر</span>
      </div>
    </div>
  );
}
