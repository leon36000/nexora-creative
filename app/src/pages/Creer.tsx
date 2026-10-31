/**
 * Nexora Creative — accueil « Créer » : la personne décrit sa vidéo avec ses mots, le studio écrit le scénario
 * (LLM cloud) et le tourne (MiniMax H3). Aucun réglage technique ; le mode expert reste dans Vidéo, Image, Director.
 */
import { useEffect, useMemo, useState } from 'react';
import { api, type CreerReponse, type EtatNexora } from '../api';
import { inFeed, isImage, isModel, toast, useStore } from '../store';
import { MediaCard } from '../ui';
import Viewer from '../Viewer';

type Format = '16:9' | '9:16' | '1:1';
type Duree = 5 | 10 | 15;

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

export default function Creer() {
  const [intention, setIntention] = useState('');
  const [format, setFormat] = useState<Format>('16:9');
  const [duree, setDuree] = useState<Duree>(5);
  const [son, setSon] = useState(true);
  const [envoi, setEnvoi] = useState(false);
  const [dernier, setDernier] = useState<CreerReponse | null>(null);
  const [voirScenario, setVoirScenario] = useState(false);
  const [etat, setEtat] = useState<EtatNexora | null>(null);
  const [vue, setVue] = useState<number | null>(null);
  const takes = useStore((s) => s.takes.filter((t) => inFeed(t) && !isImage(t) && !isModel(t)).slice(0, 12));

  useEffect(() => { void api.nexoraEtat().then(setEtat).catch(() => setEtat(null)); }, []);
  const prete = intention.trim().length > 0 && !envoi;
  const ids = useMemo(() => takes.map((t) => t.id), [takes]);

  async function creer() {
    if (!prete) return;
    setEnvoi(true);
    setVoirScenario(false);
    try {
      const r = await api.nexoraCreer({ intention: intention.trim(), format, duree, son });
      setDernier(r);
      toast(r.source === 'llm' ? 'Scénario écrit, tournage lancé.' : 'Tournage lancé (scénario simplifié : IA indisponible).');
    } catch (e) {
      toast(e instanceof Error ? e.message : 'La création a échoué.', true);
    } finally {
      setEnvoi(false);
    }
  }

  return (
    <div className="nx-creer">
      <section className="nx-hero">
        <h1>Décris ta vidéo. Nexora la tourne.</h1>
        <p className="nx-sous">Écris ce que tu imagines, avec tes mots. L’IA écrit le scénario, choisit les plans, la caméra et le son, puis tourne la vidéo.</p>
        <div className="nx-saisie">
          <textarea
            value={intention}
            onChange={(e) => setIntention(e.target.value)}
            onKeyDown={(e) => { if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') void creer(); }}
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
              {([5, 10, 15] as Duree[]).map((d) => (
                <button key={d} type="button" className={`nx-puce ${duree === d ? 'on' : ''}`} onClick={() => setDuree(d)}>{d} s</button>
              ))}
            </div>
            <button type="button" className={`nx-puce ${son ? 'on' : ''}`} onClick={() => setSon(!son)} aria-pressed={son}>{son ? 'Avec son' : 'Sans son'}</button>
            <button type="button" className="nx-creer-btn" disabled={!prete} onClick={() => void creer()}>
              {envoi ? 'L’IA écrit le scénario…' : 'Créer la vidéo'}
            </button>
          </div>
        </div>
        {!intention && (
          <div className="nx-idees">
            <span>Idées :</span>
            {IDEES.map((i) => <button key={i} type="button" className="nx-idee" onClick={() => setIntention(i)}>{i}</button>)}
          </div>
        )}
        {dernier && (
          <div className="nx-scenario">
            <button type="button" className="nx-lien" onClick={() => setVoirScenario(!voirScenario)}>
              {voirScenario ? 'Masquer' : 'Voir'} le scénario écrit par l’IA {dernier.source === 'repli' ? '(version simplifiée)' : ''}
            </button>
            {voirScenario && <pre>{dernier.prompt}</pre>}
          </div>
        )}
        {etat && !etat.llm && <p className="nx-note">L’assistant d’écriture n’est pas branché sur ce poste : la vidéo sera tournée à partir de ta phrase telle quelle.</p>}
      </section>

      <section className="nx-resultats">
        <h2>Tes vidéos</h2>
        {takes.length === 0 ? <p className="nx-vide">Tes créations apparaîtront ici, avec leur progression en direct.</p> : (
          <div className="grid">
            {takes.map((t) => <MediaCard key={t.id} take={t} onOpen={() => setVue(t.id)} pendingLabel="En file d’attente" />)}
          </div>
        )}
      </section>

      <footer className="nx-pied">Vidéo propulsée par <strong>MiniMax H3</strong> · Scénario par IA · Nexora Creative</footer>
      {vue !== null && <Viewer takeId={vue} onClose={() => setVue(null)} onStep={(d) => {
        const i = ids.indexOf(vue);
        const n = ids[i + d];
        if (n !== undefined) setVue(n);
      }} />}
    </div>
  );
}
