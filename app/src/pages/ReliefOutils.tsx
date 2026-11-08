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
type CopieMesh = ReturnType<typeof meshCopy>;

function aideFormat(format: FormatRelief, c: CopieMesh): string {
  const aides = {
    glb: c.helpGlb,
    obj: c.helpObj,
    stl: c.helpStl,
    '3mf': c.help3mf,
    usdz: c.helpUsdz,
  } satisfies Record<FormatRelief, string>;
  return aides[format];
}

function resumeTopologie(r: RapportMaillage, orientationIncoherente: boolean, langue: LangueClient, c: CopieMesh): string {
  if (r.etanche) {
    if (orientationIncoherente) return c.summaryInconsistent;
    return c.summaryClosed;
  }
  if (r.aretesOuvertes > 0) return c.summaryOpen(meshNumber(r.aretesOuvertes, langue));
  return c.summaryNotWatertight;
}

function libelleJuge(note: number, c: CopieMesh): string {
  if (note >= 8) return c.readyToUse;
  if (note >= 6) return c.usable;
  return c.redo;
}

function nomFaces(v: number, langue: LangueClient): string {
  if (v === 0) return langue === 'fr' ? 'Plein' : 'Full model';
  return `${meshNumber(v / 1000, langue)} k`;
}

export function ResumeMaillage({ r, langue = 'fr' }: { r: RapportMaillage; langue?: LangueClient }) {
  const c = meshCopy(langue);
  const orientationIncoherente = r.avertissements.includes('Volume non calculé : orientation incohérente des faces.');
  const summary = resumeTopologie(r, orientationIncoherente, langue, c);
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

export function LienExportMesh({ format, url, takeId, compatibilite, rapportRecu, rapportEchoue, langue }: {
  format: FormatRelief; url: string; takeId: number; compatibilite: RapportRelief['compatibiliteObj']; rapportRecu: boolean; rapportEchoue: boolean; langue: LangueClient;
}) {
  const c = meshCopy(langue);
  if (rapportEchoue) return <span className="btn sm accent" aria-disabled="true">{c.exportUnavailable}</span>;
  if (format === 'obj' && !compatibilite && !rapportRecu) return <span role="status">{c.objChecking}</span>;
  if (format === 'obj' && (!compatibilite || !compatibilite.compatible)) return <div role="alert">{compatibilite ? c.objUnsupported : c.objUnknown} <a href={reliefExportUrl(takeId, 'glb')} download>{c.downloadOriginalGlb}</a></div>;
  if (format === 'usdz') return <TelechargementUsdz url={url} takeId={takeId} langue={langue} />;
  return <a className="btn sm accent" href={url} download><Icon name="download" size={14} />{c.export} {NOMS_FORMAT[format]}</a>;
}

/** Un HEAD prépare le cache et permet de montrer un refus avant le téléchargement natif. */
export function TelechargementUsdz({ url, takeId, langue }: { url: string; takeId: number; langue: LangueClient }) {
  const c = meshCopy(langue);
  const [etat, setEtat] = useState<'pret' | 'chargement' | 'incompatible' | 'erreur'>('pret');
  const controle = useRef<AbortController | null>(null);
  useEffect(() => { setEtat('pret'); return () => { controle.current?.abort(); }; }, [url]);
  async function lancer(e: React.MouseEvent<HTMLAnchorElement>) {
    e.preventDefault();
    if (etat === 'chargement') return;
    setEtat('chargement');
    const requete = new AbortController();
    controle.current = requete;
    try {
      const reponse = await fetch(url, { method: 'HEAD', signal: requete.signal });
      if (requete.signal.aborted) return;
      if (reponse.status === 400) { setEtat('incompatible'); return; }
      const type = reponse.headers.get('content-type')?.split(';', 1)[0].trim().toLowerCase();
      if (!reponse.ok || type !== 'model/vnd.usdz+zip') { setEtat('erreur'); return; }
      setEtat('pret');
      const lien = document.createElement('a');
      lien.href = url; lien.download = '';
      document.body.appendChild(lien); lien.click(); lien.remove();
    } catch { if (!requete.signal.aborted) setEtat('erreur'); }
  }
  return <>
    <a className="btn sm accent" href={url} download onClick={lancer} aria-disabled={etat === 'chargement'}><Icon name="download" size={14} />{c.export} USDZ</a>
    {etat === 'chargement' && <span role="status">{c.usdzChecking}</span>}
    {etat === 'incompatible' && <div role="alert">{c.usdzUnsupported} <a href={reliefExportUrl(takeId, 'glb')} download>{c.downloadOriginalGlb}</a></div>}
    {etat === 'erreur' && <div role="alert">{c.usdzFailure}</div>}
  </>;
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
        <div className="dim" style={{ fontSize: 12 }}>{aideFormat(format, c)}</div>
        <div className="label" style={{ textTransform: 'none', letterSpacing: 0 }}>{c.numberOfFaces}</div>
        <div className="seg" role="group" aria-label={c.numberOfFaces}>
          {FACES.map((v) => <button key={v} type="button" className={faces === v ? 'on' : ''} onClick={() => setFaces(v)}>{nomFaces(v, langue)}</button>)}
        </div>
        <EtatAnalyseMaillage rapport={affiche ?? null} loading={!info && !erreurRapport} failed={erreurRapport} langue={langue} />
        <LienExportMesh format={format} url={urlExport} takeId={take.id} compatibilite={info?.compatibiliteObj} rapportRecu={info !== null} rapportEchoue={erreurRapport} langue={langue} />
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
            <div style={{ fontSize: 15, fontWeight: 600 }}>{juge.note}/10 <span className="dim" style={{ fontWeight: 400, fontSize: 12 }}>· {libelleJuge(juge.note, c)}</span></div>
            {juge.raison && <div className="dim" style={{ fontSize: 12 }}>{juge.raison}</div>}
            {juge.defauts.length > 0 && <div className="dim" style={{ fontSize: 12 }}>{juge.defauts.join(' · ')}</div>}
            {juge.note < 6 && <button type="button" className="btn sm" onClick={() => void recreate(take, { langue })}><Icon name="redo" size={14} />{c.retryWithNewSeed}</button>}
          </>
        ) : (
          <button type="button" className="btn sm" disabled={jugement} onClick={() => void juger()}><Icon name="sparkle" size={14} />{jugement ? c.judgeLoading : c.judgeFourSides}</button>
        )}
      </div>
    </div>
  );
}
