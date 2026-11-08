/**
 * Matte : importer une vidéo, cliquer le sujet (clics positifs et négatifs, sur plusieurs images),
 * voir le masque en direct, choisir fond et exports, lancer un travail asynchrone (progression, annulation, reprise),
 * puis prévisualiser (damier, matte, nouveau fond) et télécharger (PNG 16 bits, EXR, ProRes 4444, WebM alpha).
 * Rapport et mesures : recherche/22-detourage-video-pro.md.
 */
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { toast } from '../store';
import { NEXORA_PRODUCT_NAMES } from '../../shared/productNames.js';
import { creerCopieMatte, etatInterfaceMatte, type LangueMatte } from '../matteCopy';

const P = '/api/nexora/detourage';
type Pt = [number, number, 0 | 1];
interface Travail {
  id: string; nom: string; etat: string; etape: string; progression: number; message: string;
  source: { largeur: number; hauteur: number; fps: number; duree: number } | null;
  devis: { secondes: number; credits: number | null } | null;
  mesures: any; sorties: { fichiers?: Record<string, number>; sequences?: Record<string, number> } | null;
}
interface Capacites { rapide: { disponible: boolean; moteur: { nom: string } | null }; pro: { disponible: boolean; description: string }; limites: { secondesMax: number } }

class ErreurHttpMatte extends Error {
  constructor(readonly statut: number) { super('Matte HTTP'); }
}

async function appel<T>(chemin: string, init?: RequestInit): Promise<T> {
  const r = await fetch(`${P}${chemin}`, init);
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new ErreurHttpMatte(r.status);
  return j as T;
}

/** Envoi d'un fichier en flux avec progression (XHR : fetch n'expose pas la progression d'envoi). */
function envoyer(url: string, fichier: Blob, progression: (p: number) => void, copie: Copie = copieFR): Promise<any> {
  return new Promise((res, rej) => {
    const x = new XMLHttpRequest();
    x.open('PUT', url);
    x.upload.onprogress = (e) => e.lengthComputable && progression(e.loaded / e.total);
    x.onload = () => { try { const j = JSON.parse(x.responseText); x.status < 300 ? res(j) : rej(new ErreurHttpMatte(x.status)); } catch { rej(new ErreurHttpMatte(x.status)); } };
    x.onerror = () => rej(new Error(copie.t('error.uploadInterrupted')));
    x.setRequestHeader('content-type', 'application/octet-stream');
    x.send(fichier);
  });
}

const dateurMasque = (b64: string) => `data:image/png;base64,${b64}`;
type Copie = ReturnType<typeof creerCopieMatte>;
const copieFR = creerCopieMatte('fr');
const vueIdentifiants = ['apercu-echecs.mp4', 'matte.mp4', 'composite.mp4', 'suivi.mp4'] as const;
type VueId = typeof vueIdentifiants[number];
const CLES_VUE = {
  'apercu-echecs.mp4': 'view.damier', 'matte.mp4': 'view.matte', 'composite.mp4': 'view.newBackground', 'suivi.mp4': 'view.tracking',
} as const;
const CLES_FOND = { transparent: 'bg.label.transparent', couleur: 'bg.label.color', flou: 'bg.label.blur', image: 'bg.label.image' } as const;
const CLES_SEQ = { alpha: 'export.seq.alpha', rgba16: 'export.seq.rgba16', exr: 'export.seq.exr', alpha_exr: 'export.seq.alphaExr' } as const;

export default function Detourage() {
  const [langue, setLangue] = useState<LangueMatte>('fr');
  const copie = useMemo(() => creerCopieMatte(langue), [langue]);
  const tr = copie.t;
  const textesEtat = etatInterfaceMatte(langue);
  const copieCourante = useRef(copie);
  copieCourante.current = copie;
  const erreur = (e: unknown, cle: 'error.import' | 'error.preview' | 'error.search' | 'error.background' | 'error.launch'): string => {
    const c = copieCourante.current;
    const messages = etatInterfaceMatte(c.langue);
    if (e instanceof ErreurHttpMatte) {
      if (e.statut === 503) return messages.serviceUnavailable;
      if (e.statut === 402) return messages.credits;
      if (e.statut === 413) return messages.tooLarge;
    }
    return c.t(cle);
  };
  const [cap, setCap] = useState<Capacites | null>(null);
  const [travail, setTravail] = useState<Travail | null>(null);
  const [recents, setRecents] = useState<Travail[]>([]);
  const [urlLocale, setUrlLocale] = useState<string | null>(null);
  const [envoi, setEnvoi] = useState<number | null>(null);
  const [duree, setDuree] = useState(0);
  const [fps, setFps] = useState(24);
  const [t, setT] = useState(0); // position (secondes)
  const [clics, setClics] = useState<Record<number, Pt[]>>({}); // image -> points
  const [boites, setBoites] = useState<Record<number, number[]>>({}); // image -> boîte normalisée [x0, y0, x1, y1]
  const [mot, setMot] = useState(''); // mot en anglais pour la sélection par texte (SAM 3.1)
  const [trouves, setTrouves] = useState<{ image: number; secondes: number; objets: { masqueB64: string; score: number; boite: number[]; aire: number }[] } | null>(null);
  const [outil, setOutil] = useState<'ajouter' | 'retirer'>('ajouter');
  const [masque, setMasque] = useState<{ image: number; src: string; aire: number; s: number } | null>(null);
  const [occupe, setOccupe] = useState<'creating' | 'searching' | 'launching' | null>(null);
  const [mode, setMode] = useState<'suivi' | 'complet'>('complet');
  const [palier, setPalier] = useState<'rapide' | 'pro'>('rapide');
  const [largeur, setLargeur] = useState(1280);
  const [plage, setPlage] = useState<[number, number] | null>(null);
  const [fond, setFond] = useState<'transparent' | 'couleur' | 'flou' | 'image'>('transparent');
  const [couleur, setCouleur] = useState('#1aa36f');
  const [fichierFond, setFichierFond] = useState<string | null>(null);
  const [lissage, setLissage] = useState(1);
  const [vue, setVue] = useState<VueId>('apercu-echecs.mp4');
  const video = useRef<HTMLVideoElement>(null);
  const jeton = useRef(0);
  const importCourant = useRef(0);
  const occupationCourante = useRef(0);

  const [listeEtat, setListeEtat] = useState<'chargement' | 'ok' | 'erreur'>('chargement');
  const [listeVersion, setListeVersion] = useState(0);
  const [capErreur, setCapErreur] = useState(false);
  const [capVersion, setCapVersion] = useState(0);
  const [pollErreur, setPollErreur] = useState(false);
  const [suppressionEnCours, setSuppressionEnCours] = useState(false);
  const travailCourant = useRef(travail);
  travailCourant.current = travail;
  const monte = useRef(false);
  useEffect(() => { monte.current = true; return () => { monte.current = false; }; }, []);

  useEffect(() => {
    let actif = true;
    setCapErreur(false);
    void appel<Capacites>('/capacites').then((c) => {
      if (typeof c?.rapide?.disponible !== 'boolean' || !Number.isFinite(c?.limites?.secondesMax)) throw new Error('Capacités invalides.');
      if (actif) setCap(c);
    })
      .catch(() => { if (actif) setCapErreur(true); });
    return () => { actif = false; };
  }, [capVersion]);

  useEffect(() => {
    let actif = true;
    setListeEtat('chargement');
    void appel<Travail[]>('/travaux').then((l) => {
      if (!Array.isArray(l)) throw new Error('Liste invalide.');
      if (actif) { setRecents(l); setListeEtat('ok'); }
    }).catch(() => { if (actif) setListeEtat('erreur'); });
    return () => { actif = false; };
  }, [listeVersion]);

  useEffect(() => () => { if (urlLocale) URL.revokeObjectURL(urlLocale); }, [urlLocale]);

  const image = Math.round(t * fps);
  const points = clics[image] ?? [];

  // Chaque requête attend la précédente; les réponses d’un ancien travail sont ignorées.
  useEffect(() => {
    setPollErreur(false);
    if (!travail || !['en_attente', 'en_cours'].includes(travail.etat)) return;
    const id = travail.id;
    let actif = true;
    let minuterie: ReturnType<typeof setTimeout> | undefined;
    const controleur = new AbortController();
    const tour = async () => {
      let delai = 1500;
      try {
        const r = await appel<Travail>(`/travaux/${id}`, { signal: controleur.signal });
        if (!actif || travailCourant.current?.id !== id || !['en_attente', 'en_cours'].includes(travailCourant.current.etat)) return;
        if (r.id !== id) throw new Error('Réponse de suivi incohérente.');
        travailCourant.current = r;
        setTravail(r);
        setPollErreur(false);
        if (!['en_attente', 'en_cours'].includes(r.etat)) return;
      } catch {
        if (!actif || travailCourant.current?.id !== id) return;
        setPollErreur(true);
        delai = 5000;
      }
      if (actif) minuterie = setTimeout(() => { void tour(); }, delai);
    };
    minuterie = setTimeout(() => { void tour(); }, 1500);
    return () => { actif = false; clearTimeout(minuterie); controleur.abort(); };
  }, [travail?.id, travail?.etat]);

  async function importer(f: File) {
    const version = ++importCourant.current;
    const courant = () => monte.current && version === importCourant.current;
    const occupation = ++occupationCourante.current;
    setOccupe('creating');
    setEnvoi(0);
    try {
      const nouveau = await appel<Travail>('/travaux', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ nom: f.name.replace(/\.[^.]+$/, '') }) });
      if (!courant()) return;
      const r = await envoyer(`${P}/travaux/${nouveau.id}/source`, f, (p) => { if (courant()) setEnvoi(p); });
      if (!courant()) return;
      if (r.id !== nouveau.id) throw new Error('Source importée incohérente.');
      // Le nouvel import remplace l’ancien seulement une fois son dépôt confirmé.
      travailCourant.current = r;
      setTravail(r);
      setUrlLocale(URL.createObjectURL(f));
      jeton.current++;
      setClics({}); setBoites({}); setTrouves(null); setMasque(null); setPlage(null); setT(0);
      setFichierFond(null); setDuree(r.source?.duree ?? 0);
      if (r.source) setFps(r.source.fps);
      if (r.avertissement) toast(copieCourante.current.langue === 'fr' ? r.avertissement : etatInterfaceMatte(copieCourante.current.langue).sourceWarning, true);
      setListeVersion((v) => v + 1);
    } catch (e) {
      if (courant()) toast(erreur(e, 'error.import'), true);
    } finally {
      if (courant()) { setEnvoi(null); if (occupation === occupationCourante.current) setOccupe(null); }
    }
  }

  /** Image courante de la vidéo, réduite à 1280 px de large, en JPEG (base 64). */
  const capturer = useCallback((): string | null => {
    const v = video.current; if (!v || !v.videoWidth) return null;
    const k = Math.min(1, 1280 / v.videoWidth);
    const c = document.createElement('canvas'); c.width = Math.round(v.videoWidth * k); c.height = Math.round(v.videoHeight * k);
    c.getContext('2d')!.drawImage(v, 0, 0, c.width, c.height);
    return c.toDataURL('image/jpeg', 0.92).split(',')[1];
  }, []);

  const calculer = useCallback(async (pts: Pt[], boite?: number[] | null) => {
    const imageDemandee = Math.round((video.current?.currentTime ?? 0) * fps);
    const b64 = capturer(); if (!b64 || (!pts.length && !boite)) { setMasque(null); return; }
    const mon = ++jeton.current;
    try {
      const r = await appel<{ masqueB64: string; aire: number; secondes: number }>('/apercu', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ imageB64: b64, points: pts, ...(boite ? { boite } : {}) }) });
      const imageActuelle = Math.round((video.current?.currentTime ?? 0) * fps);
      if (monte.current && mon === jeton.current && imageDemandee === imageActuelle) setMasque({ image: imageDemandee, src: dateurMasque(r.masqueB64), aire: r.aire, s: r.secondes });
    } catch (e) { if (monte.current && mon === jeton.current) toast(erreur(e, 'error.preview'), true); }
  }, [capturer, fps, copie]);

  function cliquer(e: React.MouseEvent<HTMLDivElement>, negatifForce = false) {
    if (!travail || envoi !== null) return;
    const r = e.currentTarget.getBoundingClientRect();
    const x = (e.clientX - r.left) / r.width, y = (e.clientY - r.top) / r.height;
    const negatif = negatifForce || outil === 'retirer' || e.shiftKey || e.altKey;
    const pts: Pt[] = [...points, [Math.min(1, Math.max(0, x)), Math.min(1, Math.max(0, y)), negatif ? 0 : 1]];
    setClics({ ...clics, [image]: pts });
    video.current?.pause();
    void calculer(pts, boites[image]);
  }
  function annulerClic() { const pts = points.slice(0, -1); setClics({ ...clics, [image]: pts }); void calculer(pts, boites[image]); }
  function effacer() {
    const c = { ...clics }; delete c[image]; setClics(c);
    const b = { ...boites }; delete b[image]; setBoites(b);
    setTrouves(null); setMasque(null);
  }
  useEffect(() => { jeton.current++; setMasque(null); if (points.length || boites[image]) void calculer(points, boites[image]); /* image changée : recalcul */ // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [image]);

  /** Sélection par un mot (en anglais) : SAM 3.1 renvoie les objets trouvés, à choisir d'un clic. */
  async function chercherTexte() {
    const texte = mot.trim(); if (!texte || !travail || envoi !== null) return;
    const b64 = capturer(); if (!b64) return;
    const mon = ++jeton.current;
    const occupation = ++occupationCourante.current;
    video.current?.pause();
    try {
      setOccupe('searching');
      const r = await appel<{ objets: { masqueB64: string; score: number; boite: number[]; aire: number }[]; secondes: number }>('/texte', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ imageB64: b64, texte }) });
      if (!monte.current || mon !== jeton.current) return;
      setTrouves({ image, secondes: r.secondes, objets: r.objets });
      if (!r.objets.length) toast(copieCourante.current.t('mask.notFound', { texte }), true);
    } catch (e) { if (monte.current && mon === jeton.current) toast(erreur(e, 'error.search'), true); } finally { if (monte.current && occupation === occupationCourante.current) setOccupe(null); }
  }

  /** Un objet trouvé devient la graine de l'image courante : sa boîte, ses points éventuels, et son masque en aperçu. */
  function choisirObjet(o: { masqueB64: string; score: number; boite: number[]; aire: number }) {
    if (!Array.isArray(o.boite) || o.boite.length !== 4) return;
    const boite = o.boite.map(Number);
    setBoites({ ...boites, [image]: boite });
    setTrouves(null);
    setMasque({ image, src: dateurMasque(o.masqueB64), aire: o.aire, s: 0 });
    jeton.current++; // un aperçu en cours ne doit pas écraser ce masque
  }

  const nbClics = useMemo(() => Object.values(clics).reduce((n, p) => n + p.length, 0), [clics]);
  const debut = plage?.[0] ?? 0;
  const imagesCles = useMemo(() => [...new Set([...Object.keys(clics).map(Number).filter((i) => (clics[i]?.length ?? 0) > 0), ...Object.keys(boites).map(Number)])].sort((a, b) => a - b), [clics, boites]);

  async function deposerFond(f: File) {
    const id = travail?.id;
    if (!id) return;
    try {
      const ext = (f.name.split('.').pop() ?? 'png').toLowerCase();
      const r = await envoyer(`${P}/travaux/${id}/fond?ext=${ext}`, f, () => {});
      if (!monte.current || travailCourant.current?.id !== id) return;
      setFichierFond(r.fond); setFond('image'); toast(copieCourante.current.t('toast.uploadDone'));
    } catch (e) {
      if (monte.current && travailCourant.current?.id === id) toast(erreur(e, 'error.background'), true);
    }
  }

  async function lancer() {
    if (!travail) return;
    const invites = imagesCles.filter((i) => i >= Math.round(debut * fps)).map((i) => ({
      image: i - Math.round(debut * fps), points: clics[i] ?? [], ...(boites[i] ? { boite: boites[i] } : {}),
    }));
    if (!invites.length) { toast(tr('error.launchHint'), true); return; }
    const composite = fond === 'couleur' ? { type: 'couleur', valeur: couleur } : fond === 'flou' ? { type: 'flou' } : fond === 'image' && fichierFond ? { type: /\.(mp4|mov|webm)$/.test(fichierFond) ? 'video' : 'image', fichier: fichierFond } : null;
    const id = travail.id;
    const occupation = ++occupationCourante.current;
    try {
      setOccupe('launching');
      const r = await appel<Travail>(`/travaux/${id}/lancer`, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({
        palier, mode, invites, debutS: debut, dureeS: plage ? plage[1] - plage[0] : null, largeurMax: largeur, lissage, composite,
      }) });
      if (monte.current && travailCourant.current?.id === id) { travailCourant.current = r; setTravail(r); }
    } catch (e) {
      if (monte.current && travailCourant.current?.id === id) toast(erreur(e, 'error.launch'), true);
    } finally { if (monte.current && occupation === occupationCourante.current) setOccupe(null); }
  }
  async function action(a: 'annuler' | 'reprendre') {
    const id = travail?.id;
    if (!id) return;
    try {
      const r = await appel<Travail>(`/travaux/${id}/${a}`, { method: 'POST' });
      if (monte.current && travailCourant.current?.id === id) { travailCourant.current = r; setTravail(r); }
    } catch {
      if (monte.current && travailCourant.current?.id === id) toast(copieCourante.current.generique(), true);
    }
  }

  async function supprimer() {
    const courant = travail;
    if (!courant || suppressionEnCours || !confirm(tr('confirm.deleteJob'))) return;
    setSuppressionEnCours(true);
    try {
      await appel(`/travaux/${courant.id}`, { method: 'DELETE' });
    } catch {
      if (monte.current) { toast(etatInterfaceMatte(copieCourante.current.langue).deleteError, true); setSuppressionEnCours(false); }
      return;
    }
    if (!monte.current) return;
    // La suppression confirmée d’A ne doit jamais effacer un nouveau travail B.
    if (travailCourant.current?.id === courant.id) {
      travailCourant.current = null;
      jeton.current++;
      setTravail(null); setUrlLocale(null); setClics({}); setBoites({}); setTrouves(null); setMasque(null);
      setFichierFond(null); setPlage(null); setDuree(0); setT(0);
    }
    setRecents((l) => l.filter((r) => r.id !== courant.id));
    setSuppressionEnCours(false);
    setListeVersion((v) => v + 1);
  }

  const fini = travail?.etat === 'termine';
  const enCours = travail && ['en_attente', 'en_cours'].includes(travail.etat);
  const fich = travail?.sorties?.fichiers ?? {};
  const seq = travail?.sorties?.sequences ?? {};
  const m = travail?.mesures;
  const lien = (nom: string) => `${P}/travaux/${travail!.id}/sorties/${nom}`;
  const vues = vueIdentifiants.filter((n) => fich[n]).map((n) => [n, tr(CLES_VUE[n])] as [VueId, string]);
  /** Ligne d’aide sous l’image : masque calculé, objets trouvés par le mot, ou invitation à cliquer. */
  const aideMasque = masque && masque.image === image
    ? tr('mask.summary', { pourcent: (masque.aire * 100).toFixed(1), detailCalcul: masque.s ? tr('mask.summary.detail', { s: masque.s.toFixed(2) }) : '' })
    : trouves && trouves.image === image && trouves.objets.length
      ? copie.t('mask.found', { n: trouves.objets.length, s: trouves.objets.length > 1 ? 's' : '', mot: mot.trim(), sec: trouves.secondes.toFixed(2) })
      : trouves && trouves.image === image
        ? tr('mask.notFound', { texte: mot.trim() })
        : tr('mask.helpDefault');

  return (
    <div className="rail-layout" lang={langue === 'fr' ? 'fr-CA' : 'en-CA'} style={{ gridTemplateColumns: '380px 1fr' }}>
      <aside className="rail">
        <div className="display" style={{ fontSize: 26 }}>{NEXORA_PRODUCT_NAMES.matte}</div>
        <div style={{ display: 'flex', gap: 6, margin: '4px 0' }}>
          <button className={`btn sm${langue === 'fr' ? ' on' : ''}`} lang="fr-CA" onClick={() => setLangue('fr')}>{copie.boutons.francais}</button>
          <button className={`btn sm${langue === 'en' ? ' on' : ''}`} lang="en-CA" onClick={() => setLangue('en')}>{copie.boutons.english}</button>
        </div>
        <div className="dim" style={{ fontSize: 12.5, marginTop: -4 }}>{tr('header.subtitle')}</div>

        {capErreur && <div className="rail-section" role="alert">{textesEtat.capError} <button type="button" className="btn sm" onClick={() => setCapVersion((v) => v + 1)}>{textesEtat.retry}</button></div>}
        {pollErreur && <div className="rail-section" role="alert">{textesEtat.pollError}</div>}
        {cap && !cap.rapide.disponible && <div className="rail-section" style={{ color: 'var(--bad)', fontSize: 12.5 }}>{tr('engine.unavailable')}</div>}

        <div className="rail-section">
          <div className="label">{tr('section.video.title')}</div>
          <input type="file" aria-label={tr('section.video.title')} accept="video/*" onChange={(e) => e.target.files?.[0] && importer(e.target.files[0])} disabled={!cap?.rapide.disponible || !!enCours} />
          {envoi !== null && <progress value={envoi} max={1} style={{ width: '100%' }} />}
          {travail?.source && <div className="dim" style={{ fontSize: 12 }}>{tr('source.summary', { largeur: travail.source.largeur, hauteur: travail.source.hauteur, fps: travail.source.fps.toFixed(2), duree: copie.fmtDuree(travail.source.duree) })}{travail.source.duree > (cap?.limites.secondesMax ?? 120) ? tr('source.limitHint', { secondesMax: cap?.limites.secondesMax }) : ''}</div>}
        </div>

        <div className="rail-section">
          <div className="label">{tr('section.subject.title')} {imagesCles.length ? ` ${tr('subject.counts', { virgule: nbClics && imagesCles.length ? ', ' : '', clics: nbClics ? tr(nbClics > 1 ? 'subject.counts.clics.pluriel' : 'subject.counts.clics.singulier', { n: nbClics }) : '', imagesCles: tr(imagesCles.length > 1 ? 'subject.counts.images.pluriel' : 'subject.counts.images.singulier', { n: imagesCles.length }) })}` : ''}</div>
          <label className="dim" style={{ fontSize: 12 }} htmlFor="mot-detourage">{tr('subject.wordLabel')}</label>
          <div style={{ display: 'flex', gap: 6 }}>
            <input id="mot-detourage" type="text" value={mot} placeholder={tr('subject.wordPlaceholder')} onChange={(e) => setMot(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter') void chercherTexte(); }} style={{ flex: 1, minWidth: 0 }} disabled={!travail || envoi !== null} />
            <button className="btn sm" onClick={() => void chercherTexte()} disabled={!mot.trim() || !!occupe || !travail || envoi !== null}>{tr('action.search')}</button>
          </div>
          <div className="seg"><button className={outil === 'ajouter' ? 'on' : ''} onClick={() => setOutil('ajouter')}>{tr('tool.add')}</button><button className={outil === 'retirer' ? 'on' : ''} onClick={() => setOutil('retirer')}>{tr('tool.remove')}</button></div>
          <div className="dim" style={{ fontSize: 12 }}>{tr('subject.help')}</div>
          <div style={{ display: 'flex', gap: 6 }}><button className="btn sm" onClick={annulerClic} disabled={!points.length}>{tr('action.undoLast')}</button><button className="btn sm" onClick={effacer} disabled={!points.length && !boites[image]}>{tr('action.clearFrame')}</button></div>
          {duree > 0 && <>
            <div className="label" style={{ marginTop: 6 }}>{tr('range.title')}</div>
            <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
              <button className="btn sm" onClick={() => setPlage([t, plage?.[1] ?? duree])}>{tr('range.setStart')}</button>
              <button className="btn sm" onClick={() => setPlage([plage?.[0] ?? 0, Math.max(t, (plage?.[0] ?? 0) + 0.5)])}>{tr('range.setEnd')}</button>
              <span className="dim" style={{ fontSize: 12 }}>{plage ? tr('range.value', { debut: plage[0].toFixed(1), fin: plage[1].toFixed(1) }) : tr('range.allVideo')}</span>
            </div></>}
        </div>

        <div className="rail-section">
          <div className="label">{tr('section.quality.title')}</div>
          <div className="seg"><button className={palier === 'rapide' ? 'on' : ''} onClick={() => setPalier('rapide')}>{tr('tier.fast')}</button>
            <button className={palier === 'pro' ? 'on' : ''} disabled title={tr('tier.proSoon')} style={{ opacity: 0.45 }}>{tr('tier.proSoon')}</button></div>
          <div className="seg"><button className={mode === 'suivi' ? 'on' : ''} onClick={() => setMode('suivi')}>{tr('mode.trackPreview')}</button><button className={mode === 'complet' ? 'on' : ''} onClick={() => setMode('complet')}>{tr('mode.full')}</button></div>
          <label className="dim" style={{ fontSize: 12 }}>{tr('quality.maxWidth', { largeur })}
            <input type="range" min={640} max={3840} step={160} value={largeur} onChange={(e) => setLargeur(Number(e.target.value))} style={{ width: '100%' }} /></label>
          <label className="dim" style={{ fontSize: 12 }}>{tr('quality.edgeSmoothing', { lissage: lissage.toFixed(1) })}
            <input type="range" min={0} max={1.5} step={0.1} value={lissage} onChange={(e) => setLissage(Number(e.target.value))} style={{ width: '100%' }} /></label>
        </div>

        <div className="rail-section">
          <div className="label">{tr('section.background.title')}</div>
          <div className="seg">{(['transparent', 'couleur', 'flou', 'image'] as const).map((f) => <button key={f} className={fond === f ? 'on' : ''} onClick={() => setFond(f)}>{tr(CLES_FOND[f])}</button>)}</div>
          {fond === 'couleur' && <input type="color" value={couleur} onChange={(e) => setCouleur(e.target.value)} />}
          {fond === 'image' && <><input type="file" accept="image/*,video/*" onChange={(e) => e.target.files?.[0] && deposerFond(e.target.files[0])} />{fichierFond && <span className="dim" style={{ fontSize: 12 }}>{tr('bg.deposited')}</span>}</>}
          <div className="dim" style={{ fontSize: 12 }}>{tr('bg.help')}</div>
        </div>

        <div className="rail-section">
          {enCours
            ? <><progress value={travail!.progression} max={1} style={{ width: '100%' }} /><div className="dim" style={{ fontSize: 12.5 }}>{tr('job.progress', { etapeOuMessage: langue === 'fr' ? (travail!.message || copie.etat(travail!.etat)) : copie.etat(travail!.etat), pourcent: Math.round(travail!.progression * 100) })}</div><button className="btn sm" onClick={() => action('annuler')}>{tr('action.cancelJob')}</button></>
            : <button className="btn sm accent" onClick={lancer} disabled={!travail || !imagesCles.length || !!occupe || envoi !== null}>{occupe ? tr(`job.busy.${occupe}`) : (mode === 'suivi' ? tr('job.launch.trackPreview') : tr('job.launch.full'))}</button>}
          {travail && ['interrompu', 'erreur', 'annule'].includes(travail.etat) && <><div style={{ color: 'var(--bad)', fontSize: 12.5 }}>{tr('job.interrupted')}</div><button className="btn sm" onClick={() => action('reprendre')}>{tr('action.resumeKept')}</button></>}
          {travail && !enCours && <button className="btn sm" disabled={suppressionEnCours} onClick={supprimer}>{suppressionEnCours ? textesEtat.deleting : tr('action.deleteJob')}</button>}
        </div>
        {!travail && listeEtat === 'chargement' && <div className="rail-section" role="status">{textesEtat.loading}</div>}
        {listeEtat === 'erreur' && <div className="rail-section" role="alert">{textesEtat.listError} <button type="button" className="btn sm" onClick={() => setListeVersion((v) => v + 1)}>{textesEtat.retry}</button></div>}
        {!travail && listeEtat === 'ok' && recents.length === 0 && <div className="rail-section">{textesEtat.empty}</div>}
        {recents.length > 0 && !travail && <div className="rail-section"><div className="label">{tr('recents.title')}</div>{recents.slice(0, 6).map((r) => <div key={r.id} className="dim" style={{ fontSize: 12 }}>{tr('recents.item', { nom: r.nom, etat: copie.etat(r.etat) })}</div>)}</div>}
      </aside>

      <main style={{ display: 'flex', flexDirection: 'column', gap: 10, minWidth: 0, overflow: 'auto' }}>
        {!urlLocale && <div className="dim" style={{ padding: 40, textAlign: 'center' }}>{tr('empty.importPrompt')}</div>}
        {urlLocale && !fini && (
          <>
            <div style={{ position: 'relative', alignSelf: 'center', maxWidth: '100%', cursor: 'crosshair' }} onClick={cliquer} onContextMenu={(e) => { e.preventDefault(); cliquer(e, true); }}>
              <video key={urlLocale} ref={video} src={urlLocale} muted playsInline style={{ maxWidth: '100%', maxHeight: '62vh', display: 'block' }}
                onLoadedMetadata={(e) => setDuree((e.target as HTMLVideoElement).duration)} onTimeUpdate={(e) => setT((e.target as HTMLVideoElement).currentTime)} />
              {masque && masque.image === image && <div aria-hidden style={{ position: 'absolute', inset: 0, background: '#ff3b5c', opacity: 0.5, pointerEvents: 'none', maskImage: `url(${masque.src})`, WebkitMaskImage: `url(${masque.src})`, maskMode: 'luminance', maskSize: '100% 100%', WebkitMaskSize: '100% 100%' } as React.CSSProperties} />}
              {points.map(([x, y, l], i) => <span key={i} style={{ position: 'absolute', left: `${x * 100}%`, top: `${y * 100}%`, width: 12, height: 12, margin: -6, borderRadius: 6, background: l ? '#35e08a' : '#ff4d5e', border: '2px solid #fff', pointerEvents: 'none' }} />)}
              {boites[image] && <div aria-hidden style={{ position: 'absolute', left: `${boites[image][0] * 100}%`, top: `${boites[image][1] * 100}%`, width: `${(boites[image][2] - boites[image][0]) * 100}%`, height: `${(boites[image][3] - boites[image][1]) * 100}%`, border: '2px dashed #35e08a', borderRadius: 4, pointerEvents: 'none' }} />}
              {trouves && trouves.image === image && trouves.objets.map((o, i) => (
                <div key={i} title={tr('finder.chooseTitle', { score: o.score.toFixed(2) })} onClick={(e) => { e.stopPropagation(); choisirObjet(o); }}
                  style={{ position: 'absolute', left: `${o.boite[0] * 100}%`, top: `${o.boite[1] * 100}%`, width: `${(o.boite[2] - o.boite[0]) * 100}%`, height: `${(o.boite[3] - o.boite[1]) * 100}%`, border: '2px solid #4da3ff', borderRadius: 4, background: 'rgba(77, 163, 255, 0.12)', cursor: 'pointer' }}>
                  <span style={{ position: 'absolute', left: 0, top: -18, fontSize: 11, lineHeight: '16px', padding: '0 4px', borderRadius: 3, background: '#4da3ff', color: '#fff', whiteSpace: 'nowrap' }}>{tr('finder.chooseLabel', { mot: mot.trim(), score: o.score.toFixed(2) })}</span>
                </div>
              ))}
            </div>
            <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
              <button className="btn sm" onClick={() => (video.current?.paused ? video.current?.play() : video.current?.pause())}>{tr('player.playPause')}</button>
              <input type="range" min={0} max={duree || 1} step={1 / fps} value={t} onChange={(e) => { if (video.current) video.current.currentTime = Number(e.target.value); }} style={{ flex: 1 }} />
              <span className="dim" style={{ fontSize: 12 }}>{tr('player.position', { image, t: t.toFixed(2) })}</span>
            </div>
            <div className="dim" style={{ fontSize: 12 }}>{aideMasque} {imagesCles.length ? tr('mask.keyFrames', { liste: imagesCles.join(', ') }) : ''}</div>
          </>
        )}
        {fini && (
          <>
            <div className="seg" style={{ alignSelf: 'flex-start' }}>{vues.map(([n, l]) => <button key={n} className={vue === n ? 'on' : ''} onClick={() => setVue(n)}>{l}</button>)}</div>
            <video key={vue} src={lien(vue)} controls loop autoPlay muted style={{ maxWidth: '100%', maxHeight: '62vh', alignSelf: 'center', background: '#000' }} />
            <div style={{ display: 'flex', flexDirection: 'row', flexWrap: 'wrap', gap: 6 }}>
              {Object.entries(fich).filter(([n]) => /\.(mov|webm|mp4)$/.test(n) && n !== 'echecs.png').map(([n, o]) => <a key={n} className="btn sm" href={`${lien(n)}?telecharger=1`}>{tr('export.videoFile', { nom: n, taille: copie.fmtTaille(o) })}</a>)}
              {(Object.keys(CLES_SEQ) as (keyof typeof CLES_SEQ)[]).filter((s) => seq[s]).map((s) => <a key={s} className="btn sm" href={`${lien(`${s}.zip`)}?telecharger=1`}>{tr('export.seq.count', { label: tr(CLES_SEQ[s]), n: seq[s] })}</a>)}
              <a className="btn sm" href="/mode-studio/" title={tr('export.openStudio.title')}>{tr('export.openStudio')}</a>
            </div>
            {m && <div className="dim" style={{ fontSize: 12, lineHeight: 1.6 }}>
              {tr('measures.summary', { duree: m.temps_total_s, images: m.images, segments: m.segments, coupures: m.coupures?.length ? tr('measures.cuts', { liste: m.coupures.join(', ') }) : '', occlusions: m.occlusions?.length ? tr('measures.occlusions', { plages: m.occlusions.map((o: number[]) => `${o[0]}–${o[1]}`).join(', ') }) : '', sansClic: '' })}
              {m.plans_sans_clic?.length ? <span style={{ color: 'var(--bad)' }}>{tr('measures.noClick', { plages: m.plans_sans_clic.map((o: number[]) => `${o[0]}–${o[1]}`).join(', ') })}</span> : null}
              <br />{tr('measures.hardware', { gpu: m.gpu?.gpu, vram: m.gpu?.vram_pic_go, ram: m.ram_pic_go, disque: m.disque_sorties_go })}
              {m.scintillement ? <><br />{tr('measures.flicker', { avant: m.scintillement.avant, apres: m.scintillement.apres, gain: Math.round(m.scintillement.gain * 100) })}</> : null}
              {m.controle?.exr ? <><br />{tr('measures.control', { bits: m.controle.exr.bits.join('/'), alpha: m.controle.exr.alpha, compression: m.controle.exr.compression, espace: m.controle.exr.espace, bitsPng: m.controle.alpha_png?.bits })}</> : null}
            </div>}
            <button className="btn sm" style={{ alignSelf: 'flex-start' }} onClick={() => setTravail({ ...travail!, etat: 'depose' })}>{tr('action.editAndRelaunch')}</button>
          </>
        )}
      </main>
    </div>
  );
}
