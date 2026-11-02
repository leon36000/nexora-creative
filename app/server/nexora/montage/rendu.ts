/**
 * Rendu minimal d'un EditPlan v1 par ffmpeg (aucun moteur de rendu de montage n'existait côté serveur : filmMoteur.ts ne
 * fait que concaténer des plans). Coupes, fondus/dip/glisse (xfade), vitesse constante et rampes (par morceaux), zoom
 * lent, texte (ASS, posé EN DERNIER comme l'exige la recette), musique avec fondus, voix, ducking (sidechaincompress)
 * et normalisation loudnorm. Sans `drawtext` (absent de certains ffmpeg statiques) : le texte passe par libass.
 * Limites assumées de la v1 : le son propre des plans vidéo est ignoré (montage sur musique et voix off) ; loudnorm en une
 * passe (la mesure en deux passes viendra avec `mix_audio`) ; le ducking est approché (ratio dérivé de la profondeur).
 */
import { execFile } from 'node:child_process';
import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { couperLignes, texteAss } from '../cartons.js';
import { ffmpegParDefaut } from './analyse.js';
import { type EditPlan, lignedeTemps, validerEditPlan } from './editplan.js';

export const TAILLES: Record<EditPlan['format'], [number, number]> = { '16:9': [1280, 720], '9:16': [720, 1280], '1:1': [720, 720] };
const RAMPE_MORCEAUX = 6;

export interface OptionsRendu { apercu?: boolean; taille?: [number, number]; dossierPolices?: string }
export interface CommandeRendu { args: string[]; ass: string | null; dureeS: number }

const n = (x: number) => String(Math.round(x * 10000) / 10000);
const secs = (f: number, fps: number) => n(f / fps);
const tempsAss = (s: number) => `${Math.floor(s / 3600)}:${String(Math.floor((s % 3600) / 60)).padStart(2, '0')}:${(s % 60).toFixed(2).padStart(5, '0')}`;
const echap = (p: string) => p.replace(/\\/g, '/').replace(/:/g, '\\:').replace(/'/g, "\\'");

export function fichierAssTextes(plan: EditPlan, w: number, h: number): string {
  const lignes = [
    '[Script Info]', 'ScriptType: v4.00+', `PlayResX: ${w}`, `PlayResY: ${h}`, 'WrapStyle: 2', '',
    '[V4+ Styles]',
    'Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding',
    ...(['haut', 'centre', 'bas'] as const).map((pos) => `Style: ${pos},DejaVu Sans,${Math.round(h * 0.06)},&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,${Math.max(2, Math.round(h * 0.004))},1,${pos === 'haut' ? 8 : pos === 'centre' ? 5 : 2},${Math.round(w * 0.06)},${Math.round(w * 0.06)},${Math.round(h * 0.08)},1`),
    '', '[Events]', 'Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text',
  ];
  const maxCar = w < h ? 26 : 42;
  for (const t of plan.textes) {
    const taille = Math.round((h * t.taille_pct) / 100);
    const corps = t.texte.split('\n').flatMap((l) => couperLignes(l, maxCar)).map(texteAss).join('\\N');
    lignes.push(`Dialogue: 0,${tempsAss(t.debut_f / plan.fps)},${tempsAss((t.debut_f + t.duree_f) / plan.fps)},${t.position},,0,0,0,,{\\fad(150,150)\\fs${taille}}${corps}`);
  }
  return lignes.join('\n') + '\n';
}

/** Construit la commande ffmpeg d'un plan VALIDE ; `chemin` résout un identifiant de source en fichier. */
export function commandeRendu(plan: EditPlan, chemin: (src: string) => string, sortie: string, o: OptionsRendu = {}, fichierAss = 'textes.ass'): CommandeRendu {
  const fps = plan.fps;
  const [W, H] = o.taille ?? (() => { const [w, h] = TAILLES[plan.format]; return o.apercu ? [Math.round(w / 2 / 2) * 2, Math.round(h / 2 / 2) * 2] as [number, number] : [w, h] as [number, number]; })();
  const { fins, total } = lignedeTemps(plan);
  const dureeS = total / fps;
  const entrees: string[] = [];
  const index = new Map<string, number>();
  const entree = (src: string) => {
    if (!index.has(src)) {
      index.set(src, entrees.length);
      entrees.push(src);
    }
    return index.get(src)!;
  };
  const args: string[] = ['-y', '-v', 'error'];
  const filtres: string[] = [];
  // Ordre des entrées : vidéos, puis musique, puis voix.
  for (const c of plan.video) entree(c.src);
  if (plan.audio.musique) entree(plan.audio.musique.src);
  for (const v of plan.audio.voix) entree(v.src);
  for (const src of entrees) {
    if (plan.sources[src]?.kind === 'image') args.push('-loop', '1', '-framerate', String(fps), '-t', '600');
    args.push('-i', chemin(src));
  }

  const base = `fps=${fps},scale=${W}:${H}:force_original_aspect_ratio=increase,crop=${W}:${H},setsar=1,format=yuv420p`;
  plan.video.forEach((c, i) => {
    const k = index.get(c.src)!;
    const dureeClip = c.duree_f / fps;
    const zoom = c.zoom && c.zoom.a !== c.zoom.de ? `,scale=w='trunc(iw*(${n(c.zoom.de)}+(${n(c.zoom.a - c.zoom.de)})*t/${n(dureeClip)})/2)*2':h='trunc(ih*(${n(c.zoom.de)}+(${n(c.zoom.a - c.zoom.de)})*t/${n(dureeClip)})/2)*2':eval=frame,crop=${W}:${H},setsar=1` : '';
    if (c.rampe) {
      const morceaux: string[] = [];
      let lu = c.entree_f, restant = c.duree_f;
      for (let m = 0; m < RAMPE_MORCEAUX; m++) {
        const sortieF = m === RAMPE_MORCEAUX - 1 ? restant : Math.max(1, Math.round(c.duree_f / RAMPE_MORCEAUX));
        const v = c.rampe.de + ((c.rampe.a - c.rampe.de) * (m + 0.5)) / RAMPE_MORCEAUX;
        const conso = Math.max(1, Math.round(sortieF * v));
        filtres.push(`[${k}:v]trim=start=${secs(lu, fps)}:duration=${secs(conso, fps)},setpts=(PTS-STARTPTS)/${n(v)},${base}[r${i}_${m}]`);
        morceaux.push(`[r${i}_${m}]`);
        lu += conso; restant -= sortieF;
      }
      filtres.push(`${morceaux.join('')}concat=n=${RAMPE_MORCEAUX}:v=1:a=0,setpts=PTS-STARTPTS${zoom},trim=duration=${n(dureeClip)}[c${i}]`);
    } else {
      const conso = Math.max(1, Math.round(c.duree_f * c.vitesse));
      filtres.push(`[${k}:v]trim=start=${secs(c.entree_f, fps)}:duration=${secs(conso, fps)},setpts=(PTS-STARTPTS)/${n(c.vitesse)},${base}${zoom},trim=duration=${n(dureeClip)},setpts=PTS-STARTPTS[c${i}]`);
    }
  });
  // Assemblage : coupe = concat, transitions = xfade au bon décalage.
  let acc = 'c0';
  plan.video.forEach((c, i) => {
    if (i === 0) return;
    const t = c.transition_in;
    const nom = `a${i}`;
    if (t.type === 'cut') filtres.push(`[${acc}][c${i}]concat=n=2:v=1:a=0,setpts=PTS-STARTPTS[${nom}]`);
    else {
      const typeX = { fondu: 'fade', dip: 'fadeblack', glisse: 'slideleft' }[t.type];
      filtres.push(`[${acc}]settb=AVTB,fps=${fps}[${nom}x];[c${i}]settb=AVTB,fps=${fps}[${nom}y];[${nom}x][${nom}y]xfade=transition=${typeX}:duration=${secs(t.duree_f, fps)}:offset=${secs(fins[i - 1] - t.duree_f, fps)},setpts=PTS-STARTPTS[${nom}]`);
    }
    acc = nom;
  });
  let sortieVideo = acc;
  let ass: string | null = null;
  if (plan.textes.length) {
    ass = fichierAssTextes(plan, W, H);
    filtres.push(`[${acc}]ass='${echap(fichierAss)}'${o.dossierPolices ? `:fontsdir='${echap(o.dossierPolices)}'` : ''}[vt]`);
    sortieVideo = 'vt';
  }
  filtres.push(`[${sortieVideo}]trim=duration=${n(dureeS)},setpts=PTS-STARTPTS,format=yuv420p[vout]`);

  // Audio : musique + voix (ducking), puis loudnorm.
  const a = plan.audio;
  const pistes: string[] = [];
  if (a.musique) {
    const m = a.musique;
    const kd = index.get(m.src)!;
    const jouee = (m.duree_f ?? total) / fps;
    const fin = Math.max(0, jouee - m.fondu_out_f / fps);
    filtres.push(`[${kd}:a]atrim=start=${secs(m.entree_f, fps)}:duration=${n(jouee)},asetpts=PTS-STARTPTS,volume=${n(m.gain_db)}dB${m.fondu_in_f ? `,afade=t=in:d=${secs(m.fondu_in_f, fps)}` : ''}${m.fondu_out_f ? `,afade=t=out:st=${n(fin)}:d=${secs(m.fondu_out_f, fps)}` : ''},apad,atrim=duration=${n(dureeS)}[mus]`);
    pistes.push('mus');
  }
  const voixNoms: string[] = [];
  a.voix.forEach((v, i) => {
    const kd = index.get(v.src)!;
    filtres.push(`[${kd}:a]atrim=start=${secs(v.entree_f, fps)}:duration=${secs(v.duree_f, fps)},asetpts=PTS-STARTPTS,volume=${n(v.gain_db)}dB,adelay=${Math.round((v.debut_f / fps) * 1000)}:all=1,apad,atrim=duration=${n(dureeS)}[vx${i}]`);
    voixNoms.push(`vx${i}`);
  });
  let audioFinal: string | null = null;
  if (voixNoms.length) {
    filtres.push(voixNoms.length > 1 ? `${voixNoms.map((x) => `[${x}]`).join('')}amix=inputs=${voixNoms.length}:normalize=0[voix]` : `[${voixNoms[0]}]anull[voix]`);
    if (a.musique && a.ducking.actif) {
      // La profondeur voulue (dB) fixe le rapport de compression : ratio ≈ 1 + profondeur/2, seuil bas pour que la voix déclenche toujours.
      const ratio = Math.min(20, 1 + a.ducking.profondeur_db / 2);
      filtres.push(`[voix]asplit=2[vsc][vmix];[mus][vsc]sidechaincompress=threshold=0.02:ratio=${n(ratio)}:attack=20:release=400:makeup=1[duck];[duck][vmix]amix=inputs=2:normalize=0[mix]`);
      audioFinal = 'mix';
    } else if (a.musique) {
      filtres.push('[mus][voix]amix=inputs=2:normalize=0[mix]');
      audioFinal = 'mix';
    } else audioFinal = 'voix';
  } else if (a.musique) audioFinal = 'mus';
  if (audioFinal) {
    filtres.push(`[${audioFinal}]loudnorm=I=${n(a.cible_lufs)}:TP=${n(a.crete_db)}:LRA=11,aresample=48000,atrim=duration=${n(dureeS)}[aout]`);
  }
  args.push('-filter_complex', filtres.join(';'), '-map', '[vout]');
  if (audioFinal) args.push('-map', '[aout]', '-c:a', 'aac', '-b:a', o.apercu ? '128k' : '192k');
  else args.push('-an');
  args.push('-c:v', 'libx264', '-preset', o.apercu ? 'veryfast' : 'medium', '-crf', o.apercu ? '28' : '19', '-pix_fmt', 'yuv420p', '-r', String(fps), '-t', n(dureeS), '-movflags', '+faststart', sortie);
  return { args, ass, dureeS };
}

/** Valide puis rend. Un plan invalide n'est jamais rendu (renvoie les violations). */
export async function rendreEditPlan(brut: unknown, chemin: (src: string) => string, sortie: string, o: OptionsRendu & { ffmpeg?: string; ctx?: Parameters<typeof validerEditPlan>[1] } = {}): Promise<{ ok: true; sortie: string; dureeS: number } | { ok: false; erreurs: string[] }> {
  const v = validerEditPlan(brut, o.ctx);
  if (!v.ok || !v.plan) return { ok: false, erreurs: v.erreurs.map((e) => `[${e.regle}] ${e.chemin} : ${e.message}`) };
  mkdirSync(dirname(sortie), { recursive: true });
  const fichierAss = join(dirname(sortie), `${sortie.split('/').pop()}.ass`);
  const cmd = commandeRendu(v.plan, chemin, sortie, o, fichierAss);
  if (cmd.ass) writeFileSync(fichierAss, cmd.ass);
  await new Promise<void>((ok, ko) => execFile(o.ffmpeg ?? ffmpegParDefaut(), cmd.args, { maxBuffer: 1 << 26, timeout: 900_000 }, (e, _o, err) => (e ? ko(new Error(`ffmpeg : ${String(err).split('\n').filter(Boolean).slice(-14).join(' ')}`)) : ok())));
  return { ok: true, sortie, dureeS: cmd.dureeS };
}
