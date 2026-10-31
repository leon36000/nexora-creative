/** Fenêtre « Texte pour les réseaux » : titre, texte et hashtags écrits par le LLM pour une création, prêts à copier. */
import { useEffect, useState } from 'react';
import { api } from '../api';
import { toast } from '../store';

const PLATEFORMES = [['instagram', 'Instagram'], ['tiktok', 'TikTok'], ['youtube', 'YouTube'], ['linkedin', 'LinkedIn'], ['x', 'X']] as const;
type Res = { titre: string; texte: string; hashtags: string[]; mention: string; source: 'llm' | 'repli' };

export function Publication({ id, onClose }: { id: number; onClose: () => void }) {
  const [plateforme, setPlateforme] = useState<string>('instagram');
  const [langue, setLangue] = useState<'fr' | 'en'>('fr');
  const [res, setRes] = useState<Res | null>(null);
  const [charge, setCharge] = useState(true);
  useEffect(() => {
    let actif = true;
    setCharge(true);
    api.nexoraPublication({ id, plateforme, langue }).then((r) => actif && setRes(r)).catch((e) => { if (actif) toast(e instanceof Error ? e.message : 'Impossible d’écrire le texte.', true); }).finally(() => actif && setCharge(false));
    return () => { actif = false; };
  }, [id, plateforme, langue]);
  const complet = res ? `${res.titre}\n\n${res.texte}\n\n${res.hashtags.join(' ')}\n\n${res.mention}` : '';
  const copier = (t: string) => { void navigator.clipboard?.writeText(t).then(() => toast('Copié.')).catch(() => toast('Copie impossible : sélectionne le texte.', true)); };
  return (
    <div className="nx-voile" role="dialog" aria-modal="true" aria-label="Texte pour les réseaux" onClick={onClose}>
      <div className="nx-panneau" style={{ maxWidth: 640 }} onClick={(e) => e.stopPropagation()}>
        <div className="nx-sb-tete">
          <div><h2>Texte pour les réseaux</h2><p className="nx-sous" style={{ margin: 0 }}>Écrit par l’assistant, prêt à coller avec ta vidéo.</p></div>
          <button type="button" className="st-bouton" onClick={onClose}>Fermer</button>
        </div>
        <div className="st-seg" role="group" aria-label="Réseau">
          {PLATEFORMES.map(([v, label]) => <button key={v} type="button" className={plateforme === v ? 'on' : ''} onClick={() => setPlateforme(v)}>{label}</button>)}
        </div>
        <div className="st-seg" role="group" aria-label="Langue" style={{ maxWidth: 200 }}>
          <button type="button" className={langue === 'fr' ? 'on' : ''} onClick={() => setLangue('fr')}>Français</button>
          <button type="button" className={langue === 'en' ? 'on' : ''} onClick={() => setLangue('en')}>English</button>
        </div>
        {charge || !res ? <p className="nx-sous">L’assistant écrit…</p> : (
          <div className="st-suggestion">
            <span className="st-etiq">Titre</span><p><strong>{res.titre}</strong></p>
            <span className="st-etiq">Texte</span><p>{res.texte}</p>
            <span className="st-etiq">Hashtags</span><p>{res.hashtags.join(' ') || '—'}</p>
            <span className="st-etiq">Mention</span><p style={{ color: 'var(--dim)' }}>{res.mention}</p>
            <div className="st-ligne">
              <button type="button" className="st-bouton primaire" onClick={() => copier(complet)}>Tout copier</button>
              <button type="button" className="st-bouton" onClick={() => copier(res.texte)}>Copier le texte</button>
              {res.source === 'repli' && <span className="st-credit">Version simple : l’assistant est indisponible.</span>}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
