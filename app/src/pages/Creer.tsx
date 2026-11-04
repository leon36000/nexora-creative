/**
 * Nexora Creative — le studio « Créer ».
 * À gauche, le composeur : une idée en français, un bouton « Booster ma phrase » (le LLM la rend plus riche et plus filmable),
 * trois modes (Vidéo, Image, Film), un départ facultatif (ta photo ou un plan clé dessiné par Qwen-Image) et la musique
 * MiniMax en option. À droite, les créations en direct : progression, aperçu, musique, animation d'un plan clé.
 * Vidéo : le LLM écrit le scénario H3 et MiniMax H3 tourne (RTX 5090). Image : Qwen-Image (GB10). Film : l'AI Director
 * propose un découpage relisible, tourne chaque plan et assemble.
 */
import { useEffect, useMemo, useRef, useState } from 'react';
import { api, mediaUrl, posterUrl, uploadFile, type Comprehension, type EtatNexora, type Storyboard } from '../api';
import { inFeed, isImage, isModel, settingsOf, toast, useStore } from '../store';
import { MediaCard } from '../ui';
import Viewer from '../Viewer';
import FilmPlans from '../FilmPlans';
import { Publication } from '../studio/Publication';
import Producteur from '../studio/Producteur';
import { CAMERAS } from '../studio/apps';
import { setParams, useRoute } from '../router';
import { IcEtincelle, IcFilm, IcImage, IcRond, IcVideo, Ratio } from '../studio/icons';

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

const fmtTemps = (s: number) => (s < 90 ? `${Math.round(s)} s` : `${Math.floor(s / 60)} min ${String(Math.round(s % 60)).padStart(2, '0')} s`);

export default function Creer() {
  const { params } = useRoute();
  const mode: Mode = MODES.includes(params.get('mode') as Mode) ? (params.get('mode') as Mode) : 'producteur';
  const setMode = (m: Mode) => setParams({ mode: m === 'producteur' ? null : m });
  const [intention, setIntention] = useState('');
  const [format, setFormat] = useState<Format>('16:9');
  const [duree, setDuree] = useState<number>(5);
  const [dureeFilm, setDureeFilm] = useState<number>(30);
  const [son, setSon] = useState(true);
  const [musique, setMusique] = useState(false);
  const [qualite, setQualite] = useState<'rapide' | 'max'>('rapide');
  const [nombreImages, setNombreImages] = useState(2);
  const [depart, setDepart] = useState<Depart>(() => (params.get('depart') === 'photo' ? 'photo' : 'texte'));
  const [camera, setCamera] = useState<string | null>(null);
  const [cle, setCle] = useState<{ jeton: string; apercu: string } | null>(null);
  const [envoi, setEnvoi] = useState<null | 'creer' | 'plan' | 'film' | 'cle' | 'boost' | 'photo'>(null);
  const [boost, setBoost] = useState<string | null>(null);
  const [compris, setCompris] = useState<(Comprehension & { credits?: number; prompt: string }) | null>(null);
  const [voirPrompt, setVoirPrompt] = useState(false);
  const [storyboard, setStoryboard] = useState<Storyboard | null>(null);
  const [etat, setEtat] = useState<EtatNexora | null>(null);
  const [vue, setVue] = useState<number | null>(null);
  const [filmOuvert, setFilmOuvert] = useState<number | null>(null);
  const [filtre, setFiltre] = useState<Filtre>('tout');
  const [replique, setReplique] = useState('');
  const [pub, setPub] = useState<number | null>(null);
  const [idees, setIdees] = useState<Partial<Record<Exclude<Mode, 'producteur'>, string[]>>>({});
  const [inspire, setInspire] = useState(false);
  const [devis, setDevis] = useState<{ credits: number | null; secondesEstimees: number | null } | null>(null);
  const toutes = useStore((s) => s.takes);
  const lances = useRef(new Set<number>());
  const jetonsRecus = useRef(new Set<string>());

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
      api.nexoraClipAvecMusique(clip, m.id).then(() => toast('Ta vidéo avec sa musique est prête.')).catch((e) => toast(e instanceof Error ? e.message : 'Le mixage de la musique a échoué.', true));
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
    if (texte) setIntention(texte.slice(0, 4000));
    toast('Vue 3D posée comme plan clé : ajuste la description puis lance « Animer avec H3 ».');
  }, [params.get('jeton')]);
  // « Animer » depuis la Bibliothèque : /?mode=video&cle=<image> pose l'image comme plan clé.
  useEffect(() => {
    const id = Number(params.get('cle'));
    if (!id) return;
    setParams({ cle: null });
    void animer(id);
  }, [params.get('cle')]);
  const film = mode === 'film';
  const dureeClip = duree;
  useEffect(() => {
    if (mode !== 'video') { setDevis(null); return; }
    let actif = true;
    void api.nexoraDevis({ format, duree: dureeClip, son, qualite, image: cle?.jeton }).then((d) => actif && setDevis(d)).catch(() => actif && setDevis(null));
    return () => { actif = false; };
  }, [mode, format, dureeClip, son, qualite, cle]);

  const occupe = envoi !== null;
  const prete = intention.trim().length > 0 && !occupe;
  const nomImage = etat?.image ?? 'Qwen-Image';

  async function inspirer() {
    setInspire(true);
    try {
      if (mode === 'producteur') return;
      const r = await api.nexoraIdees({ mode, theme: intention.trim() || undefined });
      setIdees((x) => ({ ...x, [mode]: r.idees }));
    } catch (e) {
      toast(e instanceof Error ? e.message : 'Pas d’idée pour l’instant.', true);
    } finally {
      setInspire(false);
    }
  }

  async function booster() {
    if (!intention.trim()) return;
    setEnvoi('boost');
    try {
      if (mode === 'producteur') return;
      const r = await api.nexoraAmeliorer({ intention: intention.trim(), mode });
      setBoost(r.texte);
    } catch (e) {
      toast(e instanceof Error ? e.message : 'Impossible d’améliorer la phrase.', true);
    } finally {
      setEnvoi(null);
    }
  }

  async function creerVideo() {
    setEnvoi('creer');
    try {
      const cam = CAMERAS.find((c) => c.id === camera);
      const r = await api.nexoraCreer({ intention: intention.trim(), format, duree: dureeClip as 5 | 10 | 15, son, qualite, image: cle?.jeton, musique, replique: son && replique.trim() ? replique.trim() : undefined, camera: cam?.texte });
      toast(r.source === 'llm' ? 'Scénario écrit, tournage lancé.' : 'Tournage lancé (scénario simplifié : l’assistant est indisponible).');
      setCompris(r.comprehension ? { ...r.comprehension, credits: r.usageRedaction?.credits, prompt: r.prompt } : null);
      setVoirPrompt(false);
      setCle(null);
    } catch (e) {
      toast(e instanceof Error ? e.message : 'La création a échoué.', true);
    } finally {
      setEnvoi(null);
    }
  }

  async function dessinerCles() {
    setEnvoi('cle');
    try {
      await api.nexoraImage({ intention: intention.trim(), format, nombre: nombreImages, qualite });
      toast(`${nombreImages > 1 ? `${nombreImages} plans clés` : 'Un plan clé'} en cours de dessin avec ${nomImage}. Clique « Animer » sur celui que tu préfères.`);
      setFiltre('images');
    } catch (e) {
      toast(e instanceof Error ? e.message : 'Le dessin a échoué.', true);
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

  async function tournerFilm() {
    if (!storyboard) return;
    setEnvoi('film');
    try {
      await api.nexoraFilmTourner({ storyboard, format, son, qualite, intention: intention.trim() });
      toast(`Tournage lancé : ${storyboard.plans.length} plans. Le film s’assemble tout seul à la fin.`);
      setStoryboard(null);
    } catch (e) {
      toast(e instanceof Error ? e.message : 'Le tournage a échoué.', true);
    } finally {
      setEnvoi(null);
    }
  }

  async function choisirPhoto(f: File | undefined) {
    if (!f) return;
    if (!f.type.startsWith('image/')) { toast('Choisis une image (JPG, PNG ou WebP).', true); return; }
    setEnvoi('photo');
    try {
      const jeton = await uploadFile(f);
      setCle({ jeton, apercu: URL.createObjectURL(f) });
    } catch (e) {
      toast(e instanceof Error ? e.message : 'La photo n’a pas pu être envoyée.', true);
    } finally {
      setEnvoi(null);
    }
  }

  async function animer(id: number) {
    try {
      const { jeton } = await api.nexoraImageJeton(id);
      setCle({ jeton, apercu: posterUrl(id) });
      setMode('video');
      setDepart('cle');
      toast('Plan clé prêt : choisis la durée puis lance « Animer avec H3 ».');
    } catch (e) {
      toast(e instanceof Error ? e.message : 'Impossible d’utiliser cette image.', true);
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
  const libelle = envoi === 'creer' ? 'L’IA écrit le scénario…'
    : envoi === 'plan' ? 'L’IA découpe ton film…'
      : envoi === 'cle' ? 'Dessin en cours…'
        : mode === 'image' ? `Dessiner ${nombreImages > 1 ? `${nombreImages} images` : 'l’image'}`
          : film ? 'Proposer le découpage'
            : cleRequise ? `Dessiner ${nombreImages} plans clés` : cle ? 'Animer avec H3' : 'Créer la vidéo';
  function lancer() {
    if (mode === 'image') void dessinerCles();
    else if (film) void proposerDecoupage();
    else if (cleRequise) void dessinerCles();
    else void creerVideo();
  }
  const minutesFilm = storyboard ? Math.ceil((storyboard.plans.reduce((n, p) => n + (p.duree === 10 ? 2 : 1), 0) * SECONDES_PAR_PLAN_5S) / 60) : 0;

  return (
    <div className="st">
      <section className="st-hero">
        <div>
          <h1>Écris-le. <em>Nexora</em> le filme.</h1>
          <p>{mode === 'producteur'
            ? 'Dis ce que tu veux produire. Le Producteur IA découpe, chiffre, tourne, contrôle chaque plan et assemble. Tu valides le devis d’un clic.'
            : 'Une phrase en français suffit. L’IA écrit le scénario, dessine le plan clé, tourne avec son et compose la musique.'}</p>
        </div>
        <div className="st-pile" aria-label="Modèles utilisés">
          <span>Vidéo <b>MiniMax H3</b></span>
          <span>Image <b>{etat?.image ?? 'Qwen-Image'}</b></span>
          <span>Musique <b>MiniMax-Music3</b></span>
        </div>
      </section>

      <div className="st-modes st-modes-haut" role="tablist" aria-label="Que veux-tu créer ?">
        {([['producteur', 'Producteur IA', IcEtincelle], ['video', 'Vidéo', IcVideo], ['image', 'Image', IcImage], ['film', 'Film', IcFilm]] as const).map(([v, label, Ic]) => (
          <button key={v} type="button" role="tab" aria-selected={mode === v} className={`st-mode ${mode === v ? 'on' : ''} ${v === 'producteur' ? 'st-mode-agent' : ''}`} onClick={() => { setMode(v); setStoryboard(null); setBoost(null); }}>
            <Ic />{v === 'producteur' ? <>Producteur<span className="st-ia"> IA</span></> : label}
          </button>
        ))}
      </div>

      {mode === 'producteur' ? (
        <div className="st-grid"><Producteur onOuvrirFilm={setFilmOuvert} objectif={params.get('objectif')} /></div>
      ) : (
      <div className="st-grid">
        <aside className="st-composer" aria-label="Composeur">

          <div className="st-champ">
            <textarea
              value={intention}
              onChange={(e) => setIntention(e.target.value)}
              onKeyDown={(e) => { if ((e.ctrlKey || e.metaKey) && e.key === 'Enter' && prete && !cleRequise) lancer(); }}
              placeholder={mode === 'image' ? 'Décris l’image : sujet, décor, lumière, ambiance…' : mode === 'film' ? 'Raconte ton film : une idée, des personnages, une ambiance…' : 'Décris ta scène : ce qu’on voit, ce qui bouge, la caméra…'}
              maxLength={4000}
              aria-label="Description"
            />
            <div className="st-champ-pied">
              <span>{intention.length}/4000 · Ctrl+Entrée pour lancer</span>
              <button type="button" className={`st-boost ${envoi === 'boost' ? 'charge' : ''}`} disabled={!intention.trim() || occupe} onClick={() => void booster()} title="L’assistant réécrit ta phrase en version plus riche et plus filmable">
                {envoi === 'boost' ? <IcRond /> : <IcEtincelle />}Booster ma phrase
              </button>
            </div>
          </div>

          {boost && (
            <div className="st-suggestion" role="status">
              <span className="st-etiq">Version boostée</span>
              <p>{boost}</p>
              <div className="st-ligne">
                <button type="button" className="st-bouton primaire" onClick={() => { setIntention(boost); setBoost(null); }}>Utiliser cette version</button>
                <button type="button" className="st-bouton" onClick={() => setBoost(null)}>Garder la mienne</button>
              </div>
            </div>
          )}

          {compris && mode === 'video' && (
            <div className="st-suggestion st-compris" role="status" aria-live="polite">
              <span className="st-etiq">Ce que l’IA a compris</span>
              <p>{compris.compris}</p>
              {compris.plans.length > 1 && <p className="st-compris-plans">{compris.plans.map((p, i) => `${i + 1}. ${p.cadrage} (${p.debut.toFixed(1).replace('.', ',')} s)`).join('  ·  ')}</p>}
              {compris.hypotheses.length > 0 && (
                <ul className="st-compris-choix" aria-label="Choix faits pour toi">{compris.hypotheses.map((h) => <li key={h}>{h}</li>)}</ul>
              )}
              {compris.variantes.length > 0 && (
                <div className="st-compris-variantes">
                  <span className="st-etiq">Autres directions</span>
                  <div className="st-idees">{compris.variantes.map((v) => <button key={v} type="button" className="st-idee" title="Mettre cette direction dans la description" onClick={() => { setIntention(`${intention.trim()} — ${v}`); setCompris(null); }}>{v}</button>)}</div>
                </div>
              )}
              <div className="st-ligne">
                <button type="button" className="st-bouton" onClick={() => setVoirPrompt((x) => !x)}>{voirPrompt ? 'Masquer' : 'Voir'} le prompt envoyé à H3</button>
                <button type="button" className="st-bouton" onClick={() => setCompris(null)}>Fermer</button>
                {compris.credits != null && compris.credits > 0 && <span className="st-credit">Écriture : {compris.credits} crédit{compris.credits > 1 ? 's' : ''}</span>}
              </div>
              {voirPrompt && <pre className="st-compris-prompt">{compris.prompt}</pre>}
            </div>
          )}

          {(!intention || idees[mode]) && (
            <div className="st-idees" aria-label="Idées">
              {(idees[mode] ?? IDEES[mode]).map((i) => <button key={i} type="button" className="st-idee" onClick={() => setIntention(i)}>{i.length > 72 ? `${i.slice(0, 70)}…` : i}</button>)}
              <button type="button" className="st-idee" disabled={inspire} onClick={() => void inspirer()} style={{ borderColor: 'rgba(255,90,31,.45)', color: 'var(--accent-hi)' }}>{inspire ? 'Je cherche…' : '✦ Inspire-moi'}</button>
            </div>
          )}

          {mode === 'video' && (
            <div className="st-bloc">
              <span className="st-etiq">Départ</span>
              <div className="st-seg" role="group" aria-label="Point de départ">
                {([['texte', 'Texte seul', 'H3 imagine'], ['photo', 'Ma photo', 'import'], ['cle', 'Plan clé IA', nomImage]] as const).map(([v, label, sub]) => (
                  <button key={v} type="button" className={depart === v ? 'on' : ''} onClick={() => { setDepart(v); if (v === 'texte') setCle(null); }}>{label}<small>{sub}</small></button>
                ))}
              </div>
              {depart === 'photo' && !cle && (
                <label className="st-bouton" style={{ textAlign: 'center', cursor: 'pointer' }}>
                  {envoi === 'photo' ? 'Envoi de la photo…' : 'Choisir une photo (ta voiture, ton produit, ton lieu)'}
                  <input type="file" accept="image/*" hidden onChange={(e) => void choisirPhoto(e.target.files?.[0])} />
                </label>
              )}
              {cle && (
                <div className="st-cle">
                  <img src={cle.apercu} alt="Image de départ" />
                  <span>La vidéo part de cette image.</span>
                  <button type="button" className="st-bouton" onClick={() => { setCle(null); }}>Retirer</button>
                </div>
              )}
              {depart === 'cle' && !cle && <span className="st-credit" style={{ textAlign: 'left' }}>Écris ta scène, clique « Dessiner », puis « Animer » sur le plan clé que tu préfères.</span>}
            </div>
          )}

          {mode === 'video' && (
            <div className="st-bloc">
              <span className="st-etiq">Mouvement de caméra {camera && <button type="button" className="nx-lien" style={{ fontSize: 11, marginLeft: 6 }} onClick={() => setCamera(null)}>retirer</button>}</span>
              <div className="st-cameras" role="group" aria-label="Mouvement de caméra">
                {CAMERAS.map((c) => (
                  <button key={c.id} type="button" className={`st-camera ${camera === c.id ? 'on' : ''}`} aria-pressed={camera === c.id} onClick={() => setCamera(camera === c.id ? null : c.id)} title={c.nom}>
                    <video src={c.clip} muted loop playsInline preload="metadata" onMouseEnter={(e) => void e.currentTarget.play().catch(() => {})} onMouseLeave={(e) => e.currentTarget.pause()} />
                    <span>{c.nom}</span>
                  </button>
                ))}
              </div>
            </div>
          )}

          <div className="st-bloc">
            <span className="st-etiq">Format</span>
            <div className="st-seg" role="group" aria-label="Format">
              {FORMATS.map((f) => (
                <button key={f.v} type="button" className={format === f.v ? 'on' : ''} onClick={() => setFormat(f.v)}><Ratio v={f.v} />{f.label}<small>{f.aide}</small></button>
              ))}
            </div>
          </div>

          {mode === 'video' && (
            <div className="st-bloc">
              <span className="st-etiq">Durée</span>
              <div className="st-seg" role="group" aria-label="Durée">
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
              <span className="st-etiq">Qualité</span>
              <div className="st-seg" role="group" aria-label="Qualité">
                <button type="button" className={qualite === 'rapide' ? 'on' : ''} onClick={() => setQualite('rapide')}>Rapide<small>FastH3 · 832×480</small></button>
                <button type="button" className={qualite === 'max' ? 'on' : ''} onClick={() => setQualite('max')}>{etat?.cinema ? 'Cinéma' : 'Qualité max'}<small>{etat?.cinema ? 'H3 complet · 768p' : '1344×768'}</small></button>
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
              <span className="st-etiq">Réplique (facultatif)</span>
              <input className="st-champ-ligne" value={replique} maxLength={300} onChange={(e) => setReplique(e.target.value)} placeholder="Ce qu’un personnage dit, ex. : On y va." aria-label="Réplique" />
            </div>
          )}

          {mode !== 'image' && (
            <div className="st-interrupteurs">
              <button type="button" className="st-inter" aria-pressed={son} onClick={() => setSon(!son)}><span>Son<small>bruitages et voix H3</small></span><i /></button>
              {mode === 'video' && (
                <button type="button" className="st-inter" aria-pressed={musique} onClick={() => setMusique(!musique)} disabled={!etat?.musique} title={etat?.musique ? '' : 'Aucun moteur de musique en ligne'}>
                  <span>Musique<small>MiniMax-Music3</small></span><i />
                </button>
              )}
            </div>
          )}


          <div className="st-cta">
            <button type="button" className="st-go" disabled={!prete} onClick={lancer}>{libelle}</button>
            {mode === 'video' && devis && devis.secondesEstimees != null && !cleRequise && (
              <div className="st-devis">
                <span>Tournage ≈ <b>{fmtTemps(devis.secondesEstimees)}</b></span>
                <span>{qualite === 'max' && etat?.cinema ? 'H3 complet' : 'FastH3'} · RTX 5090{devis.credits !== null ? ` · ${devis.credits} crédits` : ''}</span>
              </div>
            )}
            {mode === 'image' && <div className="st-devis"><span>{nomImage} · DGX Spark GB10</span><span>≈ {qualite === 'max' ? '50 s' : '25 s'} par image</span></div>}
            <p className="st-credit">Propulsé par MiniMax H3 · {etat?.image ?? 'Qwen-Image'} · MiniMax-Music3</p>
          </div>
        </aside>

        <section className="st-galerie" aria-label="Tes créations">
          {storyboard && (
            <div className="st-decoupage">
              <div className="nx-sb-tete">
                <div>
                  <h2>{storyboard.titre}</h2>
                  <p className="nx-sous" style={{ margin: 0 }}>{storyboard.plans.length} plans · {storyboard.dureeTotale} s · tournage ≈ {minutesFilm} min. Retouche ce qui ne te plaît pas, puis lance.</p>
                </div>
                <div className="st-ligne">
                  <button type="button" className="st-bouton" onClick={() => setStoryboard(null)}>Annuler</button>
                  <button type="button" className="st-bouton primaire" disabled={occupe} onClick={() => void tournerFilm()}>{envoi === 'film' ? 'Lancement…' : 'Tourner le film'}</button>
                </div>
              </div>
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
            <h2>Tes créations</h2>
            <div className="st-filtres" role="group" aria-label="Filtrer">
              {([['tout', 'Tout'], ['videos', 'Vidéos'], ['films', 'Films'], ['images', 'Images']] as const).map(([v, label]) => (
                <button key={v} type="button" className={filtre === v ? 'on' : ''} onClick={() => setFiltre(v)}>{label}</button>
              ))}
            </div>
          </div>

          {montrees.length === 0 ? (
            <div className="st-vide">
              <div className="st-mosaique" aria-hidden>
                {Array.from({ length: 18 }, (_, i) => <i key={i} style={{ opacity: [1, 0.15, 0.6, 0.3, 0.9, 0.2][(i * 5) % 6] }} />)}
              </div>
              <strong>Ta première scène t’attend.</strong>
              <span>Écris une idée à gauche, ou pars d’un exemple. Les vidéos, images et films apparaîtront ici, avec leur progression en direct.</span>
            </div>
          ) : (
            <div className="st-cartes">
              {montrees.map((t) => {
                const s = settingsOf(t);
                const plans = s.film ? ((s.storyboard?.plans ?? []) as { take?: number }[]) : [];
                const faits = plans.filter((p) => p.take && toutes.find((x) => x.id === p.take)?.status === 'done').length;
                const image = isImage(t);
                const actions = t.status !== 'done' ? undefined : s.film ? (
                  <div className="st-actions-carte"><button type="button" onClick={() => setFilmOuvert(t.id)}>Plans et montage</button></div>
                ) : image ? (
                  <div className="st-actions-carte">
                    <button type="button" onClick={() => void animer(t.id)}>Animer avec H3</button>
                    <a href={mediaUrl(t.id)} download>Télécharger</a>
                  </div>
                ) : (
                  <div className="st-actions-carte">
                    {!s.nexoraAvecMusique && !s.nexoraMusiqueLance && etat?.musique && (
                      <button type="button" onClick={() => { api.nexoraClipMusique(t.id, {}).then(() => toast('Composition de la musique lancée (moins d’une minute).')).catch((e) => toast(e instanceof Error ? e.message : 'Impossible de composer la musique.', true)); }}>Ajouter une musique</button>
                    )}
                    <button type="button" onClick={() => setPub(t.id)}>Texte réseaux</button>
                    <a href={mediaUrl(t.id)} download>Télécharger</a>
                  </div>
                );
                return (
                  <MediaCard key={t.id} take={t} onOpen={() => (s.film ? setFilmOuvert(t.id) : setVue(t.id))}
                    tag={s.film ? 'Film' : s.nexoraAvecMusique ? '+ musique' : image ? 'Image' : undefined}
                    pendingLabel={s.film ? `Film : ${faits}/${plans.length} plans tournés` : 'En file d’attente'}
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
