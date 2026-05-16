import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'India Map Downloader',
  description: 'Search, explore, select, preview, and download detailed India map PDFs.'
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
