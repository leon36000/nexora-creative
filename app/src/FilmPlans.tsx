/**
 * Nexora Creative — les plans d'un film : état, contrôle qualité, aperçu, et « Refaire ce plan » (une nouvelle version
 * du film ne retourne que ce plan et ceux qui s'enchaînaient dessus).
 */
import { useState } from 'react';
import { api, mediaUrl, posterUrl } from './api';
import { settingsOf, toast, useStore } from './store';

interface Plan { resume: string; description: string; duree: number; camera: string; suite?: boolean; take?: number; controle?: { ok: boolean; defauts: string[] }; reprises?: number }

export default function FilmPlans({ filmId, onClose }: { filmId: number; onClose: () => void }) {
  const film = useStore((s) => s.takes.find((t) => t.id === filmId));
  const toutes = useStore((s) => s.takes);
  const [edition, setEdition] = useState<Record<number, string>>({});
  const [envoi, setEnvoi] = useState<number | null>(null);
  const [ordre, setOrdre] = useState<number[] | null>(null);
  const [transition, setTransition] = useState<'coupe' | 'fondu'>('coupe');
  if (!film) return null;
  const s = settingsOf(film);
  const plans = (s.storyboard?.plans ?? []) as Plan[];
  const montage = ordre ?? plans.map((_, i) => i);
  const deplacer = (k: number, d: -1 | 1) => {
    const o = [...montage];
    const j = k + d;
    if (j < 0 || j >= o.length) return;
    [o[k], o[j]] = [o[j], o[k]];
    setOrdre(o);
  };

  async function remonter() {
    try {
      await api.nexoraFilmMontage(filmId, { ordre: montage, transition });
      toast('Nouvelle version en assemblage (aucun nouveau rendu).');
      onClose();
    } catch (e) {
      toast(e instanceof Error ? e.message : 'Le montage a échoué.', true);
    }
  }

  async function refaire(i: number) {
    setEnvoi(i);
    try {
      await api.nexoraFilmRefaire(filmId, { plan: i, description: edition[i] });
      toast(`Plan ${i + 1} en retournage : une nouvelle version du film s’assemblera toute seule.`);
      onClose();
    } catch (e) {
      toast(e instanceof Error ? e.message : 'Impossible de refaire ce plan.', true);
    } finally {
      setEnvoi(null);
    }
  }

  const occupe = film.status === 'queued' || film.status === 'rendering';
  return (
    <div className="nx-voile" role="dialog" aria-modal="true" aria-label={`Plans du film ${s.storyboard?.titre ?? ''}`} onClick={onClose}>
      <div className="nx-panneau" onClick={(e) => e.stopPropagation()}>
        <div className="nx-sb-tete">
          <div>
            <h2>{s.storyboard?.titre ?? 'Film'}</h2>
            <p className="nx-sous">{plans.length} plans · {occupe ? 'en tournage' : film.status === 'done' ? 'assemblé' : film.status}{s.versionDe ? ` · version refaite du film n° ${s.versionDe}` : ''}</p>
          </div>
          <button type="button" className="nx-lien" onClick={onClose}>Fermer</button>
        </div>
        {film.status === 'done' && <video className="nx-film-video" src={mediaUrl(film.id)} poster={posterUrl(film.id)} controls playsInline />}
        {film.status === 'done' && (
          <div className="nx-montage">
            <strong>Montage</strong>
            <ol>
              {montage.map((i, k) => (
                <li key={i}>
                  <span>{k + 1}. {plans[i].resume}</span>
                  <button type="button" className="nx-lien" onClick={() => deplacer(k, -1)} disabled={k === 0} aria-label="Monter">↑</button>
                  <button type="button" className="nx-lien" onClick={() => deplacer(k, 1)} disabled={k === montage.length - 1} aria-label="Descendre">↓</button>
                  <button type="button" className="nx-lien" onClick={() => setOrdre(montage.filter((x) => x !== i))} disabled={montage.length <= 1}>Retirer</button>
                </li>
              ))}
            </ol>
            <div className="nx-options">
              <div className="nx-groupe">
                <button type="button" className={`nx-puce ${transition === 'coupe' ? 'on' : ''}`} onClick={() => setTransition('coupe')}>Coupe franche</button>
                <button type="button" className={`nx-puce ${transition === 'fondu' ? 'on' : ''}`} onClick={() => setTransition('fondu')}>Fondu enchaîné</button>
              </div>
              <button type="button" className="nx-puce on" onClick={() => void remonter()}>Créer cette version</button>
              <a className="nx-puce" href={`/api/nexora/film/${film.id}/export`} download>Exporter en ProRes (.mov)</a>
              <a className="nx-puce" href={mediaUrl(film.id)} download>Télécharger le MP4</a>
              <a className="nx-puce" href={`/api/nexora/film/${film.id}/projet`} download>Projet Premiere / DaVinci (.zip)</a>
            </div>
          </div>
        )}
        <ol className="nx-plans">
          {plans.map((p, i) => {
            const t = p.take ? toutes.find((x) => x.id === p.take) : undefined;
            const etat = !t ? (p.suite ? 'attend la fin du plan précédent' : 'en préparation') : t.status === 'done' ? 'tourné' : t.status === 'failed' ? 'échec' : 'en tournage';
            return (
              <li key={i} className="nx-plan">
                <div className="nx-plan-num">{i + 1}</div>
                <div className="nx-plan-corps">
                  <strong>{p.resume}</strong>
                  {t?.status === 'done' && <video className="nx-plan-video" src={mediaUrl(t.id)} poster={posterUrl(t.id)} muted loop playsInline onMouseEnter={(e) => void e.currentTarget.play().catch(() => {})} onMouseLeave={(e) => e.currentTarget.pause()} />}
                  <span className="nx-camera">{p.duree} s · {etat}{p.suite ? ' · enchaîné' : ''}{p.controle ? (p.controle.ok ? ' · contrôle OK' : ` · à revoir : ${p.controle.defauts.join(', ')}`) : ''}{p.reprises ? ' · repris automatiquement' : ''}</span>
                  {!occupe && (
                    <>
                      <textarea rows={2} value={edition[i] ?? p.description} onChange={(e) => setEdition({ ...edition, [i]: e.target.value })} aria-label={`Nouvelle description du plan ${i + 1}`} />
                      <button type="button" className="nx-puce on" disabled={envoi !== null} onClick={() => void refaire(i)}>{envoi === i ? 'Envoi…' : 'Refaire ce plan'}</button>
                    </>
                  )}
                </div>
              </li>
            );
          })}
        </ol>
      </div>
    </div>
  );
}
