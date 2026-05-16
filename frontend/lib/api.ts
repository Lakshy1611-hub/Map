export type Place = {
  id: string | number;
  name: string;
  displayName: string;
  lat: number;
  lon: number;
  type?: string;
  category?: string;
  address?: Record<string, string>;
  boundingBox?: number[];
};

export type NearbyPlace = {
  id: string | number;
  name: string;
  type: string;
  lat: number;
  lon: number;
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:4000';

export async function searchIndia(query: string): Promise<Place[]> {
  const response = await fetch(`${API_BASE}/api/search?q=${encodeURIComponent(query)}`);
  if (!response.ok) throw new Error('Search failed');
  return response.json();
}

export async function reverseGeocode(lat: number, lon: number): Promise<Place> {
  const response = await fetch(`${API_BASE}/api/reverse?lat=${lat}&lon=${lon}`);
  if (!response.ok) throw new Error('Reverse geocode failed');
  return response.json();
}

export async function nearbyPlaces(lat: number, lon: number): Promise<NearbyPlace[]> {
  const response = await fetch(`${API_BASE}/api/nearby?lat=${lat}&lon=${lon}&radius=1600`);
  if (!response.ok) return [];
  return response.json();
}

export function buildShareUrl(place?: Place, zoom = 16) {
  if (!place) return typeof window !== 'undefined' ? window.location.href : '';
  const url = new URL(typeof window !== 'undefined' ? window.location.href : 'https://example.com');
  url.searchParams.set('lat', String(place.lat));
  url.searchParams.set('lon', String(place.lon));
  url.searchParams.set('z', String(zoom));
  url.searchParams.set('q', place.name);
  return url.toString();
}
