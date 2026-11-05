/** Mesh exports, topology report, PBR maps, turntable GIF and four-view judge. */
import { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { api, reliefCarteUrl, reliefExportUrl, reliefGifUrl, type FormatRelief, type JugeRelief, type RapportMaillage, type RapportRelief, type Take } from '../api';
import { recreate } from '../Viewer';
import { toast } from '../store';
import { Icon } from '../ui';
import type { LangueClient } from '../../shared/creationLanguage';
import { avertissementMaillage, meshCopy, meshNumber } from '../meshCopy';

const FORMATS: FormatRelief[] = ['glb', 'obj', 'stl', '3mf', 'usdz'];
const FACES = [0, 100_000, 50_000, 20_000, 10_000, 5_000] as const;
const NOMS_FORMAT: Record<FormatRelief, string> = { glb: 'GLB', obj: 'OBJ', stl: 'STL', '3mf': '3MF', usdz: 'USDZ' };

function nomFaces(v: number, langue: LangueClient): string {
  if (v === 0) return langue === 'fr' ? 'Plein' : 'Full model';
  return `${meshNumber(v / 1000, langue)} k`;
}

export function ResumeMaillage({ r, langue = 'fr' }: { r: RapportMaillage; langue?: LangueClient }) {
  const c = meshCopy(langue);
  const orientationIncoherente = r.avertissements.includes('Volume non calculé : orientation incohérente des faces.');
  const summary = r.etanche
    ? orientationIncoherente ? c.summaryInconsistent : c.summaryClosed
    : r.aretesOuvertes > 0 ? c.summaryOpen(meshNumber(r.aretesOuvertes, langue)) : c.summaryNotWatertight;
  return (
    <div className="dim" style={{ fontSize: 12, lineHeight: 1.5 }}>
      <div>{meshNumber(r.triangles, langue)} triangles · {meshNumber(r.sommets, langue)} {c.vertices} · {c.summaryComponents(meshNumber(r.composantes, langue), r.composantes > 1)}</div>
      <div style={{ color: r.etanche && !orientationIncoherente ? 'var(--ok, #3fb950)' : undefined }}>{summary}</div>
      {r.avertissements.filter((a) => !/ouvertes/.test(a)).slice(0, 3).map((a, i) => <div key={`${i}-${a}`}>{avertissementMaillage(a, langue)}</div>)}
    </div>
  );
}

export function EtatAnalyseMaillage({ rapport, loading, failed, langue = 'fr' }: {
  rapport: RapportMaillage | null; loading: boolean; failed: boolean; langue?: LangueClient;
}) {
  const c = meshCopy(langue);
  if (failed) return <div role="alert" className="dim" style={{ fontSize: 12, color: 'var(--danger, #e5534b)' }}>{c.reportFailure}</div>;
  if (rapport) return <ResumeMaillage r={rapport} langue={langue} />;
  if (loading) return <div role="status" className="dim" style={{ fontSize: 12 }}>{c.reportLoading}</div>;
  return null;
}

export default function ReliefOutils({ take, langue }: { take: Take; langue: LangueClient }) {
  const [format, setFormat] = useState<FormatRelief>('glb');
  const [faces, setFaces] = useState(0);
  // Each model keeps its report; export preferences are shared between models.
  return <ReliefOutilsModele key={take.id} take={take} format={format} setFormat={setFormat} faces={faces} setFaces={setFaces} langue={langue} />;
}

function ReliefOutilsModele({ take, format, setFormat, faces, setFaces, langue }: Readonly<{
  take: Take; format: FormatRelief; setFormat: (format: FormatRelief) => void; faces: number;
  setFaces: (faces: number) => void; langue: LangueClient;
}>) {
  const c = meshCopy(langue);
  const vivant = useRef(false);
  useLayoutEffect(() => {
    vivant.current = true;
    return () => { vivant.current = false; };
  }, []);
  const [info, setInfo] = useState<RapportRelief | null>(null);
  const [erreurRapport, setErreurRapport] = useState(false);
  const [cartes, setCartes] = useState<{ nom: string }[]>([]);
  const [juge, setJuge] = useState<JugeRelief | null>(null);
  const [jugement, setJugement] = useState(false);
  useEffect(() => {
    let mort = false;
    setInfo(null);
    setErreurRapport(false);
    api.reliefRapport(take.id, faces || undefined)
      .then((r) => { if (!mort) { setInfo(r); setJuge((j) => j ?? r.juge); } })
      .catch(() => { if (!mort) { setInfo(null); setErreurRapport(true); } });
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
    try {
      const resultat = await api.reliefJuger(take.id);
      if (vivant.current) setJuge(resultat);
    } catch {
      if (vivant.current) toast(c.judgeUnavailable, true);
    } finally {
      if (vivant.current) setJugement(false);
    }
  }
  const affiche = faces && info?.decime ? info.decime : info?.rapport;
  const urlExport = reliefExportUrl(take.id, format, faces || null);
  return (
    <div className="relief-outils" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: 12, marginTop: 14 }}>
      <div className="rail-section">
        <div className="label">{c.export}</div>
        <div className="seg" role="group" aria-label={c.exportFormat}>
          {FORMATS.map((f) => <button key={f} type="button" className={format === f ? 'on' : ''} onClick={() => setFormat(f)}>{NOMS_FORMAT[f]}</button>)}
        </div>
        <div className="dim" style={{ fontSize: 12 }}>{format === 'glb' ? c.helpGlb : format === 'obj' ? c.helpObj : format === 'stl' ? c.helpStl : format === '3mf' ? c.help3mf : c.helpUsdz}</div>
        <div className="label" style={{ textTransform: 'none', letterSpacing: 0 }}>{c.numberOfFaces}</div>
        <div className="seg" role="group" aria-label={c.numberOfFaces}>
          {FACES.map((v) => <button key={v} type="button" className={faces === v ? 'on' : ''} onClick={() => setFaces(v)}>{nomFaces(v, langue)}</button>)}
        </div>
        <EtatAnalyseMaillage rapport={affiche ?? null} loading={!info && !erreurRapport} failed={erreurRapport} langue={langue} />
        {erreurRapport
          ? <span className="btn sm accent" aria-disabled="true"><Icon name="download" size={14} />{c.exportUnavailable}</span>
          : <a className="btn sm accent" href={urlExport} download><Icon name="download" size={14} />{c.export} {NOMS_FORMAT[format]}</a>}
        <div className="dim" style={{ fontSize: 11.5 }}>{c.serverNoCredits}</div>
      </div>

      {cartes.length > 0 && (
        <div className="rail-section">
          <div className="label">{c.pbrMaps}</div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(72px, 1fr))', gap: 8 }}>
            {cartes.map((carte) => (
              <a key={carte.nom} href={reliefCarteUrl(take.id, carte.nom)} target="_blank" rel="noreferrer" title={c.openMap(carte.nom)} style={{ display: 'grid', gap: 3, fontSize: 11 }}>
                <img src={reliefCarteUrl(take.id, carte.nom)} alt={c.mapAlt(carte.nom)} loading="lazy" style={{ width: '100%', aspectRatio: '1', objectFit: 'cover', borderRadius: 8 }} />
                <span className="dim">{carte.nom}</span>
              </a>
            ))}
          </div>
        </div>
      )}

      <div className="rail-section">
        <div className="label">{c.turntable}</div>
        <a className="btn sm" href={reliefGifUrl(take.id, true)} download><Icon name="download" size={14} />{c.animatedGif}</a>
      </div>

      <div className="rail-section" aria-live="polite">
        <div className="label">{c.qualityCheck}</div>
        {juge ? (
          <>
            <div style={{ fontSize: 15, fontWeight: 600 }}>{juge.note}/10 <span className="dim" style={{ fontWeight: 400, fontSize: 12 }}>· {juge.note >= 8 ? c.readyToUse : juge.note >= 6 ? c.usable : c.redo}</span></div>
            {juge.raison && <div className="dim" style={{ fontSize: 12 }}>{juge.raison}</div>}
            {juge.defauts.length > 0 && <div className="dim" style={{ fontSize: 12 }}>{juge.defauts.join(' · ')}</div>}
            {juge.note < 6 && <button type="button" className="btn sm" onClick={() => void recreate(take)}><Icon name="redo" size={14} />{c.retryWithNewSeed}</button>}
          </>
        ) : (
          <button type="button" className="btn sm" disabled={jugement} onClick={() => void juger()}><Icon name="sparkle" size={14} />{jugement ? c.judgeLoading : c.judgeFourSides}</button>
        )}
      </div>
    </div>
  );
}
