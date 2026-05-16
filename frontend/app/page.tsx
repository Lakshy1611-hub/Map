'use client';

import dynamic from 'next/dynamic';
import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Download, Layers3, MapPinned, Route, Search, ShieldCheck, Sparkles, WifiOff } from 'lucide-react';
import SearchHero from '../components/SearchHero';
import { Place, reverseGeocode } from '../lib/api';
import { copy, Language } from '../lib/i18n';

const MapWorkspace = dynamic(() => import('../components/MapWorkspace'), { ssr: false, loading: () => <div className="mx-auto max-w-7xl px-4 pb-16"><div className="glass h-[680px] animate-pulse rounded-[2rem]" /></div> });

const features = [
  { icon: Search, title: 'Universal India search', text: 'Find villages, cities, streets, colonies, landmarks, pincodes and coordinates with autocomplete.' },
  { icon: Layers3, title: 'Detailed hybrid maps', text: 'Switch between street, satellite, dark, and label overlays for roads, buildings, shops and area names.' },
  { icon: Download, title: 'Printable PDF export', text: 'Preview and download A4/A3 landscape or portrait map PDFs with crisp high-resolution rendering.' },
  { icon: Route, title: 'Premium map tools', text: 'Nearby recommendations, route points, distance measurement, custom markers and annotations.' },
  { icon: WifiOff, title: 'Offline-ready export', text: 'Render the visible selected map into a PDF that can be saved, printed or shared.' },
  { icon: ShieldCheck, title: 'Secure architecture', text: 'Express API proxy, clean React components, environment-based configuration and scalable structure.' }
];

export default function Home() {
  const [language, setLanguage] = useState<Language>('en');
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');
  const [place, setPlace] = useState<Place>();
  const t = copy[language];

  useEffect(() => {
    document.body.className = theme;
  }, [theme]);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const lat = Number(params.get('lat'));
    const lon = Number(params.get('lon'));
    if (Number.isFinite(lat) && Number.isFinite(lon)) {
      reverseGeocode(lat, lon).then(setPlace).catch(() => setPlace({ id: 'shared', name: params.get('q') || 'Shared location', displayName: `${lat}, ${lon}`, lat, lon }));
    }
  }, []);

  return (
    <main className="min-h-screen bg-slate-950 text-white transition light:bg-slate-100 light:text-slate-950">
      <SearchHero language={language} theme={theme} onLanguage={setLanguage} onTheme={setTheme} onSelect={setPlace} />

      <section className="mx-auto max-w-7xl px-4 pb-10">
        <div className="grid gap-4 md:grid-cols-3">
          {features.map((feature, index) => (
            <motion.article key={feature.title} initial={{ opacity: 0, y: 22 }} whileInView={{ opacity: 1, y: 0 }} transition={{ delay: index * .05 }} className="glass rounded-[2rem] p-6 transition hover:-translate-y-1 hover:shadow-glow">
              <feature.icon className="mb-4 text-cyan-300" />
              <h3 className="text-lg font-bold">{feature.title}</h3>
              <p className="mt-2 text-sm leading-6 text-slate-300 light:text-slate-600">{feature.text}</p>
            </motion.article>
          ))}
        </div>
      </section>

      <MapWorkspace place={place} language={language} theme={theme} onReversePlace={setPlace} />

      <section className="mx-auto max-w-7xl px-4 pb-20">
        <div className="glass rounded-[2rem] p-6 md:p-10">
          <div className="mb-8 flex items-center gap-3"><Sparkles className="text-fuchsia-300"/><h2 className="text-3xl font-black">{t.works}</h2></div>
          <div className="grid gap-5 md:grid-cols-4">
            {[
              ['1', 'Search', 'Type a pincode, coordinates, village, street, school, hospital, shop or landmark.'],
              ['2', 'Explore', 'Zoom, drag, switch satellite/street/dark layers, detect current location and inspect nearby places.'],
              ['3', 'Select', 'Use the rectangle or free polygon tool to mark the exact area you want to print.'],
              ['4', 'Export', 'Pick A4/A3 and portrait/landscape, preview, then download a high-quality PDF.']
            ].map(([step, title, text]) => (
              <div key={step} className="rounded-3xl border border-white/10 bg-white/10 p-5">
                <div className="mb-4 grid h-12 w-12 place-items-center rounded-2xl bg-gradient-to-br from-cyan-300 to-indigo-400 text-xl font-black text-slate-950">{step}</div>
                <h3 className="font-bold">{title}</h3>
                <p className="mt-2 text-sm leading-6 text-slate-300 light:text-slate-600">{text}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <footer className="border-t border-white/10 px-4 py-8 text-center text-sm text-slate-400">
        <MapPinned className="mx-auto mb-2 text-cyan-300" /> India Map Downloader • Built with Next.js, Tailwind CSS, Framer Motion, Leaflet and Express.
      </footer>
    </main>
  );
}
