/** Petites icônes du studio (SVG en ligne, trait de 1,6 px, couleur du texte). */
import type { SVGProps } from 'react';

const base: SVGProps<SVGSVGElement> = { width: 16, height: 16, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', strokeWidth: 1.7, strokeLinecap: 'round', strokeLinejoin: 'round', 'aria-hidden': true };

export const IcVideo = (p: SVGProps<SVGSVGElement>) => <svg {...base} {...p}><rect x="3" y="6" width="13" height="12" rx="2" /><path d="m16 10 5-3v10l-5-3" /></svg>;
export const IcImage = (p: SVGProps<SVGSVGElement>) => <svg {...base} {...p}><rect x="3" y="4" width="18" height="16" rx="2" /><circle cx="9" cy="10" r="1.6" /><path d="m21 16-5-5-8 9" /></svg>;
export const IcFilm = (p: SVGProps<SVGSVGElement>) => <svg {...base} {...p}><rect x="3" y="4" width="18" height="16" rx="2" /><path d="M7 4v16M17 4v16M3 9h4M3 15h4M17 9h4M17 15h4" /></svg>;
export const IcEtincelle = (p: SVGProps<SVGSVGElement>) => <svg {...base} {...p}><path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z" /><path d="M19 16l.7 2.1L22 19l-2.3.9L19 22l-.7-2.1L16 19l2.3-.9z" /></svg>;
export const IcRond = (p: SVGProps<SVGSVGElement>) => <svg {...base} {...p}><path d="M21 12a9 9 0 1 1-3-6.7" /></svg>;

/** Logo : la mosaïque « braise » de Nexora qui se résout en N. */
export function Marque({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" aria-hidden>
      <rect x="1" y="1" width="6" height="22" fill="#ff5a1f" />
      <rect x="17" y="1" width="6" height="22" fill="#ff5a1f" />
      <rect x="7" y="5" width="5" height="5" fill="#ff8a1f" />
      <rect x="12" y="10" width="5" height="5" fill="#ffb11a" />
    </svg>
  );
}

/** Glyphe d'un rapport d'image (rectangle à la bonne proportion). */
export function Ratio({ v }: { v: '16:9' | '9:16' | '1:1' }) {
  const [w, h] = v === '16:9' ? [18, 10] : v === '9:16' ? [10, 18] : [14, 14];
  return <span className="st-ratio" style={{ width: w, height: h }} />;
}
