/**
 * Cartons de texte (titre, slogan, appel à l'action) posés EN CODE, jamais dessinés par le modèle vidéo (règle de la
 * maison : texte et logo toujours posés en code). Un carton est un court plan : fond sombre de la marque, texte blanc
 * centré, filet orange, fondu d'entrée et de sortie ; rendu par ffmpeg avec libass (filtre `ass`), présent dans le
 * ffmpeg statique du poste comme dans celui de la VM, alors que `drawtext` ne l'est pas partout.
 */

export interface Carton { texte: string; position: 'debut' | 'fin' }

/** Échappe le texte pour une ligne Dialogue ASS (accolades et barres obliques inverses sont des commandes). */
export function texteAss(t: string): string {
  return t.replace(/\{[^}]*\}/g, '').replace(/\\/g, '＼').replace(/[{}]/g, '').replace(/\r?\n/g, '\\N').trim();
}

/** Coupe un texte en lignes de `max` caractères au plus (sur les espaces), trois lignes au plus. */
export function couperLignes(t: string, max: number): string[] {
  const mots = t.trim().split(/\s+/).filter(Boolean);
  const lignes: string[] = [];
  let l = '';
  for (const m of mots) {
    if (l && (l + ' ' + m).length > max) { lignes.push(l); l = m; } else l = l ? `${l} ${m}` : m;
  }
  if (l) lignes.push(l);
  return lignes.slice(0, 3);
}

const temps = (s: number) => {
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), r = s % 60;
  return `${h}:${String(m).padStart(2, '0')}:${r.toFixed(2).padStart(5, '0')}`;
};

/** Fichier ASS d'un carton, à la taille du film. */
export function fichierAss(texte: string, o: { w: number; h: number; dureeS: number; police?: string }): string {
  const court = Math.min(o.w, o.h);
  const taille = Math.round(court * (o.w < o.h ? 0.085 : 0.075));
  const lignes = couperLignes(texte, o.w < o.h ? 16 : 26).map(texteAss);
  const police = o.police ?? 'DejaVu Sans';
  const filet = Math.round(court * 0.12);
  const yFilet = Math.round(o.h / 2 + (lignes.length * taille * 1.15) / 2 + taille * 0.5);
  return [
    '[Script Info]', 'ScriptType: v4.00+', `PlayResX: ${o.w}`, `PlayResY: ${o.h}`, 'WrapStyle: 2', '',
    '[V4+ Styles]',
    'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding',
    `Style: Carton,${police},${taille},&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,0,0,5,40,40,0,1`,
    '',
    '[Events]',
    'Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text',
    `Dialogue: 0,${temps(0)},${temps(o.dureeS)},Carton,,0,0,0,,{\\fad(300,300)}${lignes.join('\\N')}`,
    // Filet orange (couleur signal de la marque, BGR en ASS) sous le texte.
    `Dialogue: 1,${temps(0.15)},${temps(o.dureeS)},Carton,,0,0,0,,{\\fad(300,300)\\an7\\pos(${Math.round((o.w - filet) / 2)},${yFilet})\\1c&H1F5AFF&\\bord0\\p1}m 0 0 l ${filet} 0 ${filet} ${Math.max(4, Math.round(court * 0.008))} 0 ${Math.max(4, Math.round(court * 0.008))}{\\p0}`,
    '',
  ].join('\n');
}

/** Arguments ffmpeg qui rendent un carton en MP4 (H.264, 24 i/s ; piste son muette si le film a du son). */
export function argsCarton(ass: string, sortie: string, o: { w: number; h: number; dureeS: number; son: boolean; dossierPolices?: string }): string[] {
  const echap = (p: string) => p.replace(/\\/g, '/').replace(/:/g, '\\:').replace(/'/g, "\\'");
  const filtre = `ass='${echap(ass)}'${o.dossierPolices ? `:fontsdir='${echap(o.dossierPolices)}'` : ''},format=yuv420p`;
  return [
    '-y', '-f', 'lavfi', '-i', `color=c=0x0E0E10:s=${o.w}x${o.h}:r=24:d=${o.dureeS}`,
    ...(o.son ? ['-f', 'lavfi', '-i', `anullsrc=r=48000:cl=stereo`] : []),
    '-vf', filtre,
    ...(o.son ? ['-map', '0:v', '-map', '1:a', '-c:a', 'aac', '-b:a', '192k'] : []),
    '-t', String(o.dureeS), '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', sortie,
  ];
}

/** Lit les cartons d'une demande (3 au plus, 80 caractères chacun). */
export function lireCartons(v: unknown): Carton[] {
  return (Array.isArray(v) ? v : [])
    .map((c: any) => ({ texte: String(c?.texte ?? '').trim().slice(0, 80), position: c?.position === 'debut' ? 'debut' as const : 'fin' as const }))
    .filter((c) => c.texte.length > 0)
    .slice(0, 3);
}
