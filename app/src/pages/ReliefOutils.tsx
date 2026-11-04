/**
 * Relief : les outils d'un modèle fini. Exports (GLB, OBJ, STL, 3MF, USDZ) avec nombre de faces réglable et contrôle du
 * maillage, cartes PBR, GIF de la tournette et note du juge (quatre côtés). Les exports sont calculés par le serveur :
 * ils ne coûtent aucun crédit GPU.
 */
import { useEffect, useState } from 'react';
import { api, reliefCarteUrl, reliefExportUrl, reliefGifUrl, type FormatRelief, type JugeRelief, type RapportMaillage, type RapportRelief, type Take } from '../api';
import { recreate } from '../Viewer';
import { toast } from '../store';
import { Icon } from '../ui';

const FACES = [{ v: 0, n: 'Plein' }, { v: 100_000, n: '100 k' }, { v: 50_000, n: '50 k' }, { v: 20_000, n: '20 k' }, { v: 10_000, n: '10 k' }, { v: 5_000, n: '5 k' }] as const;
const NOMS_FORMAT: Record<FormatRelief, string> = { glb: 'GLB', obj: 'OBJ', stl: 'STL', '3mf': '3MF', usdz: 'USDZ' };
const AIDE_FORMAT: Record<FormatRelief, string> = {
  glb: 'Le modèle tel quel, textures PBR comprises (web, Stage, Blender, jeux).',
  obj: 'Un zip : .obj, .mtl et la texture de couleur (tous les logiciels 3D).',
  stl: 'Sans couleur, en millimètres, posé à plat : impression 3D.',
  '3mf': 'Sans couleur, en millimètres : trancheurs récents (Bambu, Prusa, Cura).',
  usdz: 'Apple : Quick Look, Vision Pro, Reality Composer.',
};
const n = (x: number) => x.toLocaleString('fr-FR');

export function ResumeMaillage({ r }: { r: RapportMaillage }) {
  return (
    <div className="dim" style={{ fontSize: 12, lineHeight: 1.5 }}>
      <div>{n(r.triangles)} triangles · {n(r.sommets)} sommets · {r.composantes} morceau{r.composantes > 1 ? 'x' : ''}</div>
      <div style={{ color: r.etanche ? 'var(--ok, #3fb950)' : undefined }}>{r.etanche ? 'Étanche : prêt à imprimer' : r.aretesOuvertes > 0 ? `Non étanche (${n(r.aretesOuvertes)} arêtes ouvertes)` : 'Non étanche'}</div>
      {r.avertissements.filter((a) => !/ouvertes/.test(a)).slice(0, 3).map((a) => <div key={a}>{a}</div>)}
    </div>
  );
}

export default function ReliefOutils({ take }: { take: Take }) {
  const [format, setFormat] = useState<FormatRelief>('glb');
  const [faces, setFaces] = useState(0);
  const [info, setInfo] = useState<RapportRelief | null>(null);
  const [cartes, setCartes] = useState<{ nom: string }[]>([]);
  const [juge, setJuge] = useState<JugeRelief | null>(null);
  const [jugement, setJugement] = useState(false);
  useEffect(() => {
    let mort = false;
    setInfo(null);
    api.reliefRapport(take.id, faces || undefined).then((r) => { if (!mort) { setInfo(r); setJuge((j) => j ?? r.juge); } }).catch(() => {});
    return () => { mort = true; };
  }, [take.id, faces]);
  useEffect(() => {
    let mort = false;
    setJuge(null);
    api.reliefCartes(take.id).then((r) => { if (!mort) setCartes(r.cartes); }).catch(() => { if (!mort) setCartes([]); });
    return () => { mort = true; };
  }, [take.id]);

  async function juger() {
    setJugement(true);
    try { setJuge(await api.reliefJuger(take.id)); } catch (e) { toast(e instanceof Error ? e.message : 'Le juge n’a pas répondu', true); } finally { setJugement(false); }
  }
  const affiche = faces && info?.decime ? info.decime : info?.rapport;
  return (
    <div className="relief-outils" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 12, marginTop: 14 }}>
      <div className="rail-section">
        <div className="label">Exporter</div>
        <div className="seg" role="group" aria-label="Format d’export">
          {(['glb', 'obj', 'stl', '3mf', 'usdz'] as const).map((f) => <button key={f} type="button" className={format === f ? 'on' : ''} onClick={() => setFormat(f)}>{NOMS_FORMAT[f]}</button>)}
        </div>
        <div className="dim" style={{ fontSize: 12 }}>{AIDE_FORMAT[format]}</div>
        <div className="label" style={{ textTransform: 'none', letterSpacing: 0 }}>Nombre de faces</div>
        <div className="seg" role="group" aria-label="Nombre de faces">
          {FACES.map((f) => <button key={f.v} type="button" className={faces === f.v ? 'on' : ''} onClick={() => setFaces(f.v)}>{f.n}</button>)}
        </div>
        {affiche ? <ResumeMaillage r={affiche} /> : <div className="dim" style={{ fontSize: 12 }}>Contrôle du maillage…</div>}
        <a className="btn sm accent" href={reliefExportUrl(take.id, format, faces || null)} download><Icon name="download" size={14} />Télécharger en {NOMS_FORMAT[format]}</a>
        <div className="dim" style={{ fontSize: 11.5 }}>Calculé par le serveur : 0 crédit. La décimation garde les textures.</div>
      </div>

      {cartes.length > 0 && (
        <div className="rail-section">
          <div className="label">Cartes PBR</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(72px, 1fr))', gap: 8 }}>
            {cartes.map((c) => (
              <a key={c.nom} href={reliefCarteUrl(take.id, c.nom)} target="_blank" rel="noreferrer" title={`Ouvrir la carte « ${c.nom} »`} style={{ display: 'grid', gap: 3, fontSize: 11 }}>
                <img src={reliefCarteUrl(take.id, c.nom)} alt={`Carte ${c.nom}`} loading="lazy" style={{ width: '100%', aspectRatio: '1', objectFit: 'cover', borderRadius: 8 }} />
                <span className="dim">{c.nom}</span>
              </a>
            ))}
          </div>
        </div>
      )}

      <div className="rail-section">
        <div className="label">Tournette</div>
        <a className="btn sm" href={reliefGifUrl(take.id, true)} download><Icon name="download" size={14} />GIF animé</a>
      </div>

      <div className="rail-section" aria-live="polite">
        <div className="label">Contrôle qualité</div>
        {juge ? (
          <>
            <div style={{ fontSize: 15, fontWeight: 600 }}>{juge.note}/10 <span className="dim" style={{ fontWeight: 400, fontSize: 12 }}>· {juge.note >= 8 ? 'prêt à l’emploi' : juge.note >= 6 ? 'utilisable' : 'à refaire'}</span></div>
            {juge.raison && <div className="dim" style={{ fontSize: 12 }}>{juge.raison}</div>}
            {juge.defauts.length > 0 && <div className="dim" style={{ fontSize: 12 }}>{juge.defauts.join(' · ')}</div>}
            {juge.note < 6 && <button type="button" className="btn sm" onClick={() => void recreate(take)}><Icon name="redo" size={14} />Refaire avec une autre graine</button>}
          </>
        ) : (
          <button type="button" className="btn sm" disabled={jugement} onClick={() => void juger()}><Icon name="sparkle" size={14} />{jugement ? 'Le juge regarde les quatre côtés…' : 'Faire juger sur quatre côtés'}</button>
        )}
      </div>
    </div>
  );
}
