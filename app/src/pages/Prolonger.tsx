/**
 * Prolonger et Raccord (MiniMax H3) : remplacent Extend et Transitions d'OpenField, qui reposaient sur LTX.
 * Prolonger : le clip continue depuis sa dernière image. Raccord : un plan va de la dernière image d'un clip à la
 * première d'un autre, puis les trois s'assemblent. Seul le nouveau plan est tourné et facturé.
 */
import { useMemo, useState } from 'react';
import { posterUrl } from '../api';
import { setParams, useRoute } from '../router';
import { isImage, isModel, settingsOf, toast, useStore } from '../store';
import { MediaCard } from '../ui';
import FilmPlans from '../FilmPlans';
import { IcRond } from '../studio/icons';

async function poster<T>(url: string, corps: unknown): Promise<T> {
  const r = await fetch(url, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(corps) });
  const d = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(d?.error ?? `HTTP ${r.status}`);
  return d as T;
}

export default function Prolonger() {
  const { params } = useRoute();
  const raccord = params.get('mode') === 'raccord';
  const [choix, setChoix] = useState<number[]>(() => (params.get('take') ? [Number(params.get('take'))] : []));
  const [intention, setIntention] = useState('');
  const [duree, setDuree] = useState<5 | 10>(5);
  const [envoi, setEnvoi] = useState(false);
  const [ouvert, setOuvert] = useState<number | null>(null);
  // Clips terminés, y compris les plans des films (pas les films assemblés eux-mêmes).
  const clips = useStore((s) => s.takes.filter((t) => t.kind === 'video' && t.status === 'done' && !isImage(t) && !isModel(t) && !settingsOf(t).film && settingsOf(t).app !== 'nexora-raccord').slice(0, 30));
  const resultats = useStore((s) => s.takes.filter((t) => settingsOf(t).app === 'nexora-raccord').slice(0, 6));
  const max = raccord ? 2 : 1;
  const pret = choix.length === max && !envoi;
  const nom = useMemo(() => new Map(clips.map((t) => [t.id, String(settingsOf(t).intention ?? t.shot_name).slice(0, 60)])), [clips]);

  function basculer(id: number) {
    setChoix((c) => (c.includes(id) ? c.filter((x) => x !== id) : [...c, id].slice(-max)));
  }

  async function lancer() {
    setEnvoi(true);
    try {
      if (raccord) await poster('/api/nexora/raccord', { de: choix[0], vers: choix[1], intention: intention.trim() || undefined });
      else await poster('/api/nexora/prolonger', { take: choix[0], intention: intention.trim() || undefined, duree });
      toast(raccord ? 'Raccord lancé : le plan de transition se tourne, puis les trois s’assemblent.' : 'Suite lancée : elle part de la dernière image, puis s’assemble au clip.');
      setChoix([]);
      setIntention('');
    } catch (e) {
      toast(e instanceof Error ? e.message : 'Lancement impossible.', true);
    } finally {
      setEnvoi(false);
    }
  }

  return (
    <div className="st">
      <section className="st-hero">
        <div>
          <h1>{raccord ? <>Raccorde <em>deux clips</em>.</> : <>Prolonge <em>un clip</em>.</>}</h1>
          <p>{raccord
            ? 'Choisis deux vidéos dans l’ordre. MiniMax H3 tourne un plan qui part de la dernière image de la première et arrive sur la première image de la seconde.'
            : 'Choisis une vidéo. MiniMax H3 la continue depuis sa dernière image : mêmes sujets, même lumière, même mouvement.'}</p>
        </div>
        <div className="st-filtres" role="group" aria-label="Outil">
          <button type="button" className={!raccord ? 'on' : ''} onClick={() => { setParams({ mode: null }); setChoix([]); }}>Prolonger</button>
          <button type="button" className={raccord ? 'on' : ''} onClick={() => { setParams({ mode: 'raccord', take: null }); setChoix([]); }}>Raccord</button>
        </div>
      </section>

      <div className="st-grid">
        <aside className="st-composer" aria-label="Réglages">
          <div className="st-bloc">
            <span className="st-etiq">{raccord ? 'Clips choisis (dans l’ordre)' : 'Clip choisi'}</span>
            <div className="pl-choix">
              {Array.from({ length: max }, (_, i) => choix[i]).map((id, i) => (
                <div key={i} className={`pl-case ${id ? 'pleine' : ''}`}>
                  {id ? <><img src={posterUrl(id)} alt="" /><span>{nom.get(id) ?? `Vidéo ${id}`}</span><button type="button" className="nx-lien" onClick={() => basculer(id)}>Retirer</button></>
                    : <span className="pl-vide">{raccord ? (i === 0 ? '1. Clip de départ' : '2. Clip d’arrivée') : 'Choisis un clip à droite'}</span>}
                </div>
              ))}
            </div>
          </div>
          <div className="st-champ">
            <textarea value={intention} onChange={(e) => setIntention(e.target.value)} maxLength={1200} style={{ minHeight: 90 }}
              placeholder={raccord ? 'Facultatif : comment passer de l’un à l’autre (« la caméra traverse la fenêtre »)…' : 'Facultatif : ce qui se passe ensuite (« elle se retourne et sourit »)…'} aria-label="Ce qui se passe" />
          </div>
          {!raccord && (
            <div className="st-bloc">
              <span className="st-etiq">Durée ajoutée</span>
              <div className="st-seg" role="group" aria-label="Durée">
                {([5, 10] as const).map((d) => <button key={d} type="button" className={duree === d ? 'on' : ''} onClick={() => setDuree(d)}>+{d} s</button>)}
              </div>
            </div>
          )}
          <div className="st-cta">
            <button type="button" className="st-go" disabled={!pret} onClick={() => void lancer()}>{envoi ? <><IcRond /> Lancement…</> : raccord ? 'Tourner le raccord' : `Prolonger de ${duree} s`}</button>
            <p className="st-credit">Un seul nouveau plan est tourné (MiniMax H3) ; le résultat s’assemble tout seul.</p>
          </div>
        </aside>

        <section className="st-galerie" aria-label="Tes vidéos">
          {resultats.length > 0 && <>
            <div className="st-g-tete"><h2>Résultats</h2></div>
            <div className="st-cartes">{resultats.map((t) => <MediaCard key={t.id} take={t} onOpen={() => setOuvert(t.id)} tag={raccord ? 'Raccord' : 'Prolongé'} pendingLabel="Tournage du nouveau plan" />)}</div>
          </>}
          <div className="st-g-tete"><h2>Tes vidéos</h2><span className="dim" style={{ fontSize: 13 }}>{raccord ? 'Clique deux vidéos, dans l’ordre.' : 'Clique la vidéo à prolonger.'}</span></div>
          {clips.length === 0 ? (
            <div className="st-vide"><strong>Aucune vidéo terminée pour l’instant.</strong><span>Crée d’abord un clip dans Créer, il apparaîtra ici.</span></div>
          ) : (
            <div className="st-cartes">
              {clips.map((t) => {
                const rang = choix.indexOf(t.id);
                return (
                  <div key={t.id} className={`pl-clip ${rang >= 0 ? 'choisi' : ''}`}>
                    <MediaCard take={t} onOpen={() => basculer(t.id)} tag={rang >= 0 ? (raccord ? `${rang + 1}` : 'Choisi') : undefined} />
                  </div>
                );
              })}
            </div>
          )}
        </section>
      </div>
      {ouvert !== null && <FilmPlans filmId={ouvert} onClose={() => setOuvert(null)} />}
    </div>
  );
}
