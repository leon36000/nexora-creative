/**
 * Projet long : un scénario devient séquences → scènes → plans ; la bible de continuité est injectée dans chaque plan ;
 * le coût du projet entier est annoncé avant tout rendu ; les plans partent par lots ; les plans tournés se montent dans la
 * timeline du Mode Studio. Aucune limite de longueur (90 minutes = 1 080 plans de 5 s). Voir server/nexora/projet.ts.
 */
import { useEffect, useState } from 'react';
import { api, type ArbreProjet, type ResumeProjet } from '../api';
import { toast } from '../store';

const MODELE = `SÉQUENCE 1 : Le retour

INT. CAFÉ DU PORT - NUIT
Mara entre dans le café désert, la pluie ruisselle sur son manteau vert.

Elle s’assoit au comptoir et pose une vieille clé sur le zinc.

EXT. QUAI - AUBE
Le brouillard se lève sur les bateaux. Mara marche seule le long de l’eau.`;

const nombre = (n: number) => Math.round(n).toLocaleString('fr-FR');
const duree = (s: number) => (s < 60 ? `${Math.round(s)} s` : s >= 3600 ? `${Math.floor(s / 3600)} h ${String(Math.round((s % 3600) / 60)).padStart(2, '0')}` : `${Math.round(s / 60)} min`);

export default function ProjetPage() {
  const [projets, setProjets] = useState<ResumeProjet[]>([]);
  const [courant, setCourant] = useState<string | null>(null);
  const [detail, setDetail] = useState<Awaited<ReturnType<typeof api.projet>> | null>(null);
  const [titre, setTitre] = useState('');
  const [scenario, setScenario] = useState('');
  const [style, setStyle] = useState('');
  const [qualite, setQualite] = useState<'rapide' | 'max'>('max');
  const [occupe, setOccupe] = useState(false);

  const charger = async () => { try { setProjets(await api.projets()); } catch { /* liste vide */ } };
  useEffect(() => { void charger(); }, []);
  useEffect(() => { if (courant) void api.projet(courant).then(setDetail, () => setDetail(null)); else setDetail(null); }, [courant, projets]);

  async function creer() {
    setOccupe(true);
    try { const p = await api.creerProjet({ titre, scenario, format: '16:9', qualite, bible: { style } }); await charger(); setCourant(p.id); setTitre(''); }
    catch (e) { toast(e instanceof Error ? e.message : 'Création impossible.', true); }
    finally { setOccupe(false); }
  }
  async function lancer(taille: number) {
    if (!courant) return;
    setOccupe(true);
    try { const r = await api.lancerProjet(courant, taille); toast(`${r.lances} plan${r.lances > 1 ? 's' : ''} au tournage.`); await charger(); }
    catch (e) { toast(e instanceof Error ? e.message : 'Lancement impossible.', true); }
    finally { setOccupe(false); }
  }
  const e = detail?.estimation;
  const unite = detail?.creditsActifs ? 'crédits' : 'crédits estimés';
  return (
    <div className="page-scroll">
      <div className="page-pad" style={{ maxWidth: 1200 }}>
        <h1 className="display" style={{ fontSize: 'clamp(36px,4.6vw,64px)', margin: '8px 0 6px' }}>Projets <span className="hl">longs</span></h1>
        <p className="dim" style={{ maxWidth: 720 }}>Colle un scénario : séquences, scènes (INT./EXT.) et paragraphes d’action. Nexora découpe en plans, garde la même bible de continuité dans chacun, chiffre le projet entier avant de tourner, et tourne par lots.</p>

        <div className="projet-grille">
          <section className="fiche-ia" aria-label="Nouveau projet">
            <div className="fiche-ia-champs" style={{ gridColumn: '1 / -1' }}>
              <input value={titre} onChange={(ev) => setTitre(ev.target.value)} placeholder="Titre du projet" aria-label="Titre du projet" maxLength={120} />
              <input value={style} onChange={(ev) => setStyle(ev.target.value)} placeholder="Style de la bible (ex. cinéma naturaliste, grain fin, lumière de nuit)" aria-label="Style" maxLength={400} />
              <textarea value={scenario} onChange={(ev) => setScenario(ev.target.value)} rows={8} placeholder={MODELE} aria-label="Scénario" />
              <div className="pr-variantes">
                <div className="st-seg" role="group" aria-label="Qualité">
                  <button type="button" className={qualite === 'max' ? 'on' : ''} onClick={() => setQualite('max')}>Cinéma (personnages @)</button>
                  <button type="button" className={qualite === 'rapide' ? 'on' : ''} onClick={() => setQualite('rapide')}>Rapide</button>
                </div>
                <button type="button" className="btn accent" disabled={occupe || !titre.trim() || scenario.trim().length < 20} onClick={() => void creer()}>Découper et chiffrer</button>
              </div>
            </div>
          </section>

          <section aria-label="Projets">
            {projets.map((p) => (
              <button key={p.id} type="button" className={`projet-ligne${p.id === courant ? ' on' : ''}`} onClick={() => setCourant(p.id)}>
                <b>{p.titre}</b><span>{p.tournes}/{p.plans} plans tournés</span>
              </button>
            ))}
            {!projets.length && <p className="dim">Aucun projet pour l’instant.</p>}
          </section>
        </div>

        {detail && e && (
          <section className="pr-montage" aria-label="Projet courant">
            <div className="pr-carte-tete"><div><span className="st-etiq">Projet</span><h4>{detail.titre}</h4></div></div>
            <p className="pr-meta">
              {e.sequences} séquence{e.sequences > 1 ? 's' : ''} · {e.scenes} scène{e.scenes > 1 ? 's' : ''} · {nombre(e.plans)} plans · {duree(e.dureeS)} de film
            </p>
            <div className="pr-devis" style={{ gridTemplateColumns: 'repeat(3, auto) 1fr' }}>
              <div><span className="st-etiq">Coût restant</span><b>{nombre(e.credits)} {unite}</b></div>
              <div><span className="st-etiq">Calcul vidéo</span><b>≈ {e.heuresGpu} h</b></div>
              <div><span className="st-etiq">Reste à tourner</span><b>{nombre(e.restants)} plans{e.enCours ? ` (+ ${e.enCours} en cours)` : ''}</b></div>
              <div className="pr-variantes">
                <button type="button" className="st-go" disabled={occupe || !e.restants} onClick={() => void lancer(8)}>Tourner les 8 prochains plans</button>
                <a className="st-bouton" href="/mode-studio/" title="Les plans tournés se montent dans la timeline : panneau Créations, « Projets longs »">Monter dans le Mode Studio</a>
              </div>
            </div>
            <p className="pr-meta">Bible : {detail.bible.style || 'style libre'} · {detail.bible.personnages.length} personnage{detail.bible.personnages.length > 1 ? 's' : ''} (les personnages @ gardent leur visage en qualité cinéma).</p>
            <Arbre arbre={detail.arbre} />
          </section>
        )}
      </div>
    </div>
  );
}

function Arbre({ arbre }: { arbre: ArbreProjet[] }) {
  return (
    <div className="projet-arbre">
      {arbre.map((s) => (
        <details key={s.id} open={arbre.length <= 3}>
          <summary><b>{s.titre}</b> · {s.scenes.reduce((n, c) => n + c.plans.length, 0)} plans</summary>
          {s.scenes.map((c) => (
            <details key={c.id}>
              <summary>{c.titre} · {c.plans.length} plan{c.plans.length > 1 ? 's' : ''}</summary>
              <ol>{c.plans.map((p) => <li key={p.id} className={p.etat}>{p.resume} <small>{p.duree} s · {p.etat === 'tourne' ? 'tourné' : p.etat === 'en_cours' ? 'au tournage' : p.etat === 'echec' ? 'échec' : 'à tourner'}</small></li>)}</ol>
            </details>
          ))}
        </details>
      ))}
    </div>
  );
}
