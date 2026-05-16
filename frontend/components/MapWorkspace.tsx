'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import L, { LatLngBoundsExpression, LatLngExpression } from 'leaflet';
import 'leaflet-draw';
import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';
import { motion } from 'framer-motion';
import { Crosshair, Download, Eye, Fullscreen, Heart, LocateFixed, MapPin, Navigation, Pencil, Route, Ruler, Share2, Sparkles } from 'lucide-react';
import { buildShareUrl, nearbyPlaces, Place, NearbyPlace, reverseGeocode } from '../lib/api';
import { copy, Language } from '../lib/i18n';

const INDIA_CENTER: LatLngExpression = [22.9734, 78.6569];
const markerIcon = new L.Icon({
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41]
});

type Props = { place?: Place; language: Language; theme: 'dark' | 'light'; onReversePlace: (place: Place) => void };
type ExportOptions = { format: 'a4' | 'a3'; orientation: 'landscape' | 'portrait'; zoom: number };

export default function MapWorkspace({ place, language, theme, onReversePlace }: Props) {
  const t = copy[language];
  const [exportOptions, setExportOptions] = useState<ExportOptions>({ format: 'a4', orientation: 'landscape', zoom: 17 });
  const [selectionBounds, setSelectionBounds] = useState<LatLngBoundsExpression | null>(null);
  const [nearby, setNearby] = useState<NearbyPlace[]>([]);
  const [favorites, setFavorites] = useState<Place[]>([]);
  const [distancePoints, setDistancePoints] = useState<LatLngExpression[]>([]);
  const [routePoints, setRoutePoints] = useState<LatLngExpression[]>([]);
  const [annotationMode, setAnnotationMode] = useState(false);
  const [customMarkers, setCustomMarkers] = useState<LatLngExpression[]>([]);
  const mapNodeRef = useRef<HTMLDivElement | null>(null);
  const shellRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<L.Map | null>(null);
  const selectedMarkerRef = useRef<L.Marker | null>(null);
  const nearbyLayerRef = useRef<L.LayerGroup | null>(null);
  const drawingLayerRef = useRef<L.FeatureGroup | null>(null);
  const vectorLayerRef = useRef<L.LayerGroup | null>(null);

  useEffect(() => {
    const fav = localStorage.getItem('india-map-favorites');
    if (fav) setFavorites(JSON.parse(fav));
  }, []);

  useEffect(() => {
    if (!mapNodeRef.current || mapRef.current) return;
    const map = L.map(mapNodeRef.current, { center: INDIA_CENTER, zoom: 5, zoomControl: true, doubleClickZoom: false });
    mapRef.current = map;

    const street = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { attribution: '&copy; OpenStreetMap contributors', crossOrigin: true }).addTo(map);
    const satellite = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', { attribution: 'Tiles &copy; Esri', crossOrigin: true });
    const labels = L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager_labels_under/{z}/{x}/{y}{r}.png', { attribution: '&copy; CARTO & OSM', crossOrigin: true }).addTo(map);
    const dark = L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', { attribution: '&copy; CARTO & OSM', crossOrigin: true });
    L.control.layers({ 'Street + labels': street, 'Satellite View': satellite }, { 'Detailed roads/buildings labels': labels, 'Dark professional map': dark }, { position: 'bottomleft' }).addTo(map);

    drawingLayerRef.current = new L.FeatureGroup().addTo(map);
    nearbyLayerRef.current = new L.LayerGroup().addTo(map);
    vectorLayerRef.current = new L.LayerGroup().addTo(map);
    const drawControl = new L.Control.Draw({
      position: 'topleft',
      edit: { featureGroup: drawingLayerRef.current, remove: true },
      draw: { rectangle: {}, polygon: {}, polyline: {}, marker: {}, circle: false, circlemarker: false }
    });
    map.addControl(drawControl);

    map.on(L.Draw.Event.CREATED, (event: any) => {
      const layer = event.layer;
      drawingLayerRef.current?.addLayer(layer);
      if (layer?.getBounds) setSelectionBounds(layer.getBounds());
      if (layer?.getLatLng) setCustomMarkers((items) => [...items, layer.getLatLng()]);
    });

    map.on('dblclick', async (event: L.LeafletMouseEvent) => {
      try { onReversePlace(await reverseGeocode(event.latlng.lat, event.latlng.lng)); } catch { /* optional */ }
    });

    return () => { map.remove(); mapRef.current = null; };
  }, [onReversePlace]);

  useEffect(() => {
    if (!place) return;
    nearbyPlaces(place.lat, place.lon).then(setNearby);
  }, [place]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !place) return;
    selectedMarkerRef.current?.remove();
    selectedMarkerRef.current = L.marker([place.lat, place.lon], { icon: markerIcon }).bindPopup(`<strong>${place.name}</strong><br/>${place.displayName || ''}`).addTo(map);
    if (place.boundingBox?.length === 4) {
      const [south, north, west, east] = place.boundingBox;
      map.fitBounds([[south, west], [north, east]], { padding: [44, 44], maxZoom: exportOptions.zoom });
    } else {
      map.flyTo([place.lat, place.lon], exportOptions.zoom, { duration: 0.8 });
    }
  }, [place, exportOptions.zoom]);

  useEffect(() => {
    const layer = nearbyLayerRef.current;
    if (!layer) return;
    layer.clearLayers();
    nearby.slice(0, 30).forEach((item) => L.marker([item.lat, item.lon], { icon: markerIcon }).bindPopup(`<strong>${item.name}</strong><br/>${item.type}`).addTo(layer));
  }, [nearby]);

  useEffect(() => {
    const layer = vectorLayerRef.current;
    if (!layer) return;
    layer.clearLayers();
    customMarkers.forEach((pos, idx) => L.marker(pos, { icon: markerIcon }).bindPopup(`Custom marker #${idx + 1}`).addTo(layer));
    if (distancePoints.length > 1) L.polyline(distancePoints, { color: '#22d3ee', weight: 4 }).addTo(layer);
    if (routePoints.length > 1) L.polyline(routePoints, { color: '#fb7185', weight: 5, dashArray: '10 10' }).addTo(layer);
  }, [customMarkers, distancePoints, routePoints]);

  const locate = () => {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(async (position) => {
      const { latitude, longitude } = position.coords;
      mapRef.current?.flyTo([latitude, longitude], 17);
      onReversePlace(await reverseGeocode(latitude, longitude));
    });
  };

  const share = async () => {
    const url = buildShareUrl(place, mapRef.current?.getZoom() || exportOptions.zoom);
    await navigator.clipboard?.writeText(url);
    if (navigator.share) await navigator.share({ title: t.title, text: place?.displayName || t.subtitle, url });
  };

  const addFavorite = () => {
    if (!place) return;
    const next = [place, ...favorites.filter((item) => item.id !== place.id)].slice(0, 8);
    setFavorites(next);
    localStorage.setItem('india-map-favorites', JSON.stringify(next));
  };

  const renderPdfBlob = async () => {
    const node = mapNodeRef.current;
    if (!node) return null;
    node.classList.add('print-map-export');
    await new Promise((resolve) => setTimeout(resolve, 250));
    const canvas = await html2canvas(node, { useCORS: true, allowTaint: true, scale: 2.4, backgroundColor: theme === 'dark' ? '#0f172a' : '#ffffff' });
    node.classList.remove('print-map-export');
    const pdf = new jsPDF({ orientation: exportOptions.orientation, unit: 'mm', format: exportOptions.format });
    const width = pdf.internal.pageSize.getWidth();
    const height = pdf.internal.pageSize.getHeight();
    const ratio = Math.min((width - 12) / canvas.width, (height - 24) / canvas.height);
    const imgWidth = canvas.width * ratio;
    const imgHeight = canvas.height * ratio;
    pdf.addImage(canvas.toDataURL('image/jpeg', 0.96), 'JPEG', (width - imgWidth) / 2, 8, imgWidth, imgHeight);
    pdf.setFontSize(10);
    pdf.text(`${place?.displayName || 'India Map'} | Zoom ${mapRef.current?.getZoom() || exportOptions.zoom}`, 10, height - 8, { maxWidth: width - 20 });
    if (selectionBounds) pdf.text('Selected area included. Scale preserved from current map zoom.', 10, height - 14);
    return pdf.output('blob');
  };

  const preview = async () => { const blob = await renderPdfBlob(); if (blob) window.open(URL.createObjectURL(blob), '_blank', 'noopener,noreferrer'); };
  const download = async () => {
    const blob = await renderPdfBlob();
    if (!blob) return;
    const anchor = document.createElement('a');
    anchor.href = URL.createObjectURL(blob);
    anchor.download = `${(place?.name || 'india-map').replace(/\W+/g, '-').toLowerCase()}-${exportOptions.format}-${exportOptions.orientation}.pdf`;
    anchor.click();
  };

  const distanceKm = useMemo(() => {
    if (distancePoints.length < 2) return 0;
    return distancePoints.slice(1).reduce((sum, point, index) => sum + L.latLng(distancePoints[index] as any).distanceTo(point as any), 0) / 1000;
  }, [distancePoints]);

  const currentPoint = useCallback(() => place ? [place.lat, place.lon] as LatLngExpression : mapRef.current?.getCenter() as unknown as LatLngExpression, [place]);

  return (
    <section id="map" className="mx-auto max-w-7xl px-4 pb-16">
      <div className="grid gap-5 lg:grid-cols-[1fr_360px]">
        <motion.div ref={shellRef} initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }} className="map-shell relative overflow-hidden rounded-[2rem] border border-white/15 bg-slate-950/60 p-2 shadow-glow">
          <div ref={mapNodeRef} className="leaflet-container" />
          <div className="no-export absolute right-4 top-4 z-[600] flex flex-col gap-2">
            <button className="glass rounded-2xl p-3 transition hover:scale-105" onClick={locate} title="Current location"><LocateFixed size={18} /></button>
            <button className="glass rounded-2xl p-3 transition hover:scale-105" onClick={() => shellRef.current?.requestFullscreen()} title="Fullscreen"><Fullscreen size={18} /></button>
            <button className="glass rounded-2xl p-3 transition hover:scale-105" onClick={share} title="Share map link"><Share2 size={18} /></button>
          </div>
        </motion.div>

        <aside className="space-y-4">
          <div className="glass rounded-[2rem] p-5">
            <div className="mb-4 flex items-center gap-3"><Crosshair className="text-cyan-300" /><h2 className="text-xl font-bold">{t.select}</h2></div>
            <p className="text-sm text-slate-300">Draw a rectangle or free polygon directly on the map, choose print settings, then preview or download a high-resolution PDF.</p>
            <div className="mt-5 grid grid-cols-2 gap-3 text-sm">
              <select className="rounded-2xl border border-white/10 bg-slate-950/70 p-3" value={exportOptions.format} onChange={(e) => setExportOptions({ ...exportOptions, format: e.target.value as any })}><option value="a4">A4</option><option value="a3">A3</option></select>
              <select className="rounded-2xl border border-white/10 bg-slate-950/70 p-3" value={exportOptions.orientation} onChange={(e) => setExportOptions({ ...exportOptions, orientation: e.target.value as any })}><option value="landscape">Landscape</option><option value="portrait">Portrait</option></select>
              <label className="col-span-2 rounded-2xl border border-white/10 bg-slate-950/70 p-3">Zoom level: {exportOptions.zoom}<input className="mt-2 w-full accent-cyan-300" type="range" min="5" max="20" value={exportOptions.zoom} onChange={(e) => setExportOptions({ ...exportOptions, zoom: Number(e.target.value) })} /></label>
            </div>
            <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2">
              <button onClick={preview} className="rounded-2xl bg-white/10 px-4 py-3 font-semibold transition hover:bg-white/20"><Eye className="mr-2 inline" size={18}/>{t.preview}</button>
              <button onClick={download} className="rounded-2xl bg-gradient-to-r from-cyan-400 to-indigo-500 px-4 py-3 font-bold text-slate-950 transition hover:scale-[1.02]"><Download className="mr-2 inline" size={18}/>{t.download}</button>
            </div>
          </div>

          <div className="glass rounded-[2rem] p-5">
            <h3 className="mb-3 flex items-center gap-2 font-bold"><Sparkles className="text-fuchsia-300" size={18}/> Premium tools</h3>
            <div className="grid grid-cols-2 gap-2 text-sm">
              <button onClick={addFavorite} className="rounded-2xl bg-white/10 p-3 text-left hover:bg-white/20"><Heart size={16}/> Save favorite</button>
              <button onClick={() => setAnnotationMode(!annotationMode)} className="rounded-2xl bg-white/10 p-3 text-left hover:bg-white/20"><Pencil size={16}/> Annotate</button>
              <button onClick={() => { const pos = currentPoint(); if (pos) setDistancePoints([...distancePoints, pos]); }} className="rounded-2xl bg-white/10 p-3 text-left hover:bg-white/20"><Ruler size={16}/> Measure</button>
              <button onClick={() => { const pos = currentPoint(); if (pos) setRoutePoints([...routePoints, pos]); }} className="rounded-2xl bg-white/10 p-3 text-left hover:bg-white/20"><Route size={16}/> Route point</button>
            </div>
            {annotationMode && <p className="mt-3 text-xs text-fuchsia-100">Annotation mode: use the map marker draw tool to add custom markers.</p>}
            {distanceKm > 0 && <p className="mt-3 text-sm text-cyan-200">Measured distance: {distanceKm.toFixed(2)} km</p>}
          </div>

          <div className="glass rounded-[2rem] p-5">
            <h3 className="mb-3 flex items-center gap-2 font-bold"><MapPin className="text-emerald-300" size={18}/> {t.nearby}</h3>
            <div className="max-h-52 space-y-2 overflow-auto pr-1">
              {nearby.slice(0, 12).map((item) => <button key={item.id} onClick={() => mapRef.current?.flyTo([item.lat, item.lon], 18)} className="w-full rounded-2xl bg-white/10 p-3 text-left text-sm transition hover:bg-white/20"><b>{item.name}</b><br/><span className="text-slate-300">{item.type}</span></button>)}
              {!nearby.length && <p className="text-sm text-slate-300">Search a location to load shops, schools, hospitals, landmarks and other nearby places.</p>}
            </div>
          </div>

          <div className="glass rounded-[2rem] p-5">
            <h3 className="mb-3 flex items-center gap-2 font-bold"><Navigation size={18}/> {t.favorites}</h3>
            <div className="space-y-2">
              {favorites.map((item) => <button key={item.id} onClick={() => onReversePlace(item)} className="w-full truncate rounded-2xl bg-white/10 p-3 text-left text-sm hover:bg-white/20">{item.name}</button>)}
              {!favorites.length && <p className="text-sm text-slate-300">Favorite places appear here for quick access.</p>}
            </div>
          </div>
        </aside>
      </div>
    </section>
  );
}
