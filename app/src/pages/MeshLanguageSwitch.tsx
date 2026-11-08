import type { LangueClient } from '../../shared/creationLanguage';
import { meshCopy } from '../meshCopy';

export function MeshLanguageSwitch({ langue, onChange }: { langue: LangueClient; onChange: (langue: LangueClient) => void }) {
  const copy = meshCopy(langue);
  return (
    <div className="seg" role="group" aria-label={copy.languageSwitch}>
      <button type="button" className={langue === 'fr' ? 'on' : ''} aria-pressed={langue === 'fr'} onClick={() => onChange('fr')}>{copy.french}</button>
      <button type="button" className={langue === 'en' ? 'on' : ''} aria-pressed={langue === 'en'} onClick={() => onChange('en')}>{copy.english}</button>
    </div>
  );
}
