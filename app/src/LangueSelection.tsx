import type { LangueClient } from '../shared/creationLanguage';

type Props = Readonly<{
  mode: string; langue: LangueClient; libelle: string; occupe: boolean; filmPartiel: boolean;
  choisir: (langue: LangueClient) => void;
}>;

export function LangueSelection({ mode, langue, libelle, occupe, filmPartiel, choisir }: Props) {
  if (mode !== 'video' && mode !== 'film') return null;
  const nomFilm = langue === 'en' ? 'Film and dialogue language' : 'Langue du film et des dialogues';
  const nom = mode === 'film' ? nomFilm : libelle;
  const bloque = mode === 'film' && (occupe || filmPartiel);
  return <div className="st-bloc">
    <span className="st-etiq">{nom}</span>
    <fieldset className="st-seg" aria-label={nom}>
      <button type="button" className={langue === 'fr' ? 'on' : ''} aria-pressed={langue === 'fr'} disabled={bloque} onClick={() => choisir('fr')}>Français</button>
      <button type="button" className={langue === 'en' ? 'on' : ''} aria-pressed={langue === 'en'} disabled={bloque} onClick={() => choisir('en')}>English</button>
    </fieldset>
  </div>;
}
