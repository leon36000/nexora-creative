/**
 * Source slot for the continue tools (Extend, Transition, Speak, Add sound):
 * pick one of your takes, or drop a file. Either way the media is uploaded as
 * an input and comes back as a token plus the facts the page sizes itself by.
 */
import { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { mediaUrl, posterUrl, takeAsInput, uploadFile, type Take } from './api';
import { useDropZone } from './drop';
import { DropWell } from './pages/Mirror';
import { isImage, isModel, settingsOf, toast, useStore } from './store';
import { Icon } from './ui';
import type { LangueClient } from '../shared/creationLanguage';

export type SourceKind = 'video' | 'image' | 'audio';

type CopieChargement = { invalid: (accept: SourceKind[]) => string; tooLarge: string; uploadFailed: string };
type CopieSource = {
  loading: string;
  remove: string;
  takes: string;
  useTake: (id: number) => string;
  takeFailure: string;
};

const COPIES_CHARGEMENT: Record<LangueClient, CopieChargement> = {
  fr: {
    invalid: (accept) => `Dépose un fichier ${accept.join(' ou ')}.`,
    tooLarge: 'Ce fichier dépasse 45 Mo. Réduis sa taille, puis réessaie.',
    uploadFailed: 'Impossible de charger ce fichier. Réessaie.',
  },
  en: {
    invalid: (accept) => `Drop ${accept.join(' or ')}`,
    tooLarge: 'That file is over 45 MB. Trim it first.',
    uploadFailed: 'Could not upload this file. Try again.',
  },
};

const COPIES_SOURCE: Record<LangueClient, CopieSource> = {
  fr: { loading: 'Chargement…', remove: 'Retirer la source', takes: 'Tes prises', useTake: (id) => `Utiliser la prise ${id}`, takeFailure: 'Impossible de charger cette prise. Réessaie.' },
  en: { loading: 'Loading...', remove: 'Remove source', takes: 'Your takes', useTake: (id) => `Use take ${id}`, takeFailure: 'Could not load this take. Try again.' },
};

const COPIES_SOURCE_HISTORIQUE: CopieSource = {
  loading: 'Loading...', remove: 'remove', takes: 'your takes', useTake: (id) => `Use take ${id}`, takeFailure: 'Could not load this take. Try again.',
};

function copieChargement(langue?: LangueClient): CopieChargement {
  if (langue === 'fr') return COPIES_CHARGEMENT.fr;
  return COPIES_CHARGEMENT.en;
}

function copieSource(langue?: LangueClient): CopieSource {
  if (langue === 'fr') return COPIES_SOURCE.fr;
  if (langue === 'en') return COPIES_SOURCE.en;
  return COPIES_SOURCE_HISTORIQUE;
}

function messageEchec(langue: LangueClient | undefined, erreur: unknown, copieLocalisee: string, repli: string): string {
  if (langue) return copieLocalisee;
  if (erreur instanceof Error) return erreur.message;
  return repli;
}

export interface Source {
  token: string;
  kind: SourceKind;
  /** Preview URL: the take's media or a blob of the dropped file. */
  url: string;
  name: string;
  w: number;
  h: number;
  seconds: number;
  takeId?: number;
  /** The take's own prompt, used when the user leaves theirs empty. */
  prompt?: string;
}

/** Duration and frame size of a media URL, from the browser's own decoder. */
export function measure(url: string, kind: SourceKind): Promise<{ w: number; h: number; seconds: number }> {
  return new Promise((res) => {
    if (kind === 'image') {
      const img = new Image();
      img.onload = () => res({ w: img.naturalWidth, h: img.naturalHeight, seconds: 0 });
      img.onerror = () => res({ w: 0, h: 0, seconds: 0 });
      img.src = url;
      return;
    }
    const el = document.createElement(kind === 'audio' ? 'audio' : 'video');
    el.preload = 'metadata';
    el.muted = true;
    el.onloadedmetadata = () => res({ w: (el as HTMLVideoElement).videoWidth || 0, h: (el as HTMLVideoElement).videoHeight || 0, seconds: el.duration || 0 });
    el.onerror = () => res({ w: 0, h: 0, seconds: 0 });
    el.src = url;
  });
}

/** A finished take as a source. */
export async function sourceFromTake(t: Take): Promise<Source> {
  const kind: SourceKind = isImage(t) ? 'image' : 'video';
  const url = mediaUrl(t.id);
  const [token, m] = await Promise.all([takeAsInput(t.id, kind === 'image' ? `take_${t.id}.png` : `take_${t.id}.mp4`), measure(url, kind)]);
  const s = settingsOf(t);
  return { token, kind, url, name: `take ${t.id}`, ...m, takeId: t.id, prompt: s.userPrompt || s.prompt };
}

export async function sourceFromFile(f: File, kind: SourceKind): Promise<Source> {
  const url = URL.createObjectURL(f);
  const [token, m] = await Promise.all([uploadFile(f), measure(url, kind)]);
  return { token, kind, url, name: f.name.replace(/\.[^.]+$/, ''), ...m };
}

const EXT_KIND: Record<string, SourceKind> = {
  mp4: 'video', mov: 'video', webm: 'video', m4v: 'video', mkv: 'video',
  png: 'image', jpg: 'image', jpeg: 'image', webp: 'image',
  wav: 'audio', mp3: 'audio', m4a: 'audio', flac: 'audio', ogg: 'audio', aac: 'audio',
};

/** What a file is, by its MIME type, or by its extension when the browser gives none. */
export function fileKind(f: File): SourceKind | null {
  const byType = (['video', 'image', 'audio'] as SourceKind[]).find((k) => f.type.startsWith(`${k}/`));
  return byType ?? EXT_KIND[f.name.split('.').pop()?.toLowerCase() ?? ''] ?? null;
}

/** Upload a dropped or picked file as a source, if it is one of `accept`. Toasts and returns null otherwise. */
export async function loadFile(f: File, accept: SourceKind[], langue?: LangueClient): Promise<Source | null> {
  const copy = copieChargement(langue);
  const kind = fileKind(f);
  if (!kind || !accept.includes(kind)) { toast(copy.invalid(accept), true); return null; }
  if (f.size > 45e6) { toast(copy.tooLarge, true); return null; }
  try { return await sourceFromFile(f, kind); } catch (e) { toast(messageEchec(langue, e, copy.uploadFailed, 'upload failed'), true); return null; }
}

/** Load ?take=<id> once into a source, then drop the param. */
export function useTakeParam(id: string | null, onSource: (s: Source) => void, errorMessage?: string) {
  const takes = useStore((s) => s.takes);
  const [loaded, setLoaded] = useState<{ id: string; generation: number } | null>(null);
  const generation = useRef(0);
  const latest = useRef({ onSource, errorMessage });
  useLayoutEffect(() => { latest.current = { onSource, errorMessage }; }, [onSource, errorMessage]);
  useLayoutEffect(() => {
    generation.current++;
    return () => { generation.current++; };
  }, [id]);
  useEffect(() => {
    if (!id) { if (loaded) setLoaded(null); return; }
    if (id === loaded?.id && generation.current === loaded.generation) return;
    const t = takes.find((x) => x.id === Number(id));
    if (!t) return;
    setLoaded({ id, generation: generation.current });
    const current = generation.current;
    void sourceFromTake(t).then((source) => {
      if (generation.current === current) latest.current.onSource(source);
    }).catch((e) => {
      if (generation.current === current) toast(latest.current.errorMessage ?? (e instanceof Error ? e.message : 'could not load the take'), true);
    });
  }, [id, takes, loaded, errorMessage]);
}

/**
 * One source slot. Empty: a drop well plus a strip of recent takes that fit.
 * Filled: the preview with a remove button.
 */
export function SourceSlot(p: {
  label: string;
  value: Source | null;
  onChange: (s: Source | null) => void;
  accept: SourceKind[];
  title: string;
  sub: string;
  langue?: LangueClient;
}) {
  const [busy, setBusy] = useState(false);
  const takes = useStore((s) => s.takes.filter((t) => t.status === 'done' && t.output_path && !isModel(t) && (p.accept.includes(isImage(t) ? 'image' : 'video'))).slice(0, 8));
  const v = p.value;
  const copy = copieSource(p.langue);

  const take = async (t: Take) => {
    setBusy(true);
    try { p.onChange(await sourceFromTake(t)); } catch (e) { toast(messageEchec(p.langue, e, copy.takeFailure, 'failed'), true); } finally { setBusy(false); }
  };
  const file = async (f: File) => {
    setBusy(true);
    try { const src = await loadFile(f, p.accept, p.langue); if (src) p.onChange(src); } finally { setBusy(false); }
  };
  // A filled slot takes a drop too: it replaces what is there.
  const replace = useDropZone((files) => void file(files[0]));

  return (
    <div className="rail-section">
      <div className="label">{p.label}</div>
      {v ? (
        v.kind === 'audio' ? (
          <div className={`ref ${replace.over ? 'drag' : ''}`} {...replace.props} style={{ aspectRatio: 'auto', padding: '12px 12px 12px 14px', display: 'flex', alignItems: 'center', gap: 10 }}>
            <Icon name="audio" />
            <div style={{ minWidth: 0, flex: 1 }}>
              <div style={{ fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{v.name}</div>
              <div className="dim mono" style={{ fontSize: 11.5 }}>{v.seconds.toFixed(1)}s</div>
            </div>
            <button type="button" className="x" style={{ position: 'static' }} onClick={() => p.onChange(null)} aria-label={copy.remove}><Icon name="x" size={12} /></button>
          </div>
        ) : (
          <div className={`ref ${replace.over ? 'drag' : ''}`} {...replace.props} style={{ aspectRatio: `${v.w || 16} / ${v.h || 9}` }}>
            {v.kind === 'image' ? <img src={v.url} alt="" /> : <video src={v.url} muted loop autoPlay playsInline />}
            <span className="role">{v.kind === 'image' ? v.name : `${v.seconds.toFixed(1)}s · ${v.name}`}</span>
            <button type="button" className="x" onClick={() => p.onChange(null)} aria-label={copy.remove}><Icon name="x" size={12} /></button>
          </div>
        )
      ) : (
        <>
          <DropWell accept={p.accept.map((k) => `${k}/*`).join(',')} onFile={(f) => void file(f)} icon={p.accept[0]} title={busy ? copy.loading : p.title} sub={p.sub} />
          {takes.length > 0 && !p.accept.every((k) => k === 'audio') && (
            <div className="src-strip" aria-label={copy.takes}>
              {takes.map((t) => (
                <button key={t.id} type="button" title={copy.useTake(t.id)} disabled={busy} onClick={() => void take(t)}>
                  <img src={posterUrl(t.id)} alt="" loading="lazy" />
                  {!isImage(t) && <span><Icon name="video" size={11} /></span>}
                </button>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

