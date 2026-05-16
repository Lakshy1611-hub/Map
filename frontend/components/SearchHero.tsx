'use client';

import { FormEvent, useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { Languages, Map, Moon, Search, Sun } from 'lucide-react';
import { Place, searchIndia } from '../lib/api';
import { copy, Language } from '../lib/i18n';

type Props = {
  language: Language;
  theme: 'dark' | 'light';
  onLanguage: (language: Language) => void;
  onTheme: (theme: 'dark' | 'light') => void;
  onSelect: (place: Place) => void;
};

const coordinatePattern = /^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$/;

export default function SearchHero({ language, theme, onLanguage, onTheme, onSelect }: Props) {
  const t = copy[language];
  const [query, setQuery] = useState('');
  const [suggestions, setSuggestions] = useState<Place[]>([]);
  const [loading, setLoading] = useState(false);
  const [recent, setRecent] = useState<Place[]>([]);

  useEffect(() => {
    const stored = localStorage.getItem('india-map-recent');
    if (stored) setRecent(JSON.parse(stored));
  }, []);

  useEffect(() => {
    const timer = setTimeout(async () => {
      if (query.trim().length < 3 || coordinatePattern.test(query)) return setSuggestions([]);
      setLoading(true);
      try {
        setSuggestions(await searchIndia(query));
      } finally {
        setLoading(false);
      }
    }, 320);
    return () => clearTimeout(timer);
  }, [query]);

  const quick = useMemo(() => ['India Gate Delhi', 'Bandra West Mumbai', 'Mysuru Palace', '560001', 'Varanasi Ghat', 'Connaught Place'], []);

  const selectPlace = (place: Place) => {
    onSelect(place);
    setQuery(place.displayName || place.name);
    const next = [place, ...recent.filter((item) => item.id !== place.id)].slice(0, 7);
    setRecent(next);
    localStorage.setItem('india-map-recent', JSON.stringify(next));
  };

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    const match = query.match(coordinatePattern);
    if (match) {
      const place = { id: `coord-${query}`, name: 'Coordinates', displayName: `${match[1]}, ${match[2]}`, lat: Number(match[1]), lon: Number(match[2]) };
      selectPlace(place);
      return;
    }
    const [first] = await searchIndia(query);
    if (first) selectPlace(first);
  };

  return (
    <header className="relative overflow-hidden px-4 py-6 sm:py-8">
      <div className="absolute inset-0 -z-10 bg-radial-grid" />
      <motion.div aria-hidden className="absolute left-1/2 top-16 -z-10 h-[520px] w-[520px] -translate-x-1/2 rounded-full border border-cyan-300/20 bg-cyan-300/10 blur-3xl" animate={{ scale: [1, 1.08, 1], rotate: [0, 8, 0] }} transition={{ duration: 8, repeat: Infinity }} />

      <nav className="mx-auto flex max-w-7xl items-center justify-between rounded-3xl border border-white/10 bg-white/5 p-3 backdrop-blur-xl">
        <div className="flex items-center gap-3 font-black tracking-tight"><span className="rounded-2xl bg-gradient-to-br from-cyan-300 to-indigo-400 p-2 text-slate-950"><Map /></span>{t.title}</div>
        <div className="flex items-center gap-2">
          <button onClick={() => onLanguage(language === 'en' ? 'hi' : 'en')} className="rounded-2xl bg-white/10 p-3 transition hover:bg-white/20" title="Language"><Languages size={18}/></button>
          <button onClick={() => onTheme(theme === 'dark' ? 'light' : 'dark')} className="rounded-2xl bg-white/10 p-3 transition hover:bg-white/20" title="Theme">{theme === 'dark' ? <Sun size={18}/> : <Moon size={18}/>}</button>
        </div>
      </nav>

      <section className="mx-auto grid max-w-7xl items-center gap-8 py-14 lg:grid-cols-[1.1fr_.9fr] lg:py-20">
        <motion.div initial={{ opacity: 0, y: 26 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: .7 }}>
          <span className="mb-5 inline-flex rounded-full border border-cyan-300/30 bg-cyan-300/10 px-4 py-2 text-sm font-semibold text-cyan-100">AI-powered smart location detection • printable PDF maps</span>
          <h1 className="max-w-4xl text-5xl font-black leading-tight tracking-tight sm:text-6xl lg:text-7xl">Search India. Select an area. Download a beautiful map PDF.</h1>
          <p className="mt-5 max-w-2xl text-lg leading-8 text-slate-200">{t.subtitle}</p>

          <form onSubmit={submit} className="relative mt-8 max-w-3xl">
            <div className="glass flex items-center gap-3 rounded-[2rem] p-2">
              <Search className="ml-3 text-cyan-200" />
              <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder={t.search} className="min-h-14 flex-1 bg-transparent text-base outline-none placeholder:text-slate-300" />
              <button className="rounded-[1.5rem] bg-gradient-to-r from-cyan-300 to-indigo-400 px-6 py-4 font-bold text-slate-950 shadow-glow transition hover:scale-105">Search</button>
            </div>
            {(suggestions.length > 0 || loading) && (
              <div className="glass absolute z-[800] mt-3 max-h-80 w-full overflow-auto rounded-[1.5rem] p-2">
                {loading && <p className="p-3 text-sm text-slate-300">Finding exact Indian locations…</p>}
                {suggestions.map((place) => <button type="button" key={place.id} onClick={() => selectPlace(place)} className="w-full rounded-2xl p-3 text-left transition hover:bg-white/15"><b>{place.name}</b><br/><span className="text-sm text-slate-300">{place.displayName}</span></button>)}
              </div>
            )}
          </form>

          <div className="mt-5 flex flex-wrap gap-2">
            {quick.map((item) => <button key={item} onClick={() => setQuery(item)} className="rounded-full bg-white/10 px-4 py-2 text-sm transition hover:bg-white/20">{item}</button>)}
          </div>
        </motion.div>

        <motion.div initial={{ opacity: 0, scale: .92 }} animate={{ opacity: 1, scale: 1 }} className="glass relative mx-auto aspect-square w-full max-w-lg overflow-hidden rounded-[3rem] p-8">
          <div className="absolute inset-8 rounded-[2.5rem] border border-cyan-200/20 bg-[linear-gradient(135deg,rgba(34,211,238,.25),rgba(99,102,241,.18))]" />
          <div className="absolute inset-0 opacity-40 [background-image:linear-gradient(rgba(255,255,255,.18)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,.18)_1px,transparent_1px)] [background-size:38px_38px]" />
          <motion.div className="absolute left-[26%] top-[18%] h-[58%] w-[38%] rounded-[48%_52%_54%_46%] border-2 border-cyan-200/70 bg-cyan-200/10 shadow-glow" animate={{ y: [0, -14, 0], rotate: [0, 2, 0] }} transition={{ duration: 5, repeat: Infinity }} />
          <div className="absolute bottom-8 left-8 right-8 rounded-3xl bg-slate-950/70 p-5 backdrop-blur"><p className="text-sm text-slate-300">Recent searches</p><div className="mt-2 space-y-2">{recent.slice(0,3).map((item) => <button key={item.id} onClick={() => selectPlace(item)} className="block w-full truncate rounded-xl bg-white/10 px-3 py-2 text-left text-sm hover:bg-white/20">{item.name}</button>)}</div></div>
        </motion.div>
      </section>
    </header>
  );
}
