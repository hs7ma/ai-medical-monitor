import { useAuth } from "./auth";

const API_BASE = "";

async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  const headers: Record<string, string> = {
    ...((options.headers as Record<string, string>) || {}),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (options.body && !(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  if (res.status === 401) {
    if (typeof window !== "undefined") {
      useAuth.getState().logout();
      window.location.href = "/login";
    }
    throw new Error("Unauthorized");
  }
  if (!res.ok) {
    const msg = await res.text();
    throw new Error(msg || `HTTP ${res.status}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const api = {
  login: (username: string, password: string) =>
    apiFetch<{
      access_token: string;
      token_type: string;
      role: string;
      full_name: string;
    }>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),

  listBeds: () => apiFetch<any[]>("/api/beds"),
  getBedVitals: (bedId: string, minutes = 60) =>
    apiFetch<any[]>(`/api/beds/${bedId}/vitals?minutes=${minutes}`),

  listPatients: () => apiFetch<any[]>("/api/patients"),
  getPatient: (id: number) => apiFetch<any>(`/api/patients/${id}`),
  createPatient: (data: any) =>
    apiFetch<any>("/api/patients", { method: "POST", body: JSON.stringify(data) }),

  submitVitals: (patientId: number, data: any) =>
    apiFetch<any>(`/api/patients/${patientId}/vitals`, { method: "POST", body: JSON.stringify(data) }),
  getVitals: (patientId: number, limit = 50) =>
    apiFetch<any[]>(`/api/patients/${patientId}/vitals?limit=${limit}`),
  getLatestVitals: (patientId: number) =>
    apiFetch<any>(`/api/patients/${patientId}/vitals/latest`),

  listUploads: (patientId: number) =>
    apiFetch<any[]>(`/api/patients/${patientId}/uploads`),
  uploadFile: (patientId: number, file: File, category: string) => {
    const fd = new FormData();
    fd.append("file", file);
    fd.append("category", category);
    return apiFetch<any>(`/api/patients/${patientId}/uploads`, { method: "POST", body: fd });
  },
  deleteFile: (fileId: number) => apiFetch<void>(`/api/uploads/${fileId}`, { method: "DELETE" }),
  extractText: (fileId: number) =>
    apiFetch<any>(`/api/uploads/${fileId}/extract`, { method: "POST" }),
  fileUrl: (fileId: number) => `${API_BASE}/api/uploads/${fileId}`,

  listAlerts: (status = "active") =>
    apiFetch<any[]>(`/api/alerts?status_filter=${status}`),
  ackAlert: (id: number) =>
    apiFetch<any>(`/api/alerts/${id}/ack`, { method: "POST" }),

  listUsers: () => apiFetch<any[]>("/api/admin/users"),
  createUser: (data: any) =>
    apiFetch<any>("/api/admin/users", { method: "POST", body: JSON.stringify(data) }),

  // === Diagnosis Chat ===
  startSession: (patientId: number, title?: string) =>
    apiFetch<any>("/api/diagnosis/sessions", { method: "POST", body: JSON.stringify({ patient_id: patientId, title }) }),
  listSessions: (patientId?: number) =>
    apiFetch<any[]>(`/api/diagnosis/sessions${patientId ? `?patient_id=${patientId}` : ""}`),
  getSession: (sessionId: number) =>
    apiFetch<any>(`/api/diagnosis/sessions/${sessionId}`),
  getMessages: (sessionId: number) =>
    apiFetch<any[]>(`/api/diagnosis/sessions/${sessionId}/messages`),
  sendMessage: (sessionId: number, message: string, fileIds?: number[]) =>
    apiFetch<any>(`/api/diagnosis/sessions/${sessionId}/messages`, { method: "POST", body: JSON.stringify({ message, file_ids: fileIds }) }),
  getDiagnosis: (sessionId: number) =>
    apiFetch<any>(`/api/diagnosis/sessions/${sessionId}/diagnosis`),
  deleteSession: (sessionId: number) =>
    apiFetch<void>(`/api/diagnosis/sessions/${sessionId}`, { method: "DELETE" }),
  streamUrl: (sessionId: number) => `${API_BASE}/api/diagnosis/sessions/${sessionId}/stream`,
  extractFileIndicators: (patientId: number, fileIds: number[]) =>
    apiFetch<any>(`/api/diagnosis/patients/${patientId}/extract-file-indicators`, {
      method: "POST",
      body: JSON.stringify({ file_ids: fileIds }),
    }),

  // === ML Prediction ===
  mlStatus: () => apiFetch<{ available: boolean }>("/api/ml/status"),
  predictHeart: (features: any) =>
    apiFetch<any>("/api/ml/predict/heart", { method: "POST", body: JSON.stringify(features) }),
};
