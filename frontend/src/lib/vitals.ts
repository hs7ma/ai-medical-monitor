export const getVitalStatus = (vital: "spo2" | "hr" | "temp", value: number | null | undefined) => {
  if (value === null || value === undefined || value <= 0) return "no-data";
  if (vital === "spo2") {
    if (value >= 95) return "normal";
    if (value >= 90) return "warning";
    return "critical";
  }
  if (vital === "hr") {
    if (value >= 60 && value <= 100) return "normal";
    if ((value >= 50 && value < 60) || (value > 100 && value <= 110)) return "warning";
    return "critical";
  }
  if (vital === "temp") {
    if (value >= 36.1 && value <= 37.2) return "normal";
    if (value > 37.2 && value <= 38.0) return "warning";
    return "critical";
  }
  return "no-data";
};

export const statusColor: Record<string, string> = {
  normal: "#22c55e",
  warning: "#f59e0b",
  critical: "#ef4444",
  "no-data": "#6b7280",
};

export const formatTime = (iso: string) => {
  try {
    return new Date(iso).toLocaleTimeString("en-GB", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  } catch {
    return iso;
  }
};

export const formatDate = (iso: string) => {
  try {
    return new Date(iso).toLocaleDateString("en-GB", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    });
  } catch {
    return iso;
  }
};
