require('dotenv').config();
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');

const app = express();
const PORT = process.env.PORT || 4000;
const NOMINATIM = 'https://nominatim.openstreetmap.org';
const OVERPASS = 'https://overpass-api.de/api/interpreter';

app.use(helmet({ crossOriginResourcePolicy: false }));
app.use(cors({ origin: process.env.FRONTEND_ORIGIN || '*'}));
app.use(express.json({ limit: '10mb' }));

const headers = {
  'User-Agent': process.env.NOMINATIM_USER_AGENT || 'IndiaMapDownloader/1.0 (contact@example.com)',
  'Accept-Language': 'en,hi;q=0.9'
};

app.get('/api/health', (_req, res) => {
  res.json({ ok: true, service: 'India Map Downloader API', timestamp: new Date().toISOString() });
});

app.get('/api/search', async (req, res) => {
  try {
    const q = String(req.query.q || '').trim();
    if (!q) return res.status(400).json({ error: 'Query is required' });

    const params = new URLSearchParams({
      q,
      format: 'jsonv2',
      addressdetails: '1',
      extratags: '1',
      namedetails: '1',
      limit: '8',
      countrycodes: 'in',
      polygon_geojson: '0'
    });

    const response = await fetch(`${NOMINATIM}/search?${params}`, { headers });
    if (!response.ok) throw new Error(`Search provider returned ${response.status}`);
    const data = await response.json();
    res.json(data.map(normalizePlace));
  } catch (error) {
    res.status(502).json({ error: 'Unable to search location', details: error.message });
  }
});

app.get('/api/reverse', async (req, res) => {
  try {
    const lat = Number(req.query.lat);
    const lon = Number(req.query.lon);
    if (!Number.isFinite(lat) || !Number.isFinite(lon)) return res.status(400).json({ error: 'Valid lat and lon are required' });

    const params = new URLSearchParams({ lat: String(lat), lon: String(lon), format: 'jsonv2', addressdetails: '1', zoom: '18' });
    const response = await fetch(`${NOMINATIM}/reverse?${params}`, { headers });
    if (!response.ok) throw new Error(`Reverse provider returned ${response.status}`);
    const data = await response.json();
    res.json(normalizePlace(data));
  } catch (error) {
    res.status(502).json({ error: 'Unable to reverse geocode', details: error.message });
  }
});

app.get('/api/nearby', async (req, res) => {
  try {
    const lat = Number(req.query.lat);
    const lon = Number(req.query.lon);
    const radius = Math.min(Number(req.query.radius) || 1200, 4000);
    if (!Number.isFinite(lat) || !Number.isFinite(lon)) return res.status(400).json({ error: 'Valid lat and lon are required' });

    const query = `
      [out:json][timeout:18];
      (
        node(around:${radius},${lat},${lon})[amenity];
        node(around:${radius},${lat},${lon})[shop];
        node(around:${radius},${lat},${lon})[tourism];
        node(around:${radius},${lat},${lon})[historic];
        way(around:${radius},${lat},${lon})[amenity];
        way(around:${radius},${lat},${lon})[shop];
      );
      out center tags 40;
    `;

    const response = await fetch(OVERPASS, {
      method: 'POST',
      headers: { ...headers, 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ data: query })
    });
    if (!response.ok) throw new Error(`Nearby provider returned ${response.status}`);
    const data = await response.json();
    res.json((data.elements || []).map((item) => ({
      id: item.id,
      name: item.tags?.name || item.tags?.amenity || item.tags?.shop || 'Nearby place',
      type: item.tags?.amenity || item.tags?.shop || item.tags?.tourism || item.tags?.historic || 'place',
      lat: item.lat || item.center?.lat,
      lon: item.lon || item.center?.lon,
      tags: item.tags || {}
    })).filter((item) => item.lat && item.lon));
  } catch (error) {
    res.status(502).json({ error: 'Unable to fetch nearby places', details: error.message });
  }
});

app.post('/api/pdf-job', (req, res) => {
  const { title = 'India Map Download', bounds, format = 'A4', orientation = 'landscape', zoom } = req.body || {};
  res.json({
    id: `pdf_${Date.now()}`,
    title,
    bounds,
    format,
    orientation,
    zoom,
    status: 'ready',
    message: 'Client-side vector-aware PDF export is ready. Use the browser Download Map PDF action.'
  });
});

function normalizePlace(place) {
  return {
    id: place.place_id || place.osm_id,
    name: place.name || place.display_name?.split(',')[0] || 'Selected location',
    displayName: place.display_name,
    lat: Number(place.lat),
    lon: Number(place.lon),
    type: place.type,
    category: place.category || place.class,
    importance: place.importance,
    address: place.address || {},
    boundingBox: place.boundingbox?.map(Number)
  };
}

app.listen(PORT, () => {
  console.log(`India Map Downloader API running on http://localhost:${PORT}`);
});
