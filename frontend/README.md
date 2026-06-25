# Frontend — AI Medical Monitor

Next.js 14 web app for hospital monitoring and AI diagnosis.

## Tech Stack

| Component | Technology |
|---|---|
| Framework | Next.js 14 (App Router) |
| Language | TypeScript |
| Styling | Tailwind CSS |
| Charts | Recharts |
| State | Zustand (auth) + React Context (i18n) |
| Real-time | WebSocket |
| i18n | Custom (Arabic RTL + English LTR) |

## Pages

| Page | Path | Description |
|---|---|---|
| Login | `/login` | Authentication |
| Home | `/` | Redirects to dashboard |
| Dashboard | `/dashboard` | All beds grid + live vitals |
| Bed Details | `/beds/[id]` | Real-time charts + history |
| Patients | `/patients` | Patient list + create |
| Patient Files | `/patients/[id]` | Upload medical files + list |
| Alerts | `/alerts` | Alerts log + acknowledge |
| Admin | `/admin` | User management (admin only) |

## Features

- **Bilingual** — Arabic (RTL) + English (LTR), toggle in navbar
- **Live vitals** — WebSocket streaming from ESP32 via backend
- **Real-time charts** — SpO2, heart rate, temperature over time
- **Color-coded status** — green (normal), yellow (warning), red (critical)
- **File upload** — Drag & drop PDF/images for lab results, imaging, reports
- **OCR extraction** — Trigger text extraction from uploaded files
- **Role-based UI** — Admin sees user management; others see relevant pages

## Development

```bash
cd frontend
npm install
npm run dev          # http://localhost:3000
```

Set `NEXT_PUBLIC_API_URL` in `.env.local` to point to the backend.

## Build

```bash
npm run build
npm run start
```

## Type Check

```bash
npm run typecheck    # tsc --noEmit
npm run lint         # eslint
```

## Default Login

| Username | Password | Role |
|---|---|---|
| admin | admin123 | admin |
| doctor | doctor123 | doctor |
| nurse | nurse123 | nurse |
