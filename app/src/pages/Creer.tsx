/**
 * Nexora Creative — accueil « Créer » : la personne décrit sa vidéo avec ses mots.
 * Clip (5 à 15 s) : le LLM écrit le scénario, MiniMax H3 tourne. Film (30 s à 2 min) : l'AI Director propose un
 * découpage en plans que la personne peut relire et retoucher, puis chaque plan est tourné et le film assemblé.
 * Aucun réglage technique ici ; le mode expert reste dans Vidéo, Image, Director.
 */
import { useEffect, useMemo, useState } from 'react';
import { api, uploadFile, type CreerReponse, type EtatNexora, type Storyboard } from '../api';
import { inFeed, isImage, isModel, settingsOf, toast, useStore } from '../store';
import { MediaCard } from '../ui';
import Viewer from '../Viewer';
import FilmPlans from '../FilmPlans';

type Format = '16:9' | '9:16' | '1:1';
type Duree = 5 | 10 | 15 | 30 | 60 | 120;

const IDEES = [
  'Ma voiture rouge se transforme en robot géant pendant que la caméra tourne autour, au coucher du soleil.',
  'Publicité pour un café glacé : gouttes au ralenti, lumière dorée, une voix dit « Le froid qui réveille ».',
  'Un renard en papier découpé traverse une forêt d’automne qui s’anime à son passage.',
  'Plan drone au-dessus de Montréal en hiver, la neige tombe, la ville s’illumine à la tombée du jour.',
];

const FORMATS: { v: Format; label: string; aide: string }[] = [
  { v: '16:9', label: 'Paysage', aide: 'YouTube, site web' },
  { v: '9:16', label: 'Vertical', aide: 'TikTok, Reels, Shorts' },
  { v: '1:1', label: 'Carré', aide: 'Publications' },
];
const DUREES: { v: Duree; label: string }[] = [
  { v: 5, label: '5 s' }, { v: 10, label: '10 s' }, { v: 15, label: '15 s' },
  { v: 30, label: 'Film 30 s' }, { v: 60, label: 'Film 1 min' }, { v: 120, label: 'Film 2 min' },
];
/** Temps de tournage mesuré sur le DGX Spark GB10 pour un plan de 5 s (recherche/08). */
const SECONDES_PAR_PLAN_5S = 85;

export default function Creer() {
  const [intention, setIntention] = useState('');
  const [format, setFormat] = useState<Format>('16:9');
  const [duree, setDuree] = useState<Duree>(5);
  const [son, setSon] = useState(true);
  const [qualite, setQualite] = useState<'rapide' | 'max'>('rapide');
  const [envoi, setEnvoi] = useState<null | 'clip' | 'plan' | 'film'>(null);
  const [dernier, setDernier] = useState<CreerReponse | null>(null);
  const [storyboard, setStoryboard] = useState<Storyboard | null>(null);
  const [voirScenario, setVoirScenario] = useState(false);
  const [etat, setEtat] = useState<EtatNexora | null>(null);
  const [vue, setVue] = useState<number | null>(null);
  const [filmOuvert, setFilmOuvert] = useState<number | null>(null);
  const [photo, setPhoto] = useState<{ jeton: string; apercu: string } | null>(null);
  const [envoiPhoto, setEnvoiPhoto] = useState(false);
  const toutes = useStore((s) => s.takes);
  const takes = useStore((s) => s.takes.filter((t) => inFeed(t) && !isImage(t) && !isModel(t) && settingsOf(t).nexoraFilm == null).slice(0, 12));

  useEffect(() => { void api.nexoraEtat().then(setEtat).catch(() => setEtat(null)); }, []);
  const [devis, setDevis] = useState<{ credits: number | null; secondesEstimees: number } | null>(null);
  useEffect(() => {
    if (duree > 15) { setDevis(null); return; }
    let actif = true;
    void api.nexoraDevis({ format, duree, son, qualite, image: photo?.jeton }).then((d) => actif && setDevis(d)).catch(() => actif && setDevis(null));
    return () => { actif = false; };
  }, [format, duree, son, qualite, photo]);
  const film = duree > 15;
  const prete = intention.trim().length > 0 && !envoi;
  const ids = useMemo(() => takes.map((t) => t.id), [takes]);

  async function creerClip() {
    setEnvoi('clip');
    setVoirScenario(false);
    try {
      const r = await api.nexoraCreer({ intention: intention.trim(), format, duree: duree as 5 | 10 | 15, son, qualite, image: photo?.jeton });
      setDernier(r);
      toast(r.source === 'llm' ? 'Scénario écrit, tournage lancé.' : 'Tournage lancé (scénario simplifié : IA indisponible).');
    } catch (e) {
      toast(e instanceof Error ? e.message : 'La création a échoué.', true);
    } finally {
      setEnvoi(null);
    }
  }

  async function proposerDecoupage() {
    setEnvoi('plan');
    try {
      const r = await api.nexoraFilmPlan({ intention: intention.trim(), duree });
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
    setEnvoiPhoto(true);
    try {
      const jeton = await uploadFile(f);
      setPhoto({ jeton, apercu: URL.createObjectURL(f) });
    } catch (e) {
      toast(e instanceof Error ? e.message : 'La photo n’a pas pu être envoyée.', true);
    } finally {
      setEnvoiPhoto(false);
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

  const libelleBouton = envoi === 'clip' ? 'L’IA écrit le scénario…' : envoi === 'plan' ? 'L’IA découpe ton film…' : film ? 'Proposer le découpage' : 'Créer la vidéo';
  const minutesFilm = storyboard ? Math.ceil((storyboard.plans.reduce((n, p) => n + (p.duree === 10 ? 2 : 1), 0) * SECONDES_PAR_PLAN_5S) / 60) : 0;

  return (
    <div className="nx-creer">
      <section className="nx-hero">
        <h1>Décris ta vidéo. Nexora la tourne.</h1>
        <p className="nx-sous">Écris ce que tu imagines, avec tes mots. L’IA écrit le scénario, choisit les plans, la caméra et le son, puis tourne la vidéo.</p>
        <div className="nx-saisie">
          <textarea
            value={intention}
            onChange={(e) => setIntention(e.target.value)}
            onKeyDown={(e) => { if ((e.ctrlKey || e.metaKey) && e.key === 'Enter' && prete) void (film ? proposerDecoupage() : creerClip()); }}
            placeholder="Ex. : Ma voiture se transforme en robot géant pendant qu’une caméra tourne autour…"
            rows={4}
            maxLength={4000}
            aria-label="Description de la vidéo"
          />
          <div className="nx-options">
            <div className="nx-groupe" role="group" aria-label="Format">
              {FORMATS.map((f) => (
                <button key={f.v} type="button" className={`nx-puce ${format === f.v ? 'on' : ''}`} onClick={() => setFormat(f.v)} title={f.aide}>{f.label}</button>
              ))}
            </div>
            <div className="nx-groupe" role="group" aria-label="Durée">
              {DUREES.map((d) => (
                <button key={d.v} type="button" className={`nx-puce ${duree === d.v ? 'on' : ''}`} onClick={() => { setDuree(d.v); setStoryboard(null); }}>{d.label}</button>
              ))}
            </div>
            <button type="button" className={`nx-puce ${son ? 'on' : ''}`} onClick={() => setSon(!son)} aria-pressed={son}>{son ? 'Avec son' : 'Sans son'}</button>
            <div className="nx-groupe" role="group" aria-label="Qualité">
              <button type="button" className={`nx-puce ${qualite === 'rapide' ? 'on' : ''}`} onClick={() => setQualite('rapide')} title="Rendu rapide, idéal pour essayer">Rapide</button>
              <button type="button" className={`nx-puce ${qualite === 'max' ? 'on' : ''}`} onClick={() => setQualite('max')} title="Résolution native du modèle, plus long à tourner">Qualité max</button>
            </div>
            {!film && (
              photo ? (
                <span className="nx-photo">
                  <img src={photo.apercu} alt="Photo de départ" />
                  <button type="button" className="nx-lien" onClick={() => setPhoto(null)}>Retirer la photo</button>
                </span>
              ) : (
                <label className="nx-puce nx-photo-btn" title="La vidéo part de ta photo (ta voiture, ton produit, ton lieu)">
                  {envoiPhoto ? 'Envoi de la photo…' : 'Partir de ma photo'}
                  <input type="file" accept="image/*" hidden onChange={(e) => void choisirPhoto(e.target.files?.[0])} />
                </label>
              )
            )}
            <button type="button" className="nx-creer-btn" disabled={!prete} onClick={() => void (film ? proposerDecoupage() : creerClip())}>{libelleBouton}</button>
          </div>
        </div>
        {devis && !film && (
          <p className="nx-devis">Tournage estimé ≈ {devis.secondesEstimees < 90 ? `${devis.secondesEstimees} s` : `${Math.floor(devis.secondesEstimees / 60)} min ${String(devis.secondesEstimees % 60).padStart(2, '0')} s`}{devis.credits !== null ? ` · ${devis.credits} crédits` : ''}</p>
        )}
        {!intention && (
          <div className="nx-idees">
            <span>Idées :</span>
            {IDEES.map((i) => <button key={i} type="button" className="nx-idee" onClick={() => setIntention(i)}>{i}</button>)}
          </div>
        )}
        {dernier && !film && (
          <div className="nx-scenario">
            <button type="button" className="nx-lien" onClick={() => setVoirScenario(!voirScenario)}>
              {voirScenario ? 'Masquer' : 'Voir'} le scénario écrit par l’IA {dernier.source === 'repli' ? '(version simplifiée)' : ''}
            </button>
            {voirScenario && <pre>{dernier.prompt}</pre>}
          </div>
        )}
        {etat && !etat.son && <p className="nx-note">Pour ton compte, les vidéos sont tournées avec {etat.moteur}, sans piste sonore générée.</p>}
        {etat && !etat.llm && <p className="nx-note">L’assistant d’écriture n’est pas branché sur ce poste : la vidéo sera tournée à partir de ta phrase telle quelle.</p>}
      </section>

      {storyboard && (
        <section className="nx-storyboard" aria-label="Découpage proposé">
          <div className="nx-sb-tete">
            <div>
              <h2>{storyboard.titre}</h2>
              <p className="nx-sous">{storyboard.plans.length} plans · {storyboard.dureeTotale} s · tournage estimé ≈ {minutesFilm} min. Relis, retouche ce que tu veux, puis lance.</p>
            </div>
            <button type="button" className="nx-creer-btn" disabled={!!envoi} onClick={() => void tournerFilm()}>{envoi === 'film' ? 'Mise en tournage…' : 'Tourner le film'}</button>
          </div>
          {(storyboard.bible.style || storyboard.bible.personnages.length > 0) && (
            <details className="nx-bible">
              <summary>Bible de continuité (style, personnages, lieux)</summary>
              {storyboard.bible.style && <p><strong>Style :</strong> {storyboard.bible.style}</p>}
              {storyboard.bible.personnages.map((c) => <p key={c.nom}><strong>{c.nom} :</strong> {c.description}</p>)}
              {storyboard.bible.lieux.map((l) => <p key={l.nom}><strong>{l.nom} :</strong> {l.description}</p>)}
            </details>
          )}
          <ol className="nx-plans">
            {storyboard.plans.map((p, i) => (
              <li key={i} className="nx-plan">
                <div className="nx-plan-num">{i + 1}</div>
                <div className="nx-plan-corps">
                  <input value={p.resume} onChange={(e) => majPlan(i, { resume: e.target.value })} aria-label={`Résumé du plan ${i + 1}`} />
                  <textarea value={p.description} rows={3} onChange={(e) => majPlan(i, { description: e.target.value })} aria-label={`Description du plan ${i + 1}`} />
                  <div className="nx-plan-pied">
                    <span className="nx-camera">🎥 {p.camera}</span>
                    <div className="nx-groupe">
                      {([5, 10] as const).map((d) => <button key={d} type="button" className={`nx-puce ${p.duree === d ? 'on' : ''}`} onClick={() => majPlan(i, { duree: d })}>{d} s</button>)}
                    </div>
                    <button type="button" className="nx-lien" onClick={() => retirerPlan(i)} disabled={storyboard.plans.length <= 1}>Retirer</button>
                  </div>
                </div>
              </li>
            ))}
          </ol>
        </section>
      )}

      <section className="nx-resultats">
        <h2>Tes vidéos</h2>
        {takes.length === 0 ? <p className="nx-vide">Tes créations apparaîtront ici, avec leur progression en direct.</p> : (
          <div className="grid">
            {takes.map((t) => {
              const s = settingsOf(t);
              const plans = s.film ? (s.storyboard?.plans ?? []) as { take?: number }[] : [];
              const faits = plans.filter((p) => p.take && toutes.find((x) => x.id === p.take)?.status === 'done').length;
              return <MediaCard key={t.id} take={t} onOpen={() => (s.film ? setFilmOuvert(t.id) : setVue(t.id))} tag={s.film ? 'Film' : undefined}
                pendingLabel={s.film ? `Film : ${faits}/${plans.length} plans tournés` : 'En file d’attente'}
                actions={s.film ? <button type="button" className="nx-puce on" onClick={() => setFilmOuvert(t.id)}>Plans</button> : undefined} />;
            })}
          </div>
        )}
      </section>

      <footer className="nx-pied">Vidéo propulsée par <strong>{etat?.moteur ?? 'MiniMax H3'}</strong> · Scénario par IA · Nexora Creative</footer>
      {filmOuvert !== null && <FilmPlans filmId={filmOuvert} onClose={() => setFilmOuvert(null)} />}
      {vue !== null && <Viewer takeId={vue} onClose={() => setVue(null)} onStep={(d) => {
        const n = ids[ids.indexOf(vue) + d];
        if (n !== undefined) setVue(n);
      }} />}
    </div>
  );
}
