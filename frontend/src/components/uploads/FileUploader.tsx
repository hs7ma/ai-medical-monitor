"use client";

import React, { useRef, useState } from "react";
import { clsx } from "clsx";
import { useI18n } from "@/i18n/context";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Select } from "@/components/ui/Input";

interface FileUploaderProps {
  patientId: number;
  onUploaded: () => void;
  compact?: boolean;
}

export function FileUploader({ patientId, onUploaded, compact = false }: FileUploaderProps) {
  const { t } = useI18n();
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [category, setCategory] = useState("lab");
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files?.[0];
    if (f) setFile(f);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) setFile(f);
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError("");
    try {
      await api.uploadFile(patientId, file, category);
      setFile(null);
      onUploaded();
    } catch (e: any) {
      setError(e.message);
    } finally {
      setUploading(false);
    }
  };

  const categories = [
    { value: "lab", label: t("uploads.lab") },
    { value: "imaging", label: t("uploads.imaging") },
    { value: "report", label: t("uploads.report") },
    { value: "other", label: t("uploads.other") },
  ];

  return (
    <div className="space-y-2.5">
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={clsx(
          "cursor-pointer rounded-lg border border-dashed p-5 text-center transition",
          dragging ? "border-accent bg-accent-light" : "border-border hover:border-text-muted"
        )}
      >
        <input ref={inputRef} type="file" accept="image/*,application/pdf" onChange={handleChange} className="hidden" />
        {file ? (
          <div className="flex items-center justify-center gap-2">
            <svg className="h-4 w-4 text-text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <div className="text-start">
              <p className="text-sm font-medium text-text">{file.name}</p>
              <p className="text-xs text-text-muted">{(file.size / 1024).toFixed(0)} KB</p>
            </div>
          </div>
        ) : (
          <>
            <svg className="mx-auto mb-1.5 h-5 w-5 text-text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            <p className="text-xs text-text-secondary">{t("uploads.dragDrop")}</p>
            <p className="mt-0.5 text-[11px] text-text-muted">PDF, JPG, PNG</p>
          </>
        )}
      </div>

      {file && (
        <div className={clsx("flex gap-2 animate-slide-up", compact ? "flex-col" : "items-end")}>
          <div className="flex-1">
            <label className="text-[10px] font-bold uppercase tracking-wider text-text-secondary block mb-1">
              {t("uploads.category")}
            </label>
            <Select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="w-full text-xs py-1.5 h-auto"
            >
              {categories.map((c) => (
                <option key={c.value} value={c.value}>
                  {c.label}
                </option>
              ))}
            </Select>
          </div>
          <Button
            onClick={handleUpload}
            disabled={uploading}
            className={clsx("text-xs font-semibold px-4", compact ? "w-full py-2.5 mt-1" : "py-2")}
          >
            {uploading ? (
              <span className="flex items-center gap-1 justify-center">
                <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent" />
                {t("uploads.uploading")}
              </span>
            ) : (
              t("uploads.upload")
            )}
          </Button>
        </div>
      )}

      {error && <p className="text-xs text-danger">{error}</p>}
    </div>
  );
}
