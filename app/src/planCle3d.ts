/**
 * « Animer avec H3 » depuis Relief (recherche/25 §5) : la vue 3D telle que la personne l'a tournée devient le plan clé
 * d'une vidéo H3 (I2VA). L'objet garde exactement sa forme et ses couleurs dans la première image ; H3 l'anime, ajoute
 * lumière, reflets et son. Le rendu WebGL du visualiseur (fond transparent) est posé sur un fond de studio, au format
 * 16:9 de FastH3, objet centré sur 70 % de la hauteur.
 */
export const FONDS_PLAN_CLE = {
  studio: { nom: 'Studio sombre', centre: '#4a4a52', bord: '#0c0c0f' },
  clair: { nom: 'Studio clair', centre: '#f4f4f2', bord: '#b9b9b6' },
  nuit: { nom: 'Nuit bleue', centre: '#1d2b4a', bord: '#03050b' },
} as const;
export type FondPlanCle = keyof typeof FONDS_PLAN_CLE;

/** Boîte des pixels non transparents d'une image (l'objet), ou null si l'image est vide. */
export function boiteOpaque(d: Uint8ClampedArray, w: number, h: number): { x: number; y: number; w: number; h: number } | null {
  let x0 = w, y0 = h, x1 = -1, y1 = -1;
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    if (d[(y * w + x) * 4 + 3] > 8) { if (x < x0) x0 = x; if (x > x1) x1 = x; if (y < y0) y0 = y; if (y > y1) y1 = y; }
  }
  return x1 < 0 ? null : { x: x0, y: y0, w: x1 - x0 + 1, h: y1 - y0 + 1 };
}

/** Compose le plan clé (PNG) depuis le canevas du visualiseur. */
export async function planCleDepuisCanevas(source: HTMLCanvasElement, fond: FondPlanCle = 'studio', largeur = 832, hauteur = 480): Promise<Blob> {
  const tmp = document.createElement('canvas');
  tmp.width = source.width; tmp.height = source.height;
  const t = tmp.getContext('2d')!;
  t.drawImage(source, 0, 0);
  const b = boiteOpaque(t.getImageData(0, 0, tmp.width, tmp.height).data, tmp.width, tmp.height);
  if (!b) throw new Error('La vue 3D est vide : attends que le modèle soit chargé.');
  const c = document.createElement('canvas');
  c.width = largeur; c.height = hauteur;
  const g = c.getContext('2d')!;
  const f = FONDS_PLAN_CLE[fond];
  const grad = g.createRadialGradient(largeur / 2, hauteur * 0.42, 10, largeur / 2, hauteur * 0.42, largeur * 0.62);
  grad.addColorStop(0, f.centre); grad.addColorStop(1, f.bord);
  g.fillStyle = grad; g.fillRect(0, 0, largeur, hauteur);
  const echelle = Math.min((hauteur * 0.7) / b.h, (largeur * 0.8) / b.w);
  const w = b.w * echelle, h = b.h * echelle, x = (largeur - w) / 2, y = (hauteur - h) / 2;
  // Ombre de contact douce sous l'objet : il repose sur quelque chose, H3 n'invente pas une chute.
  g.save(); g.filter = 'blur(14px)'; g.fillStyle = 'rgba(0,0,0,0.55)';
  g.beginPath(); g.ellipse(largeur / 2, y + h * 0.98, w * 0.42, Math.max(6, h * 0.05), 0, 0, Math.PI * 2); g.fill(); g.restore();
  g.drawImage(tmp, b.x, b.y, b.w, b.h, x, y, w, h);
  return await new Promise<Blob>((ok, ko) => c.toBlob((x) => (x ? ok(x) : ko(new Error('capture impossible'))), 'image/png'));
}
