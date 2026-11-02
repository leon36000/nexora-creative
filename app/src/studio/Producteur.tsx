/**
 * Producteur : l'agent qui fait le gros du travail (server/nexora/agent.ts).
 * À gauche, la conversation : un objectif en français (« une pub de 30 s pour ma boulangerie, verticale »).
 * À droite, le plan proposé (plans, réplique, musique, cartons), le devis calculé par le code et le bouton qui lance,
 * puis les productions en cours : progression plan par plan, choix du juge visuel, variantes en un clic.
 * Rien n'est dépensé sans un clic sur « Valider et lancer ».
 */
import { Markdown } from './Markdown';
import { useEffect, useMemo, useRef, useState } from 'react';
import { api, mediaUrl, type FilmResume, type VueMontage, type VuePrises, type PropositionProducteur, type SessionProducteur, type VarianteProducteur } from '../api';
import { settingsOf, toast, useStore } from '../store';
import { setParams } from '../router';
import { MediaCard } from '../ui';
import { IcEtincelle, IcRond, Ratio } from './icons';

const EXEMPLES = [
  'Une pub de 20 s pour ma boulangerie de quartier, verticale, avec musique.',
  'Un teaser de 15 s pour le lancement d’une application de covoiturage, format carré.',
  'Un court film de 30 s : une renarde traverse une ville enneigée la nuit, ambiance conte.',
  'Une vidéo de bienvenue de 10 s pour mon cabinet de physiothérapie, paysage.',
];
const CLE = 'nexora.producteur.session';
const fmtMin = (m: number) => (m < 60 ? `${m} min` : `${Math.floor(m / 60)} h ${String(m % 60).padStart(2, '0')}`);

export default function Producteur({ onOuvrirFilm, objectif }: { onOuvrirFilm: (id: number) => void; objectif?: string | null }) {
  const [session, setSession] = useState<SessionProducteur | null>(null);
  const [liste, setListe] = useState<{ id: string; titre: string }[]>([]);
  const [texte, setTexte] = useState('');
  const [envoi, setEnvoi] = useState<null | 'message' | 'valider' | 'ajuster' | 'variante'>(null);
  const fil = useRef<HTMLDivElement>(null);

  useEffect(() => {
    void api.producteurListe().then((r) => setListe(r.sessions)).catch(() => {});
    let id: string | null = null;
    try { id = localStorage.getItem(CLE); } catch { /* stockage indisponible */ }
    if (id) void api.producteurSession(id).then(setSession).catch(() => { try { localStorage.removeItem(CLE); } catch { /* rien */ } });
  }, []);
  // Modèle choisi dans Explorer : l'objectif part tout de suite au Producteur, dans une nouvelle conversation.
  const lance = useRef(false);
  useEffect(() => {
    if (!objectif || lance.current) return;
    lance.current = true;
    setParams({ objectif: null });
    setSession(null);
    void envoyer(objectif, true);
  }, [objectif]);
  useEffect(() => {
    if (!session) return;
    try { localStorage.setItem(CLE, session.id); } catch { /* rien */ }
  }, [session?.id]);
  useEffect(() => { requestAnimationFrame(() => fil.current?.scrollTo({ top: fil.current.scrollHeight })); }, [session?.id, session?.fil.length, envoi]);

  // Les films de la conversation (et leurs plans, leur musique) changent d'état en direct : on relit la session.
  const filmIds = useMemo(() => new Set(session?.productions.map((p) => p.filmId) ?? []), [session]);
  const cleDirect = useStore((s) => s.takes
    .filter((t) => filmIds.has(t.id) || filmIds.has(Number(settingsOf(t).nexoraFilm)))
    .map((t) => `${t.id}:${t.status}`).join(','));
  useEffect(() => {
    if (!session || !cleDirect) return;
    const t = setTimeout(() => void api.producteurSession(session.id).then(setSession).catch(() => {}), 400);
    return () => clearTimeout(t);
  }, [cleDirect]);

  async function envoyer(message = texte, neuve = false) {
    const t = message.trim();
    if (!t || envoi) return;
    setEnvoi('message');
    setTexte('');
    try {
      const s = (!neuve && session) || (await api.producteurNouvelle());
      // La bulle de la personne s'affiche tout de suite, la réponse arrive ensuite.
      setSession({ ...s, fil: [...s.fil, { de: 'personne', texte: t, date: new Date().toISOString() }] });
      setSession(await api.producteurMessage(s.id, t));
      if (!session) void api.producteurListe().then((r) => setListe(r.sessions)).catch(() => {});
    } catch (e) {
      toast(e instanceof Error ? e.message : 'Le Producteur n’a pas répondu.', true);
      setTexte(t);
      if (session) void api.producteurSession(session.id).then(setSession).catch(() => {});
    } finally {
      setEnvoi(null);
    }
  }

  async function agir<T>(genre: 'valider' | 'ajuster' | 'variante', f: () => Promise<SessionProducteur>, ok?: string) {
    setEnvoi(genre);
    try {
      setSession(await f());
      if (ok) toast(ok);
    } catch (e) {
      toast(e instanceof Error ? e.message : 'Action impossible.', true);
    } finally {
      setEnvoi(null);
    }
  }

  function nouvelle() {
    setSession(null);
    setTexte('');
    try { localStorage.removeItem(CLE); } catch { /* rien */ }
  }

  const productions = [...(session?.productions ?? [])].reverse();
  const proposition = session?.proposition ?? null;

  return (
    <>
      <aside className="st-composer pr-chat" aria-label="Conversation avec le Producteur">
        <div className="pr-tete">
          <div>
            <span className="st-etiq">Producteur IA</span>
            <strong>{session?.titre && session.titre !== 'Nouvelle production' ? session.titre : 'Nouvelle production'}</strong>
          </div>
          <div className="st-ligne">
            {liste.length > 0 && (
              <select className="pr-select" aria-label="Productions précédentes" value={session?.id ?? ''} onChange={(e) => e.target.value && void api.producteurSession(e.target.value).then(setSession)}>
                <option value="">Historique…</option>
                {liste.map((x) => <option key={x.id} value={x.id}>{x.titre.slice(0, 40)}</option>)}
              </select>
            )}
            <button type="button" className="st-bouton" onClick={nouvelle} disabled={!session}>Nouvelle</button>
          </div>
        </div>

        <div className="pr-fil" ref={fil} aria-live="polite">
          {!session?.fil.length && (
            <div className="pr-accueil">
              <p>Dis-moi ce que tu veux produire. Je propose le découpage, la musique, les textes et le prix ; tu valides d’un clic, je tourne, je contrôle chaque plan et j’assemble.</p>
              <div className="pr-exemples">
                {EXEMPLES.map((x) => <button key={x} type="button" className="st-idee" onClick={() => void envoyer(x)} disabled={!!envoi}>{x}</button>)}
              </div>
            </div>
          )}
          {session?.fil.map((b, i) => (
            <div key={i} className={`pr-bulle ${b.de}`}>
              {b.de === 'producteur' && <span className="pr-qui"><IcEtincelle />Producteur</span>}
              {b.de === 'producteur' ? <Markdown texte={b.texte} /> : <p>{b.texte}</p>}
              {b.production && <button type="button" className="nx-lien" onClick={() => onOuvrirFilm(b.production!)}>Voir les plans</button>}
            </div>
          ))}
          {envoi === 'message' && <div className="pr-bulle producteur pr-pense"><span className="pr-qui"><IcRond />Le Producteur prépare le plan…</span></div>}
        </div>

        <div className="st-champ pr-saisie">
          <textarea
            value={texte}
            onChange={(e) => setTexte(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); void envoyer(); } }}
            placeholder={session?.productions.length ? 'Une retouche ? « Rends le plan 2 plus lumineux », « coupe le dernier plan »…' : 'Ton objectif : produit, durée, format, ambiance…'}
            maxLength={4000}
            rows={3}
            aria-label="Message au Producteur"
          />
          <div className="st-champ-pied">
            <span>Entrée pour envoyer · Maj+Entrée pour aller à la ligne</span>
            <button type="button" className="st-bouton primaire" disabled={!texte.trim() || !!envoi} onClick={() => void envoyer()}>Envoyer</button>
          </div>
        </div>
      </aside>

      <section className="st-galerie" aria-label="Plan et productions">
        {proposition && session && (
          <CarteProposition
            p={proposition} session={session} occupe={!!envoi}
            ajuster={(r) => void agir('ajuster', () => api.producteurAjuster(session.id, proposition.id, r))}
            valider={() => void agir('valider', () => api.producteurValider(session.id, proposition.id), 'C’est parti : le tournage est lancé.')}
          />
        )}

        {productions.length > 0 && (
          <div className="st-g-tete"><h2>Productions</h2></div>
        )}
        {productions.map((p) => (
          <CarteProduction key={p.filmId + p.lanceLe} filmId={p.filmId} film={'film' in p.film ? p.film : null} format={p.plan?.format}
            occupe={!!envoi} ouvrir={() => onOuvrirFilm(p.filmId)}
            variante={(g) => session && void agir('variante', () => api.producteurVariante(session.id, p.filmId, g))} />
        ))}

        {!proposition && productions.length === 0 && (
          <div className="st-vide pr-vide">
            <div className="st-mosaique" aria-hidden>{Array.from({ length: 18 }, (_, i) => <i key={i} style={{ opacity: [1, 0.15, 0.6, 0.3, 0.9, 0.2][(i * 5) % 6] }} />)}</div>
            <strong>Ton plan de production apparaîtra ici.</strong>
            <span>Plans, réplique, musique, textes à l’écran et devis : tu relis, tu ajustes d’un clic, tu lances. Rien n’est dépensé avant.</span>
          </div>
        )}
      </section>
    </>
  );
}

function CarteProposition({ p, session, occupe, ajuster, valider }: {
  p: PropositionProducteur; session: SessionProducteur; occupe: boolean;
  ajuster: (r: { candidats?: number; qualite?: string; format?: string; musique?: boolean }) => void; valider: () => void;
}) {
  const d = p.devis;
  const nbr = (n: number) => `${n.toLocaleString('fr-FR')} crédit${n > 1 ? 's' : ''}`;
  const prix = d.credits === null ? `≈ ${nbr(d.creditsEstimes)}` : d.credits === 0 ? 'Gratuit' : nbr(d.credits);
  return (
    <div className="pr-carte" aria-label="Plan proposé">
      {p.genre === 'production' ? (
        <>
          <div className="pr-carte-tete">
            <div>
              <span className="st-etiq">{p.base ? 'Variante proposée' : 'Plan proposé'}</span>
              <h2>{p.plan.titre}</h2>
              <p className="pr-meta"><Ratio v={p.plan.format} />{p.plan.format} · {p.plan.plans.reduce((n, x) => n + x.duree, 0)} s · {p.plan.plans.length} plan{p.plan.plans.length > 1 ? 's' : ''} · {p.plan.qualite === 'max' ? 'H3 complet' : 'FastH3'}{p.plan.son ? ' · son' : ''}</p>
            </div>
          </div>
          <ol className="pr-plans">
            {p.plan.cartons.filter((c) => c.position === 'debut').map((c) => <li key={`d${c.texte}`} className="pr-plan carton"><span className="pr-num">T</span><div><b>Carton</b><p>« {c.texte} »</p></div></li>)}
            {p.plan.plans.map((x, i) => (
              <li key={i} className="pr-plan">
                <span className="pr-num">{i + 1}</span>
                <div>
                  <b>{x.resume}</b>
                  <p className="pr-cam">{x.camera}{x.suite ? ' · enchaîné' : ''} · {x.duree} s</p>
                  {x.replique && <p className="pr-replique">« {x.replique} »</p>}
                </div>
              </li>
            ))}
            {p.plan.cartons.filter((c) => c.position === 'fin').map((c) => <li key={`f${c.texte}`} className="pr-plan carton"><span className="pr-num">T</span><div><b>Carton</b><p>« {c.texte} »</p></div></li>)}
          </ol>
          {p.plan.musique && <p className="pr-ligne"><span className="st-etiq">Musique</span>{p.plan.musique.envie || 'composée d’après le film'} · MiniMax-Music3</p>}
          <div className="pr-reglages">
            <div className="st-seg" role="group" aria-label="Format">
              {(['9:16', '1:1', '16:9'] as const).map((f) => <button key={f} type="button" className={p.plan.format === f ? 'on' : ''} disabled={occupe} onClick={() => p.plan.format !== f && ajuster({ format: f })}><Ratio v={f} />{f === '9:16' ? 'Vertical' : f === '1:1' ? 'Carré' : 'Paysage'}</button>)}
            </div>
            <div className="st-interrupteurs">
              <button type="button" className="st-inter" aria-pressed={p.plan.candidats === 2} disabled={occupe || !session.juge} title={session.juge ? '' : 'Juge visuel non configuré sur ce poste'} onClick={() => ajuster({ candidats: p.plan.candidats === 2 ? 1 : 2 })}>
                <span>2 prises par plan<small>le juge IA garde la meilleure · coût ×2</small></span><i />
              </button>
              <button type="button" className="st-inter" aria-pressed={p.plan.qualite === 'max'} disabled={occupe} onClick={() => ajuster({ qualite: p.plan.qualite === 'max' ? 'rapide' : 'max' })}>
                <span>Qualité cinéma<small>H3 complet · bien plus long</small></span><i />
              </button>
              <button type="button" className="st-inter" aria-pressed={!!p.plan.musique} disabled={occupe} onClick={() => ajuster({ musique: !p.plan.musique })}>
                <span>Musique<small>MiniMax-Music3</small></span><i />
              </button>
            </div>
          </div>
        </>
      ) : p.genre === 'refaire' ? (
        <div className="pr-carte-tete"><div><span className="st-etiq">Retouche proposée</span><h2>Refaire le plan {p.plan + 1}</h2><p className="pr-meta">{p.description ?? 'Même description, nouvelle prise'}{p.camera ? ` · caméra : ${p.camera}` : ''}</p></div></div>
      ) : (
        <div className="pr-carte-tete"><div><span className="st-etiq">Nouveau montage</span><h2>Plans {p.ordre.map((x) => x + 1).join(', ')}</h2><p className="pr-meta">{p.transition === 'fondu' ? 'Fondus enchaînés' : 'Coupes franches'} · aucun nouveau rendu</p></div></div>
      )}
      <div className="pr-devis">
        <div><span className="st-etiq">Devis</span><b>{prix}</b>{d.credits === null && <small className="pr-devis-note">estimation · rien n’est débité sur ce poste</small>}</div>
        <div><span className="st-etiq">Attente</span><b>≈ {fmtMin(d.minutes)}</b></div>
        <div><span className="st-etiq">Rendus</span><b>{d.rendus}</b></div>
        <button type="button" className="st-go" disabled={occupe} onClick={valider}>{occupe ? <><IcRond /> Un instant…</> : 'Valider et lancer'}</button>
      </div>
      {session.credits && <p className="st-credit">Plafond : {session.plafond.credits} crédits par production. Les échecs techniques ne sont pas facturés.</p>}
    </div>
  );
}

const VARIANTES: { g: VarianteProducteur; label: string; si?: (f: FilmResume, format?: string) => boolean }[] = [
  { g: 'format-9:16', label: 'Version verticale', si: (_f, fo) => fo !== '9:16' },
  { g: 'format-1:1', label: 'Version carrée', si: (_f, fo) => fo !== '1:1' },
  { g: 'format-16:9', label: 'Version paysage', si: (_f, fo) => fo !== '16:9' },
  { g: 'nouvelle-prise', label: 'Nouvelle prise' },
  { g: 'cinema', label: 'Qualité cinéma', si: (f) => f.qualite !== 'max' },
  { g: 'courte', label: 'Version courte', si: (f) => f.plans.length > 2 },
];

function CarteProduction({ filmId, film, format, occupe, ouvrir, variante }: {
  filmId: number; film: FilmResume | null; format?: string; occupe: boolean; ouvrir: () => void; variante: (g: VarianteProducteur) => void;
}) {
  const take = useStore((s) => s.takes.find((t) => t.id === filmId));
  const faits = film?.plans.filter((x) => x.etat === 'done').length ?? 0;
  const fini = film?.etat === 'done';
  const [montage, setMontage] = useState<null | 'rend' | 'ok'>(null);
  const [prises, setPrises] = useState<VuePrises | null>(null);
  const [prisesOuvert, setPrisesOuvert] = useState(false);
  async function chargerPrises() { try { setPrises(await api.prisesFilm(filmId)); } catch (e) { toast(e instanceof Error ? e.message : 'Prises indisponibles.', true); } }
  async function agirPrises(f: () => Promise<VuePrises & { filmId?: number }>, ok: string) {
    try { const r = await f(); setPrises(r); toast(r.filmId ? `${ok} Film n° ${r.filmId} dans la Bibliothèque.` : ok); } catch (e) { toast(e instanceof Error ? e.message : 'Action impossible.', true); }
  }
  const [vue, setVue] = useState<VueMontage | null>(null);
  async function monter() {
    setMontage('rend');
    try { setVue(await api.monterFilm(filmId, { genre: 'pub' })); setMontage('ok'); }
    catch (e) { setMontage(null); toast(e instanceof Error ? e.message : 'Le montage a échoué.', true); }
  }
  async function ameliorer() {
    if (!vue) return;
    setMontage('rend');
    try { setVue(await api.ameliorerMontage(vue.id)); }
    catch (e) { toast(e instanceof Error ? e.message : 'Amélioration impossible.', true); }
    setMontage('ok');
  }
  return (
    <div className="pr-prod">
      <div className="pr-prod-media">
        {take ? <MediaCard take={take} onOpen={ouvrir} pendingLabel={`${faits}/${film?.plans.length ?? '?'} plans tournés`} tag="Producteur" /> : <div className="card pending"><div className="status"><div className="label">Chargement…</div></div></div>}
      </div>
      <div className="pr-prod-corps">
        <div className="pr-carte-tete">
          <div>
            <span className="st-etiq">{fini ? 'Prêt' : film?.etat === 'failed' ? 'Échec' : 'En production'}</span>
            <h3>{film?.titre ?? `Film ${filmId}`}</h3>
          </div>
        </div>
        {film?.erreur && <p className="pr-erreur">{film.erreur}</p>}
        <ul className="pr-suivi">
          {film?.plans.map((x) => (
            <li key={x.plan} className={x.etat}>
              <span className="pr-num">{x.plan}</span>
              <span className="pr-suivi-txt">
                {x.resume}
                {x.juge && <small title={x.juge.raison}>{x.juge.source === 'juge' ? '✦ Juge : ' : ''}{x.juge.raison}</small>}
                {Array.isArray(x.controle) && <small className="bad">Contrôle : {x.controle.join(', ')}</small>}
                {!!x.reprises && <small>Reprise automatique ({x.reprises})</small>}
              </span>
              <span className="pr-etat">{x.etat === 'done' ? 'tourné' : x.etat === 'rendering' ? 'au tournage' : x.etat === 'failed' ? 'échec' : 'en file'}</span>
            </li>
          ))}
          {film?.musique && <li className={film.musique}><span className="pr-num">♪</span><span className="pr-suivi-txt">Bande originale</span><span className="pr-etat">{film.musique === 'done' ? 'composée' : film.musique === 'failed' ? 'échec' : 'en cours'}</span></li>}
        </ul>
        {prisesOuvert && prises && <PanneauPrises v={prises} occupe={occupe} agir={agirPrises} filmId={filmId} fermer={() => setPrisesOuvert(false)} />}
        {vue && <ApercuMontage vue={vue} occupe={montage === 'rend'} ameliorer={() => void ameliorer()} fermer={() => { setVue(null); setMontage(null); }} />}
        {fini && film && (
          <div className="pr-variantes">
            <a className="st-bouton primaire" href={mediaUrl(filmId)} download>Télécharger</a>
            <button type="button" className="st-bouton" onClick={ouvrir}>Plans et montage</button>
            <a className="st-bouton" href="/mode-studio/" title="Montage expert : la vidéo est dans l’onglet Créations">Mode Studio</a>
            <button type="button" className="st-bouton" onClick={() => { setPrisesOuvert(true); void chargerPrises(); }}>Prises</button>
            <button type="button" className="st-bouton" disabled={occupe || montage === 'rend'} onClick={() => void monter()}>{montage === 'rend' ? 'Montage…' : 'Monter'}</button>
            <span className="pr-sep" aria-hidden />
            {VARIANTES.filter((v) => !v.si || v.si(film, film.format ?? format)).map((v) => (
              <button key={v.g} type="button" className="st-bouton" disabled={occupe} onClick={() => variante(v.g)}>{v.label}</button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

const pct = (v: number) => Math.round(v * 100);

/** Aperçu du montage construit par le harnais (code seul) : lecteur, mesures en clair, un tour d'amélioration. */
function ApercuMontage({ vue, occupe, ameliorer, fermer }: { vue: VueMontage; occupe: boolean; ameliorer: () => void; fermer: () => void }) {
  const m = vue.metriques;
  const mesures: [string, number][] = [['Rythme', m.rythme], ['Coupes sur le temps', m.battues], ['Variété des plans', m.doublons], ['Texte', m.texte], ['Audio', m.audio]];
  const fini = vue.tours >= vue.plafondTours;
  return (
    <div className="pr-montage" aria-label="Aperçu du montage">
      <div className="pr-carte-tete">
        <div><span className="st-etiq">Montage sur la musique</span><h4>Score {pct(m.score)} / 100</h4></div>
        <button type="button" className="nx-lien" onClick={fermer}>Fermer</button>
      </div>
      <video key={vue.url + vue.tours} className="pr-montage-video" src={`${vue.url}?v=${vue.tours}`} controls playsInline preload="metadata" />
      <ul className="pr-mesures">
        {mesures.map(([n, v]) => <li key={n}><span>{n}</span><i style={{ ['--v' as string]: `${pct(v)}%` }} /><b>{pct(v)}</b></li>)}
      </ul>
      <p className="pr-meta">
        {m.plans} plans · {vue.dureeS.toFixed(1)} s · {m.dureeMoyennePlanS.toFixed(1)} s par plan · {m.coupesParMinute} coupes/min{m.bpm ? ` · ${Math.round(m.bpm)} BPM` : ''}
        {vue.sonie ? ` · sonie ${vue.sonie.lufs.toFixed(1)} LUFS` : ''}{vue.musique === false ? ' · sans musique' : ''}
      </p>
      {m.ecarts.length > 0 && <ul className="pr-ecarts">{m.ecarts.slice(0, 3).map((e, i) => <li key={i}><small className={e.gravite === 'majeur' || e.gravite === 'bloquant' ? 'bad' : ''}>{e.message}</small></li>)}</ul>}
      {vue.amelioration && <p className="pr-meta" role="status">{vue.amelioration.message}</p>}
      <div className="pr-variantes">
        <button type="button" className="st-bouton primaire" disabled={occupe || fini} onClick={ameliorer}>{occupe ? 'Un instant…' : fini ? 'Montage au maximum' : `Améliorer (${vue.tours}/${vue.plafondTours})`}</button>
        <a className="st-bouton" href={`${vue.url}?v=${vue.tours}`} download>Télécharger l’aperçu</a>
      </div>
      <p className="pr-meta">Aperçu 720p : plans et bande originale ; le son propre des plans n’est pas mixé.</p>
    </div>
  );
}

const nombreFr = (n: number) => Math.round(n).toLocaleString('fr-FR');

/** Prises par plan : brouillons rapides pour choisir, finale cinéma pour la prise gardée, coût du projet avec les écartées. */
function PanneauPrises({ v, occupe, agir, filmId, fermer }: {
  v: VuePrises; occupe: boolean; filmId: number; fermer: () => void;
  agir: (f: () => Promise<VuePrises & { filmId?: number }>, ok: string) => Promise<void>;
}) {
  const c = v.compteur;
  const unite = v.creditsActifs ? 'crédits' : 'crédits estimés';
  return (
    <div className="pr-montage" aria-label="Prises par plan">
      <div className="pr-carte-tete">
        <div><span className="st-etiq">Prises par plan</span>
          <h4>{nombreFr(c.credits)} {unite} · {c.prises} prise{c.prises > 1 ? 's' : ''}</h4></div>
        <button type="button" className="nx-lien" onClick={fermer}>Fermer</button>
      </div>
      <p className="pr-meta" role="status">
        Dont {nombreFr(c.ecartees.credits)} pour {c.ecartees.prises} prise{c.ecartees.prises > 1 ? 's' : ''} écartée{c.ecartees.prises > 1 ? 's' : ''} ou en brouillon : tout ce qui est rendu se paie, gardé ou non. Un échec technique n’est pas facturé.
      </p>
      {v.plans.map((p) => (
        <div key={p.plan} className="pr-prises-plan">
          <div className="pr-prises-tete">
            <b>Plan {p.plan}</b><span>{p.resume}</span>
            <button type="button" className="st-bouton" disabled={occupe} onClick={() => void agir(() => api.brouillonsFilm(filmId, p.plan - 1, 2), '2 brouillons rapides en route.')}>+ 2 brouillons rapides</button>
          </div>
          <div className="pr-prises-grille">
            {p.prises.map((x) => (
              <figure key={x.take} className={`pr-prise${x.retenue ? ' retenue' : ''}${x.rejetee ? ' rejetee' : ''}`}>
                {x.statut === 'done' ? <video src={mediaUrl(x.take)} muted loop playsInline preload="metadata" onMouseEnter={(e) => void e.currentTarget.play().catch(() => {})} onMouseLeave={(e) => e.currentTarget.pause()} /> : <div className="pr-prise-attente">{x.statut === 'failed' ? 'échec' : 'en cours…'}</div>}
                <figcaption>
                  <span>{x.brouillon ? 'Brouillon' : 'Cinéma'}{x.retenue ? ' · gardée' : x.rejetee ? ' · rejetée' : ''}</span>
                  <small>{nombreFr(x.credits)} cr.</small>
                </figcaption>
                {x.statut === 'done' && (
                  <div className="pr-prise-actions">
                    {x.brouillon
                      ? <button type="button" className="st-bouton primaire" disabled={occupe} onClick={() => void agir(() => api.prise(filmId, p.plan - 1, x.take, 'finaliser'), 'Finale en qualité cinéma lancée.')}>Finaliser</button>
                      : !x.retenue && <button type="button" className="st-bouton primaire" disabled={occupe} onClick={() => void agir(() => api.prise(filmId, p.plan - 1, x.take, 'garder'), 'Nouvelle version du film avec cette prise.')}>Garder</button>}
                    {!x.retenue && !x.rejetee && <button type="button" className="st-bouton" disabled={occupe} onClick={() => void agir(() => api.prise(filmId, p.plan - 1, x.take, 'rejeter'), 'Prise rejetée.')}>Rejeter</button>}
                  </div>
                )}
              </figure>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
