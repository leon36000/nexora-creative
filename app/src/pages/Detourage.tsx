/**
 * Détourage vidéo pro : importer une vidéo, cliquer le sujet (clics positifs et négatifs, sur plusieurs images),
 * voir le masque en direct, choisir fond et exports, lancer un travail asynchrone (progression, annulation, reprise),
 * puis prévisualiser (damier, matte, nouveau fond) et télécharger (PNG 16 bits, EXR, ProRes 4444, WebM alpha).
 * Rapport et mesures : recherche/22-detourage-video-pro.md.
 */
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { toast } from '../store';

const P = '/api/nexora/detourage';
type Pt = [number, number, 0 | 1];
interface Travail {
  id: string; nom: string; etat: string; etape: string; progression: number; message: string;
  source: { largeur: number; hauteur: number; fps: number; duree: number } | null;
  devis: { secondes: number; credits: number | null } | null;
  mesures: any; sorties: { fichiers?: Record<string, number>; sequences?: Record<string, number> } | null;
}
interface Capacites { rapide: { disponible: boolean; moteur: { nom: string } | null }; pro: { disponible: boolean; description: string }; limites: { secondesMax: number } }

async function appel<T>(chemin: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`${P}${chemin}`, init);
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error((j as { error?: string }).error ?? `Erreur ${r.status}`);
  return j as T;
}

/** Envoi d'un fichier en flux avec progression (XHR : fetch n'expose pas la progression d'envoi). */
function envoyer(url: string, fichier: Blob, progression: (p: number) => void): Promise<any> {
  return new Promise((res, rej) => {
    const x = new XMLHttpRequest();
    x.open('PUT', url);
    x.upload.onprogress = (e) => e.lengthComputable && progression(e.loaded / e.total);
    x.onload = () => { try { const j = JSON.parse(x.responseText); x.status < 300 ? res(j) : rej(new Error(j.error ?? `Erreur ${x.status}`)); } catch { rej(new Error(`Erreur ${x.status}`)); } };
    x.onerror = () => rej(new Error('Envoi interrompu'));
    x.setRequestHeader('content-type', 'application/octet-stream');
    x.send(fichier);
  });
}

const dateurMasque = (b64: string) => `data:image/png;base64,${b64}`;
const fmtS = (s: number) => (s < 90 ? `${Math.round(s)} s` : `${Math.floor(s / 60)} min ${Math.round(s % 60)} s`);
const fmtO = (o: number) => (o > 1e9 ? `${(o / 1e9).toFixed(2)} Go` : o > 1e6 ? `${(o / 1e6).toFixed(1)} Mo` : `${Math.round(o / 1e3)} Ko`);

export default function Detourage() {
  const [cap, setCap] = useState<Capacites | null>(null);
  const [travail, setTravail] = useState<Travail | null>(null);
  const [recents, setRecents] = useState<Travail[]>([]);
  const [urlLocale, setUrlLocale] = useState<string | null>(null);
  const [envoi, setEnvoi] = useState<number | null>(null);
  const [duree, setDuree] = useState(0);
  const [fps, setFps] = useState(24);
  const [t, setT] = useState(0); // position (secondes)
  const [clics, setClics] = useState<Record<number, Pt[]>>({}); // image -> points
  const [outil, setOutil] = useState<'ajouter' | 'retirer'>('ajouter');
  const [masque, setMasque] = useState<{ image: number; src: string; aire: number; s: number } | null>(null);
  const [occupe, setOccupe] = useState<string | null>(null);
  const [mode, setMode] = useState<'suivi' | 'complet'>('complet');
  const [palier, setPalier] = useState<'rapide' | 'pro'>('rapide');
  const [largeur, setLargeur] = useState(1280);
  const [plage, setPlage] = useState<[number, number] | null>(null);
  const [fond, setFond] = useState<'transparent' | 'couleur' | 'flou' | 'image'>('transparent');
  const [couleur, setCouleur] = useState('#1aa36f');
  const [fichierFond, setFichierFond] = useState<string | null>(null);
  const [lissage, setLissage] = useState(1);
  const [vue, setVue] = useState<'apercu-echecs.mp4' | 'matte.mp4' | 'composite.mp4' | 'suivi.mp4'>('apercu-echecs.mp4');
  const video = useRef<HTMLVideoElement>(null);
  const jeton = useRef(0);

  useEffect(() => { void appel<Capacites>('/capacites').then(setCap).catch(() => setCap(null)); void appel<Travail[]>('/travaux').then(setRecents).catch(() => {}); }, []);

  const image = Math.round(t * fps);
  const points = clics[image] ?? [];

  // Suivi de l'avancement d'un travail en cours
  useEffect(() => {
    if (!travail || !['en_attente', 'en_cours'].includes(travail.etat)) return;
    const h = setInterval(() => { void appel<Travail>(`/travaux/${travail.id}`).then(setTravail).catch(() => {}); }, 1500);
    return () => clearInterval(h);
  }, [travail?.id, travail?.etat]);

  async function importer(f: File) {
    try {
      setOccupe('Création du travail…');
      const nouveau = await appel<Travail>('/travaux', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ nom: f.name.replace(/\.[^.]+$/, '') }) });
      setUrlLocale(URL.createObjectURL(f));
      setClics({}); setMasque(null); setPlage(null); setT(0);
      setEnvoi(0);
      const r = await envoyer(`${P}/travaux/${nouveau.id}/source`, f, setEnvoi);
      setTravail(r); setEnvoi(null);
      if (r.source) setFps(r.source.fps);
      if (r.avertissement) toast(r.avertissement, true);
    } catch (e) { toast(e instanceof Error ? e.message : 'import impossible', true); setEnvoi(null); } finally { setOccupe(null); }
  }

  /** Image courante de la vidéo, réduite à 1280 px de large, en JPEG (base 64). */
  const capturer = useCallback((): string | null => {
    const v = video.current; if (!v || !v.videoWidth) return null;
    const k = Math.min(1, 1280 / v.videoWidth);
    const c = document.createElement('canvas'); c.width = Math.round(v.videoWidth * k); c.height = Math.round(v.videoHeight * k);
    c.getContext('2d')!.drawImage(v, 0, 0, c.width, c.height);
    return c.toDataURL('image/jpeg', 0.92).split(',')[1];
  }, []);

  const calculer = useCallback(async (pts: Pt[]) => {
    const b64 = capturer(); if (!b64 || !pts.length) { setMasque(null); return; }
    const mon = ++jeton.current;
    try {
      const r = await appel<{ masqueB64: string; aire: number; secondes: number }>('/apercu', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ imageB64: b64, points: pts }) });
      if (mon === jeton.current) setMasque({ image: Math.round((video.current?.currentTime ?? 0) * fps), src: dateurMasque(r.masqueB64), aire: r.aire, s: r.secondes });
    } catch (e) { if (mon === jeton.current) toast(e instanceof Error ? e.message : 'aperçu impossible', true); }
  }, [capturer, fps]);

  function cliquer(e: React.MouseEvent<HTMLDivElement>, negatifForce = false) {
    if (!travail || envoi !== null) return;
    const r = e.currentTarget.getBoundingClientRect();
    const x = (e.clientX - r.left) / r.width, y = (e.clientY - r.top) / r.height;
    const negatif = negatifForce || outil === 'retirer' || e.shiftKey || e.altKey;
    const pts: Pt[] = [...points, [Math.min(1, Math.max(0, x)), Math.min(1, Math.max(0, y)), negatif ? 0 : 1]];
    setClics({ ...clics, [image]: pts });
    video.current?.pause();
    void calculer(pts);
  }
  function annulerClic() { const pts = points.slice(0, -1); setClics({ ...clics, [image]: pts }); void calculer(pts); }
  function effacer() { const c = { ...clics }; delete c[image]; setClics(c); setMasque(null); }
  useEffect(() => { setMasque(null); if (points.length) void calculer(points); /* image changée : recalcul */ // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [image]);

  const nbClics = useMemo(() => Object.values(clics).reduce((n, p) => n + p.length, 0), [clics]);
  const debut = plage?.[0] ?? 0;
  const imagesCles = Object.keys(clics).map(Number).filter((i) => (clics[i]?.length ?? 0) > 0);

  async function deposerFond(f: File) {
    if (!travail) return;
    try {
      const ext = (f.name.split('.').pop() ?? 'png').toLowerCase();
      const r = await envoyer(`${P}/travaux/${travail.id}/fond?ext=${ext}`, f, () => {});
      setFichierFond(r.fond); setFond('image'); toast('Fond déposé');
    } catch (e) { toast(e instanceof Error ? e.message : 'fond impossible', true); }
  }

  async function lancer() {
    if (!travail) return;
    const invites = imagesCles.filter((i) => i >= Math.round(debut * fps)).map((i) => ({ image: i - Math.round(debut * fps), points: clics[i] }));
    if (!invites.length) { toast('Clique d’abord sur le sujet (dans la plage choisie)', true); return; }
    const composite = fond === 'couleur' ? { type: 'couleur', valeur: couleur } : fond === 'flou' ? { type: 'flou' } : fond === 'image' && fichierFond ? { type: /\.(mp4|mov|webm)$/.test(fichierFond) ? 'video' : 'image', fichier: fichierFond } : null;
    try {
      setOccupe('Lancement…');
      setTravail(await appel<Travail>(`/travaux/${travail.id}/lancer`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({
        palier, mode, invites, debutS: debut, dureeS: plage ? plage[1] - plage[0] : null, largeurMax: largeur, lissage, composite,
      }) }));
    } catch (e) { toast(e instanceof Error ? e.message : 'lancement impossible', true); } finally { setOccupe(null); }
  }
  async function action(a: 'annuler' | 'reprendre') { if (travail) setTravail(await appel<Travail>(`/travaux/${travail.id}/${a}`, { method: 'POST' }).catch((e) => { toast(e.message, true); return travail; })); }
  async function supprimer() {
    if (!travail || !confirm('Supprimer ce détourage et tous ses fichiers temporaires ?')) return;
    await appel(`/travaux/${travail.id}`, { method: 'DELETE' }).catch((e) => toast(e.message, true));
    setTravail(null); setUrlLocale(null); setClics({}); setMasque(null); void appel<Travail[]>('/travaux').then(setRecents);
  }

  const fini = travail?.etat === 'termine';
  const enCours = travail && ['en_attente', 'en_cours'].includes(travail.etat);
  const fich = travail?.sorties?.fichiers ?? {};
  const seq = travail?.sorties?.sequences ?? {};
  const m = travail?.mesures;
  const lien = (nom: string) => `${P}/travaux/${travail!.id}/sorties/${nom}`;
  const vues = [['apercu-echecs.mp4', 'Damier'], ['matte.mp4', 'Matte'], ['composite.mp4', 'Nouveau fond'], ['suivi.mp4', 'Suivi']].filter(([n]) => fich[n]) as [typeof vue, string][];

  return (
    <div className="rail-layout" style={{ gridTemplateColumns: '380px 1fr' }}>
      <aside className="rail">
        <div className="display" style={{ fontSize: 26 }}>Détourage pro</div>
        <div className="dim" style={{ fontSize: 12.5, marginTop: -4 }}>Isole une personne, un animal ou un objet dans une vidéo : cheveux, fourrure, bords nets, sans scintillement. Sortie alpha 16 bits et EXR.</div>

        {cap && !cap.rapide.disponible && <div className="rail-section" style={{ color: 'var(--bad)', fontSize: 12.5 }}>Aucun moteur de détourage en ligne. Lance le serveur de détourage sur la machine GPU (outils/detourage).</div>}

        <div className="rail-section">
          <div className="label">1 · Vidéo</div>
          <input type="file" accept="video/*" onChange={(e) => e.target.files?.[0] && importer(e.target.files[0])} disabled={!cap?.rapide.disponible || !!enCours} />
          {envoi !== null && <progress value={envoi} max={1} style={{ width: '100%' }} />}
          {travail?.source && <div className="dim" style={{ fontSize: 12 }}>{travail.source.largeur}×{travail.source.hauteur} · {travail.source.fps.toFixed(2)} i/s · {fmtS(travail.source.duree)}{travail.source.duree > (cap?.limites.secondesMax ?? 120) ? ` (limite ${cap?.limites.secondesMax} s par travail : choisis une plage)` : ''}</div>}
        </div>

        <div className="rail-section">
          <div className="label">2 · Sujet {nbClics ? `(${nbClics} clic${nbClics > 1 ? 's' : ''}, ${imagesCles.length} image${imagesCles.length > 1 ? 's' : ''})` : ''}</div>
          <div className="seg"><button className={outil === 'ajouter' ? 'on' : ''} onClick={() => setOutil('ajouter')}>+ Ajouter</button><button className={outil === 'retirer' ? 'on' : ''} onClick={() => setOutil('retirer')}>− Retirer</button></div>
          <div className="dim" style={{ fontSize: 12 }}>Clique le sujet ; Maj ou Alt + clic retire. Change d’image et ajoute un clic quand le sujet change de forme, passe derrière un objet ou ressort.</div>
          <div style={{ display: 'flex', gap: 6 }}><button className="btn sm" onClick={annulerClic} disabled={!points.length}>Annuler le dernier</button><button className="btn sm" onClick={effacer} disabled={!points.length}>Effacer cette image</button></div>
          {duree > 0 && <>
            <div className="label" style={{ marginTop: 6 }}>Plage traitée</div>
            <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
              <button className="btn sm" onClick={() => setPlage([t, plage?.[1] ?? duree])}>Début ici</button>
              <button className="btn sm" onClick={() => setPlage([plage?.[0] ?? 0, Math.max(t, (plage?.[0] ?? 0) + 0.5)])}>Fin ici</button>
              <span className="dim" style={{ fontSize: 12 }}>{plage ? `${plage[0].toFixed(1)} → ${plage[1].toFixed(1)} s` : 'toute la vidéo'}</span>
            </div></>}
        </div>

        <div className="rail-section">
          <div className="label">3 · Qualité</div>
          <div className="seg"><button className={palier === 'rapide' ? 'on' : ''} onClick={() => setPalier('rapide')}>Rapide</button>
            <button className={palier === 'pro' ? 'on' : ''} disabled title={cap?.pro.description} style={{ opacity: 0.45 }}>Pro (bientôt)</button></div>
          <div className="seg"><button className={mode === 'suivi' ? 'on' : ''} onClick={() => setMode('suivi')}>Aperçu du suivi</button><button className={mode === 'complet' ? 'on' : ''} onClick={() => setMode('complet')}>Détourage complet</button></div>
          <label className="dim" style={{ fontSize: 12 }}>Largeur max : {largeur} px
            <input type="range" min={640} max={3840} step={160} value={largeur} onChange={(e) => setLargeur(Number(e.target.value))} style={{ width: '100%' }} /></label>
          <label className="dim" style={{ fontSize: 12 }}>Stabilisation des bords : {lissage.toFixed(1)}
            <input type="range" min={0} max={1.5} step={0.1} value={lissage} onChange={(e) => setLissage(Number(e.target.value))} style={{ width: '100%' }} /></label>
        </div>

        <div className="rail-section">
          <div className="label">4 · Fond</div>
          <div className="seg">{(['transparent', 'couleur', 'flou', 'image'] as const).map((f) => <button key={f} className={fond === f ? 'on' : ''} onClick={() => setFond(f)}>{f === 'transparent' ? 'Aucun' : f === 'couleur' ? 'Couleur' : f === 'flou' ? 'Flou' : 'Image'}</button>)}</div>
          {fond === 'couleur' && <input type="color" value={couleur} onChange={(e) => setCouleur(e.target.value)} />}
          {fond === 'image' && <><input type="file" accept="image/*,video/*" onChange={(e) => e.target.files?.[0] && deposerFond(e.target.files[0])} />{fichierFond && <span className="dim" style={{ fontSize: 12 }}>fond déposé</span>}</>}
          <div className="dim" style={{ fontSize: 12 }}>La transparence est toujours exportée (PNG 16 bits, EXR, ProRes 4444, WebM) ; le fond ajoute une vidéo composée.</div>
        </div>

        <div className="rail-section">
          {enCours
            ? <><progress value={travail!.progression} max={1} style={{ width: '100%' }} /><div className="dim" style={{ fontSize: 12.5 }}>{travail!.message || travail!.etape} · {Math.round(travail!.progression * 100)} %</div><button className="btn sm" onClick={() => action('annuler')}>Annuler</button></>
            : <button className="btn sm accent" onClick={lancer} disabled={!travail || !nbClics || !!occupe || envoi !== null}>{occupe ?? (mode === 'suivi' ? 'Lancer l’aperçu du suivi' : 'Lancer le détourage')}</button>}
          {travail && ['interrompu', 'erreur', 'annule'].includes(travail.etat) && <><div style={{ color: 'var(--bad)', fontSize: 12.5 }}>{travail.message}</div><button className="btn sm" onClick={() => action('reprendre')}>Reprendre (le calcul déjà fait est conservé)</button></>}
          {travail && !enCours && <button className="btn sm" onClick={supprimer}>Supprimer le travail et ses fichiers</button>}
        </div>
        {recents.length > 0 && !travail && <div className="rail-section"><div className="label">Travaux récents</div>{recents.slice(0, 6).map((r) => <div key={r.id} className="dim" style={{ fontSize: 12 }}>{r.nom} · {r.etat}</div>)}</div>}
      </aside>

      <main style={{ display: 'flex', flexDirection: 'column', gap: 10, minWidth: 0, overflow: 'auto' }}>
        {!urlLocale && <div className="dim" style={{ padding: 40, textAlign: 'center' }}>Importe une vidéo pour commencer.</div>}
        {urlLocale && !fini && (
          <>
            <div style={{ position: 'relative', alignSelf: 'center', maxWidth: '100%', cursor: 'crosshair' }} onClick={cliquer} onContextMenu={(e) => { e.preventDefault(); cliquer(e, true); }}>
              <video ref={video} src={urlLocale} muted playsInline style={{ maxWidth: '100%', maxHeight: '62vh', display: 'block' }}
                onLoadedMetadata={(e) => setDuree((e.target as HTMLVideoElement).duration)} onTimeUpdate={(e) => setT((e.target as HTMLVideoElement).currentTime)} />
              {masque && masque.image === image && <div aria-hidden style={{ position: 'absolute', inset: 0, background: '#ff3b5c', opacity: 0.5, pointerEvents: 'none', maskImage: `url(${masque.src})`, WebkitMaskImage: `url(${masque.src})`, maskMode: 'luminance', maskSize: '100% 100%', WebkitMaskSize: '100% 100%' } as React.CSSProperties} />}
              {points.map(([x, y, l], i) => <span key={i} style={{ position: 'absolute', left: `${x * 100}%`, top: `${y * 100}%`, width: 12, height: 12, margin: -6, borderRadius: 6, background: l ? '#35e08a' : '#ff4d5e', border: '2px solid #fff', pointerEvents: 'none' }} />)}
            </div>
            <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
              <button className="btn sm" onClick={() => (video.current?.paused ? video.current?.play() : video.current?.pause())}>Lecture / pause</button>
              <input type="range" min={0} max={duree || 1} step={1 / fps} value={t} onChange={(e) => { if (video.current) video.current.currentTime = Number(e.target.value); }} style={{ flex: 1 }} />
              <span className="dim" style={{ fontSize: 12 }}>image {image} · {t.toFixed(2)} s</span>
            </div>
            <div className="dim" style={{ fontSize: 12 }}>{masque && masque.image === image ? `Masque : ${(masque.aire * 100).toFixed(1)} % de l’image, calculé en ${masque.s.toFixed(2)} s.` : 'Clique sur le sujet pour voir son masque.'} {imagesCles.length ? `Images avec clics : ${imagesCles.sort((a, b) => a - b).join(', ')}.` : ''}</div>
          </>
        )}
        {fini && (
          <>
            <div className="seg" style={{ alignSelf: 'flex-start' }}>{vues.map(([n, l]) => <button key={n} className={vue === n ? 'on' : ''} onClick={() => setVue(n)}>{l}</button>)}</div>
            <video key={vue} src={lien(vue)} controls loop autoPlay muted style={{ maxWidth: '100%', maxHeight: '62vh', alignSelf: 'center', background: '#000' }} />
            <div style={{ display: 'flex', flexDirection: 'row', flexWrap: 'wrap', gap: 6 }}>
              {Object.entries(fich).filter(([n]) => /\.(mov|webm|mp4)$/.test(n) && n !== 'echecs.png').map(([n, o]) => <a key={n} className="btn sm" href={`${lien(n)}?telecharger=1`}>{n} · {fmtO(o)}</a>)}
              {[['alpha', 'Alpha PNG 16 bits'], ['rgba16', 'RGBA PNG 16 bits'], ['exr', 'EXR RGBA (prémultiplié, linéaire)'], ['alpha_exr', 'EXR alpha']].filter(([s]) => seq[s]).map(([s, l]) => <a key={s} className="btn sm" href={`${lien(`${s}.zip`)}?telecharger=1`}>{l} · {seq[s]} images (zip)</a>)}
              <a className="btn sm" href="/mode-studio/" title="Importe le ProRes 4444 ou le WebM alpha dans la timeline">Ouvrir Mode Studio</a>
            </div>
            {m && <div className="dim" style={{ fontSize: 12, lineHeight: 1.6 }}>
              Calcul {m.temps_total_s} s · {m.images} images · {m.segments} segment(s){m.coupures?.length ? ` · coupures aux images ${m.coupures.join(', ')}` : ''}{m.occlusions?.length ? ` · sujet absent aux images ${m.occlusions.map((o: number[]) => `${o[0]}–${o[1]}`).join(', ')}` : ''}
              {m.plans_sans_clic?.length ? <span style={{ color: 'var(--bad)' }}> · plans sans clic (masque vide) : {m.plans_sans_clic.map((o: number[]) => `${o[0]}–${o[1]}`).join(', ')}</span> : null}
              <br />GPU {m.gpu?.gpu} · VRAM pic {m.gpu?.vram_pic_go} Go · RAM pic {m.ram_pic_go} Go · disque {m.disque_sorties_go} Go
              {m.scintillement ? <><br />Scintillement des bords : {m.scintillement.avant} → {m.scintillement.apres} ({Math.round(m.scintillement.gain * 100)} % de moins)</> : null}
              {m.controle?.exr ? <><br />EXR : {m.controle.exr.bits.join('/')} bits, alpha {m.controle.exr.alpha}, {m.controle.exr.compression}, {m.controle.exr.espace} · PNG : {m.controle.alpha_png?.bits} bits</> : null}
            </div>}
            <button className="btn sm" style={{ alignSelf: 'flex-start' }} onClick={() => setTravail({ ...travail!, etat: 'depose' })}>Modifier les clics et relancer</button>
          </>
        )}
      </main>
    </div>
  );
}
