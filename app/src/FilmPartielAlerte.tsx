import type { EchecFilmPartiel } from './api';
import { filmPartielAConsulter, ouvrirCiblePartielle } from './filmPartielActions';
import type { LangueClient } from '../shared/creationLanguage';

export function FilmPartielAlerte({ erreur, langue, rafraichir, existe, ouvrirFilm, ouvrirPrise, indisponible, nouveauFilm }: {
  erreur: EchecFilmPartiel; langue: LangueClient; rafraichir: () => Promise<void>; existe: (id: number) => boolean;
  ouvrirFilm: (id: number) => void; ouvrirPrise: (id: number) => void; indisponible: () => void; nouveauFilm: () => void;
}) {
  const consulter = async (id: number, ouvrir: (id: number) => void) => {
    if (!await ouvrirCiblePartielle(id, rafraichir, existe, ouvrir)) indisponible();
  };
  return <div role="alert">
    <p>{langue === 'en' ? `Film #${erreur.filmId} ${erreur.prises.map((p) => `#${p.takeId}`).join(', ')}: submissions may still be running or need review. Check before retrying.` : `Film n° ${erreur.filmId} ${erreur.prises.map((p) => `#${p.takeId}`).join(', ')} : des prises peuvent encore tourner ou nécessiter une vérification. Vérifie avant de réessayer.`}</p>
    {erreur.conflit && <p>{langue === 'en' ? `Existing film #${erreur.conflit.filmId}, shot #${erreur.conflit.takeId}: check its status.` : `Film existant n° ${erreur.conflit.filmId}, prise n° ${erreur.conflit.takeId} : vérifie son état.`}</p>}
    <button type="button" className="st-bouton" onClick={() => void consulter(filmPartielAConsulter(erreur), ouvrirFilm)}>{langue === 'en' ? 'View shots' : 'Voir les plans'}</button>
    {erreur.prises.map((p) => <button key={p.takeId} type="button" className="st-bouton" onClick={() => void consulter(p.takeId, ouvrirPrise)}>{langue === 'en' ? `View shot ${p.plan + 1}` : `Voir la prise du plan ${p.plan + 1}`}</button>)}
    {erreur.conflit && <button type="button" className="st-bouton" onClick={() => void consulter(erreur.conflit!.takeId, ouvrirPrise)}>{langue === 'en' ? 'View existing shot' : 'Voir la prise existante'}</button>}
    <p>{langue === 'en' ? 'Starting a different film clears this draft; it does not stop existing shots or release credits.' : 'Créer un autre film efface ce brouillon ; cela n’arrête pas les prises existantes et ne libère aucun crédit.'}</p>
    <button type="button" className="st-bouton" onClick={nouveauFilm}>{langue === 'en' ? 'Start a different film' : 'Créer un autre film'}</button>
  </div>;
}
