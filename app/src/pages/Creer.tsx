/**
 * Nexora Creative — le studio « Créer ».
 * À gauche, le composeur : une idée en français, un bouton « Booster ma phrase » (le LLM la rend plus riche et plus filmable),
 * trois modes (Vidéo, Image, Film), un départ facultatif (ta photo ou un plan clé dessiné par Qwen-Image) et la musique
 * MiniMax en option. À droite, les créations en direct : progression, aperçu, musique, animation d'un plan clé.
 * Vidéo : le LLM écrit le scénario H3 et MiniMax H3 tourne (RTX 5090). Image : Qwen-Image (GB10). Film : l'AI Director
 * propose un découpage relisible, tourne chaque plan et assemble.
 */
import { useEffect, useMemo, useRef, useState } from 'react';
import { api, EchecFilmPartiel, mediaUrl, posterUrl, uploadFile, type Comprehension, type EtatNexora, type Storyboard } from '../api';
import { getState, inFeed, isImage, isModel, refreshTakes, settingsOf, toast, useStore } from '../store';
import { MediaCard } from '../ui';
import Viewer from '../Viewer';
import FilmPlans from '../FilmPlans';
import { Publication } from '../studio/Publication';
import Producteur from '../studio/Producteur';
import { CAMERAS } from '../studio/apps';
import { setParams, useRoute } from '../router';
import { isCurrentVideoHandoff, readVideoStillHandoff } from '../viewerHandoff';
import { resumeCorrespondAIntention } from '../creationSummary';
import { IcEtincelle, IcFilm, IcImage, IcRond, IcVideo, Ratio } from '../studio/icons';
import { cleDevisCreation, ControleDevis } from '../devisCreation';
import { creationVideoCopy, erreurVisibleCreationVideo, nomCameraCreation } from '../creationVideoCopy';
import type { LangueClient } from '../../shared/creationLanguage';
import { FilmPartielAlerte } from '../FilmPartielAlerte';

type Mode = 'producteur' | 'video' | 'image' | 'film';
const MODES: Mode[] = ['producteur', 'video', 'image', 'film'];
type Format = '16:9' | '9:16' | '1:1';
type Depart = 'texte' | 'photo' | 'cle';
type Filtre = 'tout' | 'videos' | 'films' | 'images';

const IDEES: Record<Exclude<Mode, 'producteur'>, string[]> = {
  video: [
    'Ma voiture rouge se transforme en robot géant pendant que la caméra tourne autour, au coucher du soleil.',
    'Un dragon d’obsidienne jaillit d’une mer de nuages d’orage et rugit vers la caméra.',
    'Publicité pour un café glacé : gouttes au ralenti, lumière dorée, une voix dit « Le froid qui réveille ».',
    'Combat de karaté sur un toit trempé de pluie, la nuit, sous des lanternes rouges.',
  ],
  image: [
    'Une guerrière en kimono noir face à un dragon sur une falaise, au crépuscule.',
    'Affiche de film : un astronaute seul sur une plage de cendres sous deux lunes.',
    'Portrait en studio d’un renard en papier découpé, lumière douce, fond bleu nuit.',
  ],
  film: [
    'Un livreur à vélo découvre qu’une ville entière s’illumine sur son passage, de l’aube à la nuit.',
    'Une flotte de vaisseaux surgit de l’hyperespace au-dessus d’une planète à anneaux ; un duel éclate dans un temple.',
  ],
};
const FORMATS: { v: Format; label: string; aide: string }[] = [
  { v: '16:9', label: 'Paysage', aide: 'YouTube, site' },
  { v: '9:16', label: 'Vertical', aide: 'TikTok, Reels' },
  { v: '1:1', label: 'Carré', aide: 'Publications' },
];
const DUREES_VIDEO = [5, 10, 15] as const;
const DUREES_FILM = [{ v: 30, label: '30 s' }, { v: 60, label: '1 min' }, { v: 120, label: '2 min' }] as const;
const SECONDES_PAR_PLAN_5S = 40;

const fmtTemps = (s: number, langue: LangueClient = 'fr') => (s < 90 ? `${Math.round(s)} s` : langue === 'en' ? `${Math.floor(s / 60)} min ${String(Math.round(s % 60)).padStart(2, '0')} sec` : `${Math.floor(s / 60)} min ${String(Math.round(s % 60)).padStart(2, '0')} s`);

export default function Creer() {
  const { params } = useRoute();
  const mode: Mode = MODES.includes(params.get('mode') as Mode) ? (params.get('mode') as Mode) : 'producteur';
  const handoffEpoch = useRef(0);
  const [langueClient, setLangueClient] = useState<LangueClient>('fr');
  const langueActive: LangueClient = mode === 'video' ? langueClient : 'fr';
  const texteVideo = creationVideoCopy(langueActive);
  const langueClientRef = useRef(langueClient);
  langueClientRef.current = langueClient;
  const modeRef = useRef(mode);
  modeRef.current = mode;
  const texteCourantCreation = () => creationVideoCopy(modeRef.current === 'video' ? langueClientRef.current : 'fr');
  const [intention, setIntention] = useState('');
  const intentionRef = useRef(intention);
  intentionRef.current = intention;
  const [format, setFormat] = useState<Format>('16:9');
  const [duree, setDuree] = useState<number>(5);
  const [dureeFilm, setDureeFilm] = useState<number>(30);
  const [son, setSon] = useState(true);
  const [musique, setMusique] = useState(false);
  const [qualite, setQualiteState] = useState<'rapide' | 'max'>('rapide');
  const [nombreImages, setNombreImages] = useState(2);
  const [depart, setDepart] = useState<Depart>(() => (params.get('depart') === 'photo' ? 'photo' : 'texte'));
  const [camera, setCamera] = useState<string | null>(null);
  const [cle, setCleState] = useState<{ jeton: string; apercu: string } | null>(null);
  const [envoi, setEnvoi] = useState<null | 'creer' | 'plan' | 'film' | 'cle' | 'boost' | 'photo' | 'prise'>(null);
  const [boost, setBoost] = useState<string | null>(null);
  const [compris, setCompris] = useState<(Comprehension & { credits?: number; prompt: string; intentionSource: string }) | null>(null);
  const [voirPrompt, setVoirPrompt] = useState(false);
  function changerIntention(value: string) {
    intentionRef.current = value;
    setIntention(value);
    if (compris && !resumeCorrespondAIntention(compris.intentionSource, value)) {
      setCompris(null);
      setVoirPrompt(false);
    }
  }
  const [storyboard, setStoryboard] = useState<Storyboard | null>(null);
  const [filmPartiel, setFilmPartiel] = useState<EchecFilmPartiel | null>(null);
  const [etat, setEtat] = useState<EtatNexora | null>(null);
  const [vue, setVue] = useState<number | null>(null);
  const [filmOuvert, setFilmOuvert] = useState<number | null>(null);
  const [filtre, setFiltre] = useState<Filtre>('tout');
  const [replique, setReplique] = useState('');
  const [langueReplique, setLangueReplique] = useState<LangueClient>('fr');
  const [pub, setPub] = useState<number | null>(null);
  const [idees, setIdees] = useState<Partial<Record<Exclude<Mode, 'producteur'>, string[]>>>({});
  const [inspire, setInspire] = useState(false);
  const [devis, setDevis] = useState<{ credits: number | null; secondesEstimees: number | null; erreur?: string; code?: string; cle: string } | null>(null);
  const toutes = useStore((s) => s.takes);
  const lances = useRef(new Set<number>());
  const jetonsRecus = useRef(new Set<string>());
  const handoffsImageEnCours = useRef(new Set<string>());
  const dernierMode = useRef(mode);
  const versionLangueRef = useRef(0);
  const requeteIdeesRef = useRef(0);
  const requeteBoostRef = useRef(0);

  const controleDevis = useRef(new ControleDevis());
  function invaliderDevis() { controleDevis.current.invalider(); setDevis(null); }
  function setQualite(value: 'rapide' | 'max') { if (value !== qualite) invaliderDevis(); setQualiteState(value); }
  function setCle(value: { jeton: string; apercu: string } | null) { if (value?.jeton !== cle?.jeton) invaliderDevis(); setCleState(value); }

  function invaliderSelectionImage() {
    handoffEpoch.current += 1;
    setEnvoi((courant) => courant === 'prise' || courant === 'photo' ? null : courant);
  }
  const setMode = (m: Mode) => {
    if (m !== mode) {
      invaliderSelectionImage();
      dernierMode.current = m;
    }
    setParams({ mode: m === 'producteur' ? null : m });
  };
  function changerDepart(v: Depart) {
    if (v === depart) return;
    invaliderSelectionImage();
    setDepart(v);
    setCle(null);
  }

  // A browser back/forward or another route link can change mode without setMode().
  useEffect(() => {
    if (dernierMode.current !== mode) {
      dernierMode.current = mode;
      invaliderSelectionImage();
    }
    if (mode !== 'video' && params.has('cle')) setParams({ cle: null, intention: null, handoff: null });
  }, [mode, params.get('cle')]);

  const visibles = useStore((s) => s.takes.filter((t) => inFeed(t) && !isModel(t) && settingsOf(t).nexoraFilm == null && settingsOf(t).nexoraMusiqueDe == null && t.kind !== 'audio'));
  const montrees = useMemo(() => visibles.filter((t) => {
    const s = settingsOf(t);
    if (filtre === 'images') return isImage(t);
    if (filtre === 'films') return !!s.film;
    if (filtre === 'videos') return !isImage(t) && !s.film;
    return true;
  }).slice(0, 24), [visibles, filtre]);
  const ids = useMemo(() => montrees.map((t) => t.id), [montrees]);

  // Musiques composées pour des clips (MiniMax-Music3) : dès qu'une est prête, le mixage se lance une seule fois.
  const musiques = useStore((s) => s.takes.filter((t) => settingsOf(t).nexoraMusiqueDe != null && settingsOf(t).app === 'nexora-musique' && t.status !== 'failed' && t.status !== 'stopped'));
  useEffect(() => {
    for (const m of musiques) {
      const clip = settingsOf(m).nexoraMusiqueDe as number;
      const dejaMixee = toutes.some((x) => settingsOf(x).nexoraAvecMusique && settingsOf(x).musique === m.output_path);
      if (m.status !== 'done' || lances.current.has(m.id) || dejaMixee || settingsOf(toutes.find((x) => x.id === clip) ?? m).film) continue;
      lances.current.add(m.id);
      api.nexoraClipAvecMusique(clip, m.id)
        .then(() => toast(texteCourantCreation().toastMusicMixReady))
        .catch(() => toast(texteCourantCreation().errorMusicMix, true));
    }
  }, [musiques, toutes]);
  // « Avec musique » demandé à la création : la musique se compose dès que le clip est terminé.
  useEffect(() => {
    for (const t of toutes) {
      const s = settingsOf(t);
      if (!s.nexoraAutoMusique || t.status !== 'done' || s.nexoraMusiqueLance || lances.current.has(-t.id)) continue;
      lances.current.add(-t.id);
      api.nexoraClipMusique(t.id, {}).catch(() => {});
    }
  }, [toutes]);

  useEffect(() => { void api.nexoraEtat().then(setEtat).catch(() => setEtat(null)); }, []);
  // « Animer avec H3 » depuis Nexora Mesh : /?mode=video&jeton=asset:…&intention=… pose la vue 3D comme plan clé.
  useEffect(() => {
    const jeton = params.get('jeton');
    if (!jeton || !/^asset:[0-9a-f-]{36}$/i.test(jeton) || jetonsRecus.current.has(jeton)) return;
    jetonsRecus.current.add(jeton);
    let apercu = '';
    try { apercu = sessionStorage.getItem('nexora-plan-cle-apercu') ?? ''; sessionStorage.removeItem('nexora-plan-cle-apercu'); } catch { /* sans aperçu */ }
    const texte = params.get('intention');
    setParams({ jeton: null, intention: null });
    setCle({ jeton, apercu });
    setDepart('cle');
    if (texte) changerIntention(texte.slice(0, 4000));
    toast(texteCourantCreation().toast3dKeyframe);
  }, [params.get('jeton')]);
  // « Animer » depuis la Bibliothèque : /?mode=video&cle=<image> pose l'image comme plan clé.
  useEffect(() => {
    const handoff = readVideoStillHandoff(mode, params);
    if (!handoff) return;
    const handoffKey = handoff.handoffId ?? `${handoff.takeId}:${handoff.intention ?? ''}`;
    if (handoffsImageEnCours.current.has(handoffKey)) return;
    handoffsImageEnCours.current.add(handoffKey);
    setParams({ cle: null, intention: null, handoff: null });
    if (handoff.intention !== undefined) changerIntention(handoff.intention);
    void animer(handoff.takeId, `${location.pathname}${location.search}`).finally(() => handoffsImageEnCours.current.delete(handoffKey));
  }, [mode, params.get('cle'), params.get('intention')]);
  const film = mode === 'film';
  const dureeClip = duree;
  const cleDevis = cleDevisCreation(mode, format, dureeClip, son, qualite, cle?.jeton, langueClient);
  const devisCourant = devis?.cle === cleDevis ? devis : null;
  useEffect(() => {
    if (mode !== 'video') { setDevis(null); return; }
    let actif = true;
    const version = controleDevis.current.jeton();
    void api.nexoraDevis({ format, duree: dureeClip, son, qualite, image: cle?.jeton, langueClient }).then((d) => actif && controleDevis.current.accepte(version) && setDevis({ ...d, cle: cleDevis })).catch(() => actif && controleDevis.current.accepte(version) && setDevis(null));
    return () => { actif = false; };
  }, [mode, format, dureeClip, son, qualite, cle, langueClient, cleDevis]);

  const occupe = envoi !== null;
  const prete = intention.trim().length > 0 && !occupe && !(mode === 'video' && devisCourant?.code === 'H3_MAX_ANCHOR_UNAVAILABLE');
  const nomImage = etat?.image ?? 'Qwen-Image';

  function choisirLangueClient(langue: LangueClient) {
    if (langueClientRef.current === langue) return;
    langueClientRef.current = langue;
    versionLangueRef.current++;
    requeteIdeesRef.current++;
    requeteBoostRef.current++;
    setLangueClient(langue);
    setIdees((x) => ({ ...x, video: undefined }));
    setBoost(null);
    setCompris(null);
    setVoirPrompt(false);
    setInspire(false);
    if (envoi === 'boost') setEnvoi(null);
  }

  async function inspirer() {
    const versionLangue = versionLangueRef.current;
    const requete = ++requeteIdeesRef.current;
    const langueRequete = langueClientRef.current;
    setInspire(true);
    try {
      if (mode === 'producteur') return;
      const r = await api.nexoraIdees({ mode, theme: intention.trim() || undefined, ...(mode === 'video' ? { langueClient: langueRequete } : {}) });
      if (mode === 'video' && versionLangue !== versionLangueRef.current) return;
      setIdees((x) => ({ ...x, [mode]: r.idees }));
    } catch (e) {
      if (mode === 'video' && versionLangue !== versionLangueRef.current) return;
      const texteCourant = texteCourantCreation();
      toast(mode === 'video' ? erreurVisibleCreationVideo(e, texteCourant.errorIdeas, texteCourant.errorNetwork) : e instanceof Error ? e.message : 'Pas d’idée pour l’instant.', true);
    } finally {
      if (requete === requeteIdeesRef.current) setInspire(false);
    }
  }

  async function booster() {
    if (!intention.trim()) return;
    const versionLangue = versionLangueRef.current;
    const requete = ++requeteBoostRef.current;
    const langueRequete = langueClientRef.current;
    setEnvoi('boost');
    try {
      if (mode === 'producteur') return;
      const r = await api.nexoraAmeliorer({ intention: intention.trim(), mode, ...(mode === 'video' ? { langueClient: langueRequete } : {}) });
      if (mode === 'video' && versionLangue !== versionLangueRef.current) return;
      setBoost(r.texte);
    } catch (e) {
      if (mode === 'video' && versionLangue !== versionLangueRef.current) return;
      const texteCourant = texteCourantCreation();
      toast(mode === 'video' ? erreurVisibleCreationVideo(e, texteCourant.errorBoost, texteCourant.errorNetwork) : e instanceof Error ? e.message : 'Impossible d’améliorer la phrase.', true);
    } finally {
      if (requete === requeteBoostRef.current) setEnvoi(null);
    }
  }

  async function creerVideo() {
    if (envoi !== null || (mode === 'video' && depart === 'photo' && !cle)) return;
    const intentionRequete = intentionRef.current.trim();
    const versionLangue = versionLangueRef.current;
    const langueRequete = langueClientRef.current;
    setEnvoi('creer');
    try {
      const cam = CAMERAS.find((c) => c.id === camera);
      const r = await api.nexoraCreer({ intention: intentionRequete, format, duree: dureeClip as 5 | 10 | 15, son, qualite, image: cle?.jeton, musique, replique: son && replique.trim() ? replique.trim() : undefined, langueReplique, camera: cam?.texte, langueClient: langueRequete });
      const texteCourant = texteCourantCreation();
      toast(r.source === 'llm' ? texteCourant.toastStarted : texteCourant.toastFallbackStarted);
      if (versionLangue === versionLangueRef.current && resumeCorrespondAIntention(intentionRequete, intentionRef.current)) {
        setCompris(r.comprehension ? { ...r.comprehension, credits: r.usageRedaction?.credits, prompt: r.prompt, intentionSource: intentionRequete } : null);
      }
      setVoirPrompt(false);
      setCle(null);
    } catch (e) {
      const texteCourant = texteCourantCreation();
      toast(versionLangue === versionLangueRef.current ? erreurVisibleCreationVideo(e, texteCourant.errorCreate, texteCourant.errorNetwork) : texteCourant.errorCreate, true);
    } finally {
      setEnvoi(null);
    }
  }

  async function dessinerCles() {
    const versionLangue = versionLangueRef.current;
    const langueRequete = langueClientRef.current;
    setEnvoi('cle');
    try {
      await api.nexoraImage({ intention: intention.trim(), format, nombre: nombreImages, qualite, ...(mode === 'video' ? { langueClient: langueRequete } : {}) });
      const texteCourant = texteCourantCreation();
      toast(mode === 'video' ? texteCourant.toastIdeasStarted(nombreImages, nomImage) : `${nombreImages > 1 ? `${nombreImages} plans clés` : 'Un plan clé'} en cours de dessin avec ${nomImage}. Clique « Animer » sur celui que tu préfères.`);
      setFiltre('images');
    } catch (e) {
      const texteCourant = texteCourantCreation();
      toast(mode === 'video' ? versionLangue !== versionLangueRef.current ? texteCourant.errorDrawing : erreurVisibleCreationVideo(e, texteCourant.errorDrawing, texteCourant.errorNetwork) : e instanceof Error ? e.message : 'Le dessin a échoué.', true);
    } finally {
      setEnvoi(null);
    }
  }

  async function proposerDecoupage() {
    setEnvoi('plan');
    try {
      const r = await api.nexoraFilmPlan({ intention: intention.trim(), duree: dureeFilm });
      setStoryboard(r.storyboard);
      if (r.source === 'repli') toast('L’IA n’a pas répondu : découpage simple proposé.', true);
    } catch (e) {
      toast(e instanceof Error ? e.message : 'Le découpage a échoué.', true);
    } finally {
      setEnvoi(null);
    }
  }

  function traiterEchecTournage(e: unknown) {
    if (!(e instanceof EchecFilmPartiel)) {
      toast(e instanceof Error ? e.message : 'Le tournage a échoué.', true);
      return;
    }
    setFilmPartiel(e);
    const ids = e.prises.map((p) => '#' + p.takeId).join(', ');
    let prises = '';
    if (ids) prises = (langueClient === 'en' ? ', shots ' : ', prises ') + ids;
    const detail = langueClient === 'en'
      ? `Film #${e.filmId}${prises}: check their status before retrying.`
      : `Film n° ${e.filmId}${prises} : vérifie leur état avant de réessayer.`;
    toast(`${e.message} ${detail}`, true);
  }

  async function tournerFilm() {
    if (!storyboard) return;
    setEnvoi('film');
    try {
      await api.nexoraFilmTourner({ storyboard, format, son, qualite, intention: intention.trim() });
      toast(`Tournage lancé : ${storyboard.plans.length} plans. Le film s’assemble tout seul à la fin.`);
      setStoryboard(null);
    } catch (e) {
      traiterEchecTournage(e);
    } finally {
      setEnvoi(null);
    }
  }

  async function choisirPhoto(f: File | undefined) {
    if (!f) return;
    if (!f.type.startsWith('image/')) { toast(texteCourantCreation().errorInvalidPhoto, true); return; }
    const epoch = ++handoffEpoch.current;
    setEnvoi('photo');
    setCle(null);
    try {
      const jeton = await uploadFile(f);
      if (epoch !== handoffEpoch.current) return;
      setCle({ jeton, apercu: URL.createObjectURL(f) });
    } catch (e) {
      if (epoch !== handoffEpoch.current) return;
      toast(modeRef.current === 'video' ? texteCourantCreation().errorPhoto : e instanceof Error ? e.message : 'La photo n’a pas pu être envoyée.', true);
    } finally {
      if (epoch === handoffEpoch.current) setEnvoi(null);
    }
  }

  async function animer(id: number, route?: string) {
    setMode('video');
    const epoch = ++handoffEpoch.current;
    const routeCible = route ?? `${location.pathname}${location.search}`;
    const courant = () => isCurrentVideoHandoff(epoch, handoffEpoch.current, routeCible, `${location.pathname}${location.search}`);
    setEnvoi('prise');
    setCle(null);
    setDepart('cle');
    try {
      const { jeton } = await api.nexoraImageJeton(id);
      if (!courant()) return;
      setCle({ jeton, apercu: posterUrl(id) });
      toast(texteCourantCreation().toastKeyReady);
    } catch (e) {
      if (!courant()) return;
      toast(modeRef.current === 'video' ? texteCourantCreation().errorUseImage : e instanceof Error ? e.message : 'Impossible d’utiliser cette image.', true);
    } finally {
      if (epoch === handoffEpoch.current) setEnvoi(null);
    }
  }

  function majPlan(i: number, patch: Partial<Storyboard['plans'][number]>) {
    if (!storyboard) return;
    const plans = storyboard.plans.map((p, k) => (k === i ? { ...p, ...patch } : p));
    setStoryboard({ ...storyboard, plans, dureeTotale: plans.reduce((n, p) => n + p.duree, 0) });
  }
  function retirerPlan(i: number) {
    if (!storyboard || storyboard.plans.length <= 1) return;
    const plans = storyboard.plans.filter((_, k) => k !== i);
    setStoryboard({ ...storyboard, plans, dureeTotale: plans.reduce((n, p) => n + p.duree, 0) });
  }

  const cleRequise = mode === 'video' && depart === 'cle' && !cle;
  const photoRequise = mode === 'video' && depart === 'photo' && !cle;
  const libelle = envoi === 'creer' ? (mode === 'video' ? texteVideo.writingScenario : 'L’IA écrit le scénario…')
    : envoi === 'plan' ? 'L’IA découpe ton film…'
      : envoi === 'cle' ? (mode === 'video' ? texteVideo.drawing : 'Dessin en cours…')
        : envoi === 'prise' ? texteVideo.preparingKeyFrame
        : mode === 'image' ? `Dessiner ${nombreImages > 1 ? `${nombreImages} images` : 'l’image'}`
          : film ? 'Proposer le découpage'
            : cleRequise ? texteVideo.drawKeyFrameCount(nombreImages) : cle ? texteVideo.animate : texteVideo.createVideo;
  function lancer() {
    if (photoRequise) return;
    if (mode === 'image') void dessinerCles();
    else if (film) void proposerDecoupage();
    else if (cleRequise) void dessinerCles();
    else void creerVideo();
  }
  const minutesFilm = storyboard ? Math.ceil((storyboard.plans.reduce((n, p) => n + (p.duree === 10 ? 2 : 1), 0) * SECONDES_PAR_PLAN_5S) / 60) : 0;

  return (
    <div className="st" lang={langueActive === 'en' ? 'en-CA' : 'fr-CA'}>
      <section className="st-hero">
        <div>
          <h1>{mode === 'video' ? texteVideo.title : <>Écris-le. <em>Nexora</em> le filme.</>}</h1>
          <p>{mode === 'producteur'
            ? 'Dis ce que tu veux produire. Le Producteur IA découpe, chiffre, tourne, contrôle chaque plan et assemble. Tu valides le devis d’un clic.'
            : mode === 'video' ? texteVideo.intro : 'Une phrase en français suffit. L’IA écrit le scénario, dessine le plan clé, tourne avec son et compose la musique.'}</p>
        </div>
        <div className="st-pile" aria-label={langueActive === 'en' ? texteVideo.models : 'Modèles utilisés'}>
          <span>{texteVideo.modelVideo} <b>MiniMax H3</b></span>
          <span>{texteVideo.modelImage} <b>{etat?.image ?? 'Qwen-Image'}</b></span>
          <span>{texteVideo.modelMusic} <b>MiniMax-Music3</b></span>
        </div>
      </section>

      <div className="st-modes st-modes-haut" role="tablist" aria-label={langueActive === 'en' ? texteVideo.tabs : 'Que veux-tu créer ?'}>
        {([['producteur', 'Producteur IA', IcEtincelle], ['video', 'Vidéo', IcVideo], ['image', 'Image', IcImage], ['film', 'Film', IcFilm]] as const).map(([v, label, Ic]) => {
          const modeLabel = langueActive === 'en'
            ? v === 'producteur' ? texteVideo.tabProducer : v === 'video' ? texteVideo.tabVideo : v === 'image' ? texteVideo.tabImage : texteVideo.tabFilm
            : label;
          return (
          <button key={v} type="button" role="tab" aria-selected={mode === v} className={`st-mode ${mode === v ? 'on' : ''} ${v === 'producteur' ? 'st-mode-agent' : ''}`} onClick={() => { setMode(v); setStoryboard(null); setBoost(null); }}>
            <Ic />{modeLabel}
          </button>
        );})}
      </div>

      {mode === 'producteur' ? (
        <div className="st-grid"><Producteur onOuvrirFilm={setFilmOuvert} objectif={params.get('objectif')} /></div>
      ) : (
      <div className="st-grid">
        <aside className="st-composer" aria-label={langueActive === 'en' ? texteVideo.composer : 'Composeur'}>

          {mode === 'video' && (
            <div className="st-bloc">
              <span className="st-etiq">{texteVideo.language}</span>
              <div className="st-seg" role="group" aria-label={texteVideo.language}>
                <button type="button" className={langueClient === 'fr' ? 'on' : ''} aria-pressed={langueClient === 'fr'} onClick={() => choisirLangueClient('fr')}>Français</button>
                <button type="button" className={langueClient === 'en' ? 'on' : ''} aria-pressed={langueClient === 'en'} onClick={() => choisirLangueClient('en')}>English</button>
              </div>
            </div>
          )}

          <div className="st-champ">
            <textarea
              value={intention}
              onChange={(e) => changerIntention(e.target.value)}
              onKeyDown={(e) => { if ((e.ctrlKey || e.metaKey) && e.key === 'Enter' && prete && !cleRequise && !photoRequise) lancer(); }}
              placeholder={mode === 'video' ? texteVideo.placeholder : mode === 'image' ? 'Décris l’image : sujet, décor, lumière, ambiance…' : mode === 'film' ? 'Raconte ton film : une idée, des personnages, une ambiance…' : 'Décris ta scène : ce qu’on voit, ce qui bouge, la caméra…'}
              maxLength={4000}
              aria-label={mode === 'video' ? texteVideo.description : 'Description'}
            />
            <div className="st-champ-pied">
              <span>{intention.length}/4000 · {mode === 'video' ? texteVideo.count : 'Ctrl+Entrée pour lancer'}</span>
              <button type="button" className={`st-boost ${envoi === 'boost' ? 'charge' : ''}`} disabled={!intention.trim() || occupe} onClick={() => void booster()} title={mode === 'video' ? texteVideo.boostTitle : 'L’assistant réécrit ta phrase en version plus riche et plus filmable'}>
                {envoi === 'boost' ? <IcRond /> : <IcEtincelle />}{mode === 'video' ? texteVideo.boost : 'Booster ma phrase'}
              </button>
            </div>
          </div>

          {boost && (
            <div className="st-suggestion" role="status">
              <span className="st-etiq">{mode === 'video' ? texteVideo.boosted : 'Version boostée'}</span>
              <p>{boost}</p>
              <div className="st-ligne">
                <button type="button" className="st-bouton primaire" onClick={() => { changerIntention(boost); setBoost(null); }}>{mode === 'video' ? texteVideo.useBoost : 'Utiliser cette version'}</button>
                <button type="button" className="st-bouton" onClick={() => setBoost(null)}>{mode === 'video' ? texteVideo.keepOriginal : 'Garder la mienne'}</button>
              </div>
            </div>
          )}

          {compris && mode === 'video' && resumeCorrespondAIntention(compris.intentionSource, intention) && (
            <div className="st-suggestion st-compris" role="status" aria-live="polite">
              <span className="st-etiq">{texteVideo.understood}</span>
              <p>{compris.compris}</p>
              {compris.plans.length > 1 && <p className="st-compris-plans" aria-label={texteVideo.planList}>{compris.plans.map((p, i) => `${i + 1}. ${p.cadrage} (${langueActive === 'fr' ? p.debut.toFixed(1).replace('.', ',') : p.debut.toFixed(1)} s)`).join('  ·  ')}</p>}
              {compris.hypotheses.length > 0 && (
                <ul className="st-compris-choix" aria-label={texteVideo.choices}>{compris.hypotheses.map((h) => <li key={h}>{h}</li>)}</ul>
              )}
              {compris.variantes.length > 0 && (
                <div className="st-compris-variantes">
                  <span className="st-etiq">{texteVideo.directions}</span>
                  <div className="st-idees">{compris.variantes.map((v) => <button key={v} type="button" className="st-idee" title={texteVideo.useDirection} onClick={() => { changerIntention(`${intention.trim()} — ${v}`); setCompris(null); }}>{v}</button>)}</div>
                </div>
              )}
              <div className="st-ligne">
                <button type="button" className="st-bouton" onClick={() => setVoirPrompt((x) => !x)}>{voirPrompt ? texteVideo.hidePrompt : texteVideo.viewPrompt}</button>
                <button type="button" className="st-bouton" onClick={() => setCompris(null)}>{texteVideo.close}</button>
                {compris.credits != null && compris.credits > 0 && <span className="st-credit">{compris.credits === 1 ? texteVideo.writingOne : texteVideo.writingMany(compris.credits)}</span>}
              </div>
              {voirPrompt && <pre className="st-compris-prompt">{compris.prompt}</pre>}
            </div>
          )}

          {(!intention || idees[mode]) && (
            <div className="st-idees" aria-label={mode === 'video' ? texteVideo.ideas : 'Idées'}>
              {(idees[mode] ?? (mode === 'video' ? texteVideo.ideaExamples : IDEES[mode])).map((i) => <button key={i} type="button" className="st-idee" onClick={() => changerIntention(i)}>{i.length > 72 ? `${i.slice(0, 70)}…` : i}</button>)}
              <button type="button" className="st-idee" disabled={inspire} onClick={() => void inspirer()} style={{ borderColor: 'rgba(255,90,31,.45)', color: 'var(--accent-hi)' }}>{inspire ? texteVideo.searching : texteVideo.inspire}</button>
            </div>
          )}

          {mode === 'video' && (
            <div className="st-bloc">
              <span className="st-etiq">{texteVideo.departure}</span>
              <div className="st-seg" role="group" aria-label={texteVideo.startPoint}>
                {([['texte', texteVideo.textOnly, texteVideo.h3Imagines], ['photo', texteVideo.photo, texteVideo.import], ['cle', texteVideo.keyFrame, nomImage]] as const).map(([v, label, sub]) => (
                  <button key={v} type="button" className={depart === v ? 'on' : ''} onClick={() => changerDepart(v)}>{label}<small>{sub}</small></button>
                ))}
              </div>
              {depart === 'photo' && !cle && (
                <>
                  <label className="st-bouton" style={{ textAlign: 'center', cursor: 'pointer' }}>
                    {envoi === 'photo' ? texteVideo.uploadingPhoto : texteVideo.choosePhoto}
                    <input type="file" accept="image/*" hidden onChange={(e) => void choisirPhoto(e.target.files?.[0])} />
                  </label>
                  {envoi !== 'photo' && <span className="st-credit" role="status" style={{ textAlign: 'left' }}>{texteVideo.photoRequired}</span>}
                </>
              )}
              {cle && (
                <div className="st-cle">
                  <img src={cle.apercu} alt={texteVideo.startImageAlt} />
                  <span>{texteVideo.startsFromImage}</span>
                  <button type="button" className="st-bouton" onClick={() => { setCle(null); }}>{texteVideo.remove}</button>
                </div>
              )}
              {depart === 'cle' && !cle && <span className="st-credit" style={{ textAlign: 'left' }}>{texteVideo.keyFrameHint}</span>}
            </div>
          )}

          {mode === 'video' && (
            <div className="st-bloc">
              <span className="st-etiq">{texteVideo.cameraMove} {camera && <button type="button" className="nx-lien" style={{ fontSize: 11, marginLeft: 6 }} onClick={() => setCamera(null)}>{texteVideo.remove.toLowerCase()}</button>}</span>
              <div className="st-cameras" role="group" aria-label={texteVideo.cameraAria}>
                {CAMERAS.map((c) => (
                  <button key={c.id} type="button" className={`st-camera ${camera === c.id ? 'on' : ''}`} aria-pressed={camera === c.id} onClick={() => setCamera(camera === c.id ? null : c.id)} title={nomCameraCreation(langueActive, c.id, c.nom)}>
                    <video src={c.clip} muted loop playsInline preload="metadata" onMouseEnter={(e) => void e.currentTarget.play().catch(() => {})} onMouseLeave={(e) => e.currentTarget.pause()} />
                    <span>{nomCameraCreation(langueActive, c.id, c.nom)}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className="st-bloc">
            <span className="st-etiq">{texteVideo.format}</span>
            <div className="st-seg" role="group" aria-label={texteVideo.formatAria}>
              {FORMATS.map((f) => (
                <button key={f.v} type="button" className={format === f.v ? 'on' : ''} onClick={() => setFormat(f.v)}><Ratio v={f.v} />{f.v === '16:9' ? texteVideo.landscape : f.v === '9:16' ? texteVideo.vertical : texteVideo.square}<small>{f.v === '16:9' ? texteVideo.landscapeHelp : f.v === '9:16' ? texteVideo.verticalHelp : texteVideo.squareHelp}</small></button>
              ))}
            </div>
          </div>

          {mode === 'video' && (
            <div className="st-bloc">
              <span className="st-etiq">{texteVideo.duration}</span>
              <div className="st-seg" role="group" aria-label={texteVideo.duration}>
                {DUREES_VIDEO.map((d) => <button key={d} type="button" className={duree === d ? 'on' : ''} onClick={() => setDuree(d)}>{d} s</button>)}
              </div>
            </div>
          )}
          {film && (
            <div className="st-bloc">
              <span className="st-etiq">Durée du film</span>
              <div className="st-seg" role="group" aria-label="Durée du film">
                {DUREES_FILM.map((d) => <button key={d.v} type="button" className={dureeFilm === d.v ? 'on' : ''} onClick={() => { setDureeFilm(d.v); setStoryboard(null); }}>{d.label}</button>)}
              </div>
            </div>
          )}
          {mode === 'image' && (
            <div className="st-bloc">
              <span className="st-etiq">Nombre d’images</span>
              <div className="st-seg" role="group" aria-label="Nombre d’images">
                {[1, 2, 4].map((n) => <button key={n} type="button" className={nombreImages === n ? 'on' : ''} onClick={() => setNombreImages(n)}>{n}</button>)}
              </div>
            </div>
          )}

          {mode !== 'image' && (
            <div className="st-bloc">
              <span className="st-etiq">{texteVideo.quality}</span>
              <div className="st-seg" role="group" aria-label={texteVideo.quality}>
                <button type="button" className={qualite === 'rapide' ? 'on' : ''} onClick={() => setQualite('rapide')}>{texteVideo.fast}<small>FastH3 · 832×480</small></button>
                <button type="button" className={qualite === 'max' ? 'on' : ''} onClick={() => setQualite('max')}>{etat?.cinema ? texteVideo.cinema : texteVideo.maxQuality}<small>{etat?.cinema ? `${texteVideo.fullH3} · 768p` : '1344×768'}</small></button>
              </div>
            </div>
          )}
          {mode === 'image' && (
            <div className="st-bloc">
              <span className="st-etiq">Qualité</span>
              <div className="st-seg" role="group" aria-label="Qualité de l’image">
                <button type="button" className={qualite === 'rapide' ? 'on' : ''} onClick={() => setQualite('rapide')}>Brouillon<small>12 étapes</small></button>
                <button type="button" className={qualite === 'max' ? 'on' : ''} onClick={() => setQualite('max')}>Maximale<small>25 étapes</small></button>
              </div>
            </div>
          )}

          {mode === 'video' && son && (
            <div className="st-bloc">
              <span className="st-etiq">{texteVideo.reply}</span>
              <div className="st-seg" role="group" aria-label={texteVideo.replyLanguage}>
                <button type="button" className={langueReplique === 'fr' ? 'on' : ''} aria-pressed={langueReplique === 'fr'} onClick={() => setLangueReplique('fr')}>{texteVideo.replyFrench}</button>
                <button type="button" className={langueReplique === 'en' ? 'on' : ''} aria-pressed={langueReplique === 'en'} onClick={() => setLangueReplique('en')}>{texteVideo.replyEnglish}</button>
              </div>
              <input className="st-champ-ligne" value={replique} maxLength={300} onChange={(e) => setReplique(e.target.value)} placeholder={texteVideo.replyPlaceholder} aria-label={texteVideo.replyAria} />
            </div>
          )}

          {mode !== 'image' && (
            <div className="st-interrupteurs">
              <button type="button" className="st-inter" aria-pressed={son} onClick={() => setSon(!son)}><span>{texteVideo.sound}<small>{texteVideo.soundDetail}</small></span><i /></button>
              {mode === 'video' && (
                <button type="button" className="st-inter" aria-pressed={musique} onClick={() => setMusique(!musique)} disabled={!etat?.musique} title={etat?.musique ? '' : texteVideo.musicUnavailable}>
                  <span>{texteVideo.music}<small>{texteVideo.musicDetail}</small></span><i />
                </button>
              )}
            </div>
          )}


          <div className="st-cta">
            <button type="button" className="st-go" disabled={!prete || photoRequise} onClick={lancer}>{libelle}</button>
            {mode === 'video' && devisCourant?.code === 'H3_MAX_ANCHOR_UNAVAILABLE' && <p className="st-credit" role="alert">{devisCourant.erreur}</p>}
            {mode === 'video' && devisCourant && devisCourant.secondesEstimees != null && !cleRequise && (
              <div className="st-devis">
                <span>{texteVideo.estimate} <b>{fmtTemps(devisCourant.secondesEstimees, langueActive)}</b></span>
                <span>{qualite === 'max' && etat?.cinema ? texteVideo.fullH3 : texteVideo.fastH3} · RTX 5090{devisCourant.credits !== null ? ` · ${texteVideo.creditUnit(devisCourant.credits)}` : ''}</span>
              </div>
            )}
            {mode === 'image' && <div className="st-devis"><span>{nomImage} · DGX Spark GB10</span><span>≈ {qualite === 'max' ? '50 s' : '25 s'} par image</span></div>}
            <p className="st-credit">{mode === 'video' ? texteVideo.powered : 'Propulsé par MiniMax H3'} · {etat?.image ?? 'Qwen-Image'} · MiniMax-Music3</p>
          </div>
        </aside>

        <section className="st-galerie" aria-label={mode === 'video' ? texteVideo.galleryAria : 'Tes créations'}>
          {storyboard && (
            <div className="st-decoupage">
              <div className="nx-sb-tete">
                <div>
                  <h2>{storyboard.titre}</h2>
                  <p className="nx-sous" style={{ margin: 0 }}>{storyboard.plans.length} plans · {storyboard.dureeTotale} s · tournage ≈ {minutesFilm} min. Retouche ce qui ne te plaît pas, puis lance.</p>
                </div>
                <div className="st-ligne">
                  <button type="button" className="st-bouton" disabled={!!filmPartiel} onClick={() => setStoryboard(null)}>Annuler</button>
                  <button type="button" className="st-bouton primaire" disabled={occupe || !!filmPartiel} onClick={() => void tournerFilm()}>{envoi === 'film' ? 'Lancement…' : 'Tourner le film'}</button>
                </div>
              </div>
              {filmPartiel && <FilmPartielAlerte erreur={filmPartiel} langue={langueClient} rafraichir={refreshTakes}
                existe={(id) => getState().takes.some((t) => t.id === id)} ouvrirFilm={setFilmOuvert} ouvrirPrise={setVue}
                indisponible={() => toast(langueClient === 'en' ? 'This item is not available. Try refreshing later.' : 'Cet élément est indisponible. Réessaie plus tard.', true)}
                nouveauFilm={() => { setFilmPartiel(null); setStoryboard(null); changerIntention(''); }} />}
              <details className="nx-bible">
                <summary>Bible de continuité (style, personnages, lieux)</summary>
                <p><strong>Style :</strong> {storyboard.bible.style}</p>
                {storyboard.bible.personnages.map((p) => <p key={p.nom}><strong>{p.nom} :</strong> {p.description}</p>)}
                {storyboard.bible.lieux.map((l) => <p key={l.nom}><strong>{l.nom} :</strong> {l.description}</p>)}
              </details>
              <ol className="nx-plans">
                {storyboard.plans.map((p, i) => (
                  <li key={i} className="nx-plan">
                    <div className="nx-plan-num">{i + 1}</div>
                    <div className="nx-plan-corps">
                      <input value={p.resume} onChange={(e) => majPlan(i, { resume: e.target.value })} aria-label={`Titre du plan ${i + 1}`} />
                      <textarea rows={3} value={p.description} onChange={(e) => majPlan(i, { description: e.target.value })} aria-label={`Description du plan ${i + 1}`} />
                      <div className="nx-plan-pied">
                        <span className="nx-camera">{p.camera}</span>
                        <button type="button" className={`nx-puce ${p.duree === 5 ? 'on' : ''}`} onClick={() => majPlan(i, { duree: 5 })}>5 s</button>
                        <button type="button" className={`nx-puce ${p.duree === 10 ? 'on' : ''}`} onClick={() => majPlan(i, { duree: 10 })}>10 s</button>
                        <button type="button" className="nx-lien" onClick={() => retirerPlan(i)} disabled={storyboard.plans.length <= 1}>Retirer</button>
                      </div>
                    </div>
                  </li>
                ))}
              </ol>
            </div>
          )}

          <div className="st-g-tete">
            <h2>{mode === 'video' ? texteVideo.creations : 'Tes créations'}</h2>
            <div className="st-filtres" role="group" aria-label={mode === 'video' ? texteVideo.filter : 'Filtrer'}>
              {([['tout', mode === 'video' ? texteVideo.all : 'Tout'], ['videos', mode === 'video' ? texteVideo.videos : 'Vidéos'], ['films', mode === 'video' ? texteVideo.films : 'Films'], ['images', mode === 'video' ? texteVideo.images : 'Images']] as const).map(([v, label]) => (
                <button key={v} type="button" className={filtre === v ? 'on' : ''} onClick={() => setFiltre(v)}>{label}</button>
              ))}
            </div>
          </div>

          {montrees.length === 0 ? (
            <div className="st-vide">
              <div className="st-mosaique" aria-hidden>
                {Array.from({ length: 18 }, (_, i) => <i key={i} style={{ opacity: [1, 0.15, 0.6, 0.3, 0.9, 0.2][(i * 5) % 6] }} />)}
              </div>
              <strong>{mode === 'video' ? texteVideo.emptyTitle : 'Ta première scène t’attend.'}</strong>
              <span>{mode === 'video' ? texteVideo.emptyDescription : 'Écris une idée à gauche, ou pars d’un exemple. Les vidéos, images et films apparaîtront ici, avec leur progression en direct.'}</span>
            </div>
          ) : (
            <div className="st-cartes">
              {montrees.map((t) => {
                const s = settingsOf(t);
                const plans = s.film ? ((s.storyboard?.plans ?? []) as { take?: number }[]) : [];
                const faits = plans.filter((p) => p.take && toutes.find((x) => x.id === p.take)?.status === 'done').length;
                const image = isImage(t);
                const actions = t.status !== 'done' ? undefined : s.film ? (
                  <div className="st-actions-carte"><button type="button" onClick={() => setFilmOuvert(t.id)}>{mode === 'video' ? texteVideo.openPlans : 'Plans et montage'}</button></div>
                ) : image ? (
                  <div className="st-actions-carte">
                    <button type="button" onClick={() => void animer(t.id)}>{mode === 'video' ? texteVideo.animate : 'Animer avec H3'}</button>
                    <a href={mediaUrl(t.id)} download>{mode === 'video' ? texteVideo.download : 'Télécharger'}</a>
                  </div>
                ) : (
                  <div className="st-actions-carte">
                    {!s.nexoraAvecMusique && !s.nexoraMusiqueLance && etat?.musique && (
                      <button type="button" onClick={() => { api.nexoraClipMusique(t.id, {}).then(() => toast(mode === 'video' ? texteVideo.toastMusicStarted : 'Composition de la musique lancée (moins d’une minute).')).catch((e) => toast(mode === 'video' ? texteVideo.errorMusic : e instanceof Error ? e.message : 'Impossible de composer la musique.', true)); }}>{mode === 'video' ? texteVideo.addMusic : 'Ajouter une musique'}</button>
                    )}
                    <button type="button" onClick={() => setPub(t.id)}>{mode === 'video' ? texteVideo.socialText : 'Texte réseaux'}</button>
                    <a href={mediaUrl(t.id)} download>{mode === 'video' ? texteVideo.download : 'Télécharger'}</a>
                  </div>
                );
                return (
                  <MediaCard key={t.id} take={t} onOpen={() => (s.film ? setFilmOuvert(t.id) : setVue(t.id))}
                    tag={s.film ? (mode === 'video' ? texteVideo.filmTag : 'Film') : s.nexoraAvecMusique ? (mode === 'video' ? texteVideo.musicTag : '+ musique') : image ? (mode === 'video' ? texteVideo.imageTag : 'Image') : undefined}
                    pendingLabel={s.film ? (mode === 'video' ? texteVideo.filmProgress(faits, plans.length) : `Film : ${faits}/${plans.length} plans tournés`) : mode === 'video' ? texteVideo.queued : 'En file d’attente'}
                    actions={actions} />
                );
              })}
            </div>
          )}
        </section>
      </div>
      )}

      {pub !== null && <Publication id={pub} onClose={() => setPub(null)} />}
      {filmOuvert !== null && <FilmPlans filmId={filmOuvert} onClose={() => setFilmOuvert(null)} />}
      {vue !== null && <Viewer takeId={vue} onClose={() => setVue(null)} onStep={(d) => {
        const n = ids[ids.indexOf(vue) + d];
        if (n !== undefined) setVue(n);
      }} />}
    </div>
  );
}
