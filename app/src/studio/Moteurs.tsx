/** État des moteurs GPU dans la barre du haut : points verts (en ligne), orange qui pulse (au travail). */
import { useEffect, useState } from 'react';
import { api, type MoteurGpu } from '../api';
import type { LangueClient } from '../../shared/creationLanguage.js';
import { libellesNavigation } from '../interfaceLanguage.js';

const NOMS: Record<string, { court: string; role: string }> = {
  principal: { court: 'GB10', role: 'principal' },
  rtx5090: { court: 'RTX 5090', role: 'rtx5090' },
};

function classePoint(m: MoteurGpu): string {
  if (!m.enLigne) return '';
  return m.enCours ? 'busy' : 'on';
}

function infobulle(m: MoteurGpu, copy: ReturnType<typeof libellesNavigation>): string {
  const etat = m.enLigne ? copy.gpu.online : copy.gpu.offline;
  const taches = m.enCours ? `, ${copy.gpu.tasks(m.enCours)}` : '';
  return `${m.nom}: ${etat}${taches} · ${m.recettes.join(', ')}`;
}

export function Moteurs({ langue = 'fr' }: { langue?: LangueClient } = {}) {
  const [moteurs, setMoteurs] = useState<MoteurGpu[]>([]);
  const copy = libellesNavigation(langue);
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
        const role = n.role ? copy.gpu.roles[n.role] ?? n.role : '';
        return (
          <span key={m.id} className="st-gpu" title={infobulle(m, copy)}>
            <i className={`st-dot ${classePoint(m)}`} />
            <b>{n.court}</b>
            <span className="long">{role}</span>
          </span>
        );
      })}
    </>
  );
}
