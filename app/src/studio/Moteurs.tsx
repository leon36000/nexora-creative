/** État des moteurs GPU dans la barre du haut : points verts (en ligne), orange qui pulse (au travail). */
import { useEffect, useState } from 'react';
import { api, type MoteurGpu } from '../api';

const NOMS: Record<string, { court: string; role: string }> = {
  principal: { court: 'GB10', role: 'Image · Musique' },
  rtx5090: { court: 'RTX 5090', role: 'MiniMax H3' },
};

export function Moteurs() {
  const [moteurs, setMoteurs] = useState<MoteurGpu[]>([]);
  useEffect(() => {
    let actif = true;
    const lire = () => api.nexoraMoteursGpu().then((m) => actif && setMoteurs(m)).catch(() => actif && setMoteurs([]));
    void lire();
    const t = setInterval(lire, 8000);
    return () => { actif = false; clearInterval(t); };
  }, []);
  return (
    <>
      {moteurs.map((m) => {
        const n = NOMS[m.id] ?? { court: m.nom, role: '' };
        return (
          <span key={m.id} className="st-gpu" title={`${m.nom} : ${m.enLigne ? 'en ligne' : 'hors ligne'}${m.enCours ? `, ${m.enCours} tâche(s)` : ''} · ${m.recettes.join(', ')}`}>
            <i className={`st-dot ${m.enLigne ? (m.enCours ? 'busy' : 'on') : ''}`} />
            <b>{n.court}</b>
            <span className="long">{n.role}</span>
          </span>
        );
      })}
    </>
  );
}
