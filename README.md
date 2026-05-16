# India Map Downloader

A modern, fully responsive Google Maps-style web application for searching locations in India, exploring detailed interactive maps, selecting an area, previewing the result, and downloading high-quality printable map PDFs.

## Features

- Search any Indian village, city, colony, street, landmark, pincode, or coordinates.
- Autocomplete suggestions powered by the backend Nominatim proxy.
- Interactive Leaflet maps with zoom, drag, fullscreen, current location, share links, pins, labels, and nearby places.
- Street, satellite, detailed label, and dark professional map layers.
- Rectangle and free-form polygon area selection.
- A4/A3, landscape/portrait PDF preview and download.
- Hindi/English language toggle, dark/light mode, favorites, recent searches, distance, route and annotation tools.
- Premium glassmorphism UI, gradients, animations, rounded cards, and responsive layouts.
- Node.js + Express backend for geocoding, reverse geocoding and nearby place recommendations.

## Folder structure

```text
.
├── backend/
│   └── server.js              # Express API for search, reverse geocoding, nearby places and PDF job metadata
├── frontend/
│   ├── app/                   # Next.js app router pages and global styles
│   ├── components/            # Search hero and Leaflet map workspace
│   ├── lib/                   # API client and translations
│   ├── next.config.mjs
│   ├── tailwind.config.ts
│   └── tsconfig.json
├── .env.example
└── package.json
```

## Installation

```bash
npm install
cp .env.example .env.local
```

Update `NOMINATIM_USER_AGENT` in `.env.local` with a real contact email before production use.

## Development

Run the frontend and backend together:

```bash
npm run dev
```

Or run them separately:

```bash
npm run dev:backend
npm run dev:frontend
```

- Frontend: <http://localhost:3000>
- Backend: <http://localhost:4000/api/health>

## Build

```bash
npm run build
```

## Deployment

### Frontend

Deploy the `frontend` Next.js app to Vercel, Netlify, a Node server, or Docker. Set:

```bash
NEXT_PUBLIC_API_BASE=https://your-api.example.com
```

### Backend

Deploy `backend/server.js` to Render, Fly.io, Railway, ECS, Cloud Run, or a VPS. Set:

```bash
PORT=4000
FRONTEND_ORIGIN=https://your-frontend.example.com
NOMINATIM_USER_AGENT=IndiaMapDownloader/1.0 (your-email@example.com)
```

### Production notes

- Use a commercial or self-hosted tile provider for heavy production traffic.
- Respect OpenStreetMap/Nominatim usage policies and cache results when scaling.
- For fully vector PDF output at enterprise scale, add a server-side static map renderer with licensed vector tile data. The included client export preserves the visible map at high resolution and keeps labels/roads/buildings clear for practical print use.
