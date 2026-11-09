/**
 * Nexora Mesh (ex-Relief, ex-Object ; `/mesh` est l'adresse, `/relief` et `/object` restent des alias) : any still
 * becomes a textured 3D model (TRELLIS.2 on the local
 * engine). The rail takes the still and the settings; the canvas shows the
 * selected model on a turntable you can grab, next to every other take.
 * Each result is an ordinary take whose file is a GLB, so the Library, the
 * Viewer and the Stage all read it from /api/media/<take>.
 */
import { Suspense, lazy, useEffect, useRef, useState } from 'react';
import { api, downloadUrl, mediaUrl, posterUrl, subjectUrl, uploadFile, type ObjetTexteEtat, type Take } from '../api';
import { FONDS_PLAN_CLE, planCleDepuisCanevas, type FondPlanCle } from '../planCle3d';
import { navigate, setParams, useRoute } from '../router';
import { SourceSlot, loadFile, useTakeParam, type Source } from '../SourcePick';
import { definirMessageEchecPriseMesh, inFeed, isModel, settingsOf, toast, useStore } from '../store';
import { Icon, MediaCard, Spill, Stepper, Switch, fmtSeconds, presetClip, useEstimate } from '../ui';
import Viewer, { recreate, remove } from '../Viewer';
import { usePageDrop } from '../drop';
import type { ModelLook } from '../ModelView';
import { PRODUIT_3D } from '../produit3d.js';
import ReliefOutils from './ReliefOutils';
import type { LangueClient } from '../../shared/creationLanguage';
import { meshCopy, meshNumber } from '../meshCopy';
import { MeshLanguageSwitch } from './MeshLanguageSwitch';

const ModelView = lazy(() => import('../ModelView'));

export default function ObjectPage({
  langue,
  onLangueChange,
}: {
  langue: LangueClient;
  onLangueChange: (langue: LangueClient) => void;
}) {
  const { params } = useRoute();
  const c = meshCopy(langue);
  useEffect(() => definirMessageEchecPriseMesh(() => c.cardFailedHelp), [c]);
  const [source, setSource] = useState<Source | null>(null);
  const [quality, setQuality] = useState<'draft' | 'quality'>('draft');
  const [cutout, setCutout] = useState(true);
  // Background removal you can see before the 3D run: a cutout take of the still.
  const [cut, setCut] = useState<{ takeId: number; forSource: string } | null>(null);
  const [showCut, setShowCut] = useState(true);
  const [cutting, setCutting] = useState(false);
  const sourceKey = source ? String(source.takeId ?? source.token) : '';
  const cutTake = useStore((st) => (cut ? st.takes.find((t) => t.id === cut.takeId) : undefined));
  const cutReady = !!cut && cut.forSource === sourceKey && cutTake?.status === 'done';
  const usingCut = cutReady && showCut;
  useEffect(() => { setShowCut(true); }, [cut?.takeId]);
  const [count, setCount] = useState(1);
  const [busy, setBusy] = useState<string | null>(null);
  const [selected, setSelected] = useState<number | null>(null);
  const [look, setLook] = useState<ModelLook>('lit');
  const [viewing, setViewing] = useState<number | null>(null);
  // Texte → 3D : une image de référence propre, puis le modèle, puis le contrôle du juge sur quatre côtés.
  const [mode, setMode] = useState<'image' | 'vues' | 'texte'>('image');
  // Plusieurs vues du même objet (Pixal3D) : la vue de face est la source principale ci-dessous.
  const [vueGauche, setVueGauche] = useState<Source | null>(null);
  const [vueDos, setVueDos] = useState<Source | null>(null);
  const [vueDroite, setVueDroite] = useState<Source | null>(null);
  const [vuesMax, setVuesMax] = useState(2);
  const [etatLimiteVues, setEtatLimiteVues] = useState<'loading' | 'ready' | 'unavailable' | 'unsupported'>('unavailable');
  const [intention, setIntention] = useState('');
  const [chaine, setChaine] = useState<ObjetTexteEtat | null>(null);
  const [devisT, setDevisT] = useState<{ key: string; value: { secondesEstimees: number; credits: number | null } } | null>(null);
  const devisKey = `${mode}:${mode === 'vues' ? 'draft' : quality}`;
  const devisActuel = devisT?.key === devisKey ? devisT.value : null;
  const [chaineId, setChaineId] = useState<number | null>(null);
  useEffect(() => {
    let mort = false;
    api.objetDevis({ qualite: mode === 'vues' ? 'draft' : quality, source: mode }).then((d) => { if (!mort) setDevisT({ key: devisKey, value: d }); }).catch(() => {});
    return () => { mort = true; };
  }, [devisKey]);
  useEffect(() => {
    if (mode !== 'vues') return;
    let mort = false;
    // The server clamps this setting to 2..4. Until it answers, keep the
    // minimum contract so that a stale UI cannot submit more views than safe.
    setVuesMax(2);
    setEtatLimiteVues('loading');
    void api.nexoraEtat().then((etat) => {
      if (mort) return;
      if (etat.objet3d?.multivue !== true) {
        setEtatLimiteVues('unsupported');
        return;
      }
      const max = etat.objet3d?.vuesMax;
      if (typeof max === 'number' && Number.isFinite(max)) {
        setVuesMax(Math.max(2, Math.min(4, Math.floor(max))));
        setEtatLimiteVues('ready');
      } else {
        setEtatLimiteVues('unavailable');
      }
    }).catch(() => { if (!mort) setEtatLimiteVues('unavailable'); });
    return () => { mort = true; };
  }, [mode]);
  useEffect(() => {
    if (chaineId === null) return;
    let mort = false;
    let minuterie: ReturnType<typeof setTimeout> | undefined;
    const tour = async () => {
      if (mort) return;
      try {
        const e = await api.objetTexteEtat(chaineId);
        if (mort) return;
        if (e.etat === 'fini' && !e.objet) {
          setChaine({ ...e, etat: 'echec' });
          setChaineId(null);
          toast(c.requestFailure, true);
          return;
        }
        setChaine(e);
        if (e.etat === 'fini') {
          if (e.objet) setSelected(e.objet);
          setChaineId(null);
          return;
        }
        if (e.etat === 'echec') { setChaineId(null); toast(c.requestFailure, true); return; }
      } catch { /* réessaie au prochain tour */ }
      if (!mort) minuterie = setTimeout(() => void tour(), 2500);
    };
    void tour();
    return () => { mort = true; clearTimeout(minuterie); };
  }, [chaineId, c]);

  async function creerDepuisTexte() {
    setBusy(c.inProgress);
    try {
      const r = await api.objetTexte({ intention, qualite: quality });
      setChaine(null);
      setChaineId(r.id);
    } catch (e) {
      toast(c.requestFailure, true);
    } finally {
      setBusy(null);
    }
  }
  const enCours = chaine !== null && chaine.etat !== 'fini' && chaine.etat !== 'echec' || (chaineId !== null && chaine === null);

  // Deep link from the Viewer's Make 3D: /mesh?take=44 (and the /object, /relief aliases) preloads that still.
  useTakeParam(params.get('take'), (s) => { setSource(s); setParams({ take: null }); }, c.takeFailure);
  usePageDrop(c.addStill, (files) => {
    void (async () => { const s = await loadFile(files[0], ['image'], langue); if (s) setSource(s); })();
  });

  const takes = useStore((s) => s.takes.filter((t) => inFeed(t) && isModel(t)));
  const est = useEstimate({ kind: 'object', quality });
  const optionalViewsSelected = [vueGauche, vueDos, vueDroite].filter(Boolean).length;
  const exceedsViewLimit = optionalViewsSelected + 1 > vuesMax;
  const showEmptyOptionalSlots = optionalViewsSelected < vuesMax - 1;
  const viewCount = 1 + optionalViewsSelected;
  const takeMultiplier = mode === 'image' ? count : 1;
  const displayedSeconds = mode === 'image' && est ? est * count : devisActuel ? devisActuel.secondesEstimees * takeMultiplier : null;
  const shown = takes.find((t) => t.id === selected) ?? takes.find((t) => t.status === 'done');
  useEffect(() => { setLook('lit'); }, [shown?.id]);

  async function removeBackground() {
    if (!source) return;
    setCutting(true);
    try {
      const r = await api.generate({
        kind: 'cutout', app: 'cutout', mode: 'matte', background: 'transparent',
        ...(source.takeId ? { sourceTake: source.takeId } : { image: source.token }),
        userPrompt: 'Remove background', shotName: `${(source.name || 'still').slice(0, 30)}_cutout`,
      });
      setCut({ takeId: r.takeIds[0], forSource: sourceKey });
    } catch (e) {
      toast(c.backgroundFailure, true);
    } finally {
      setCutting(false);
    }
  }

  async function go() {
    if (!source) return;
    setBusy(c.inProgress);
    try {
      const r = await api.generate({
        kind: 'object', app: 'object', quality, count,
        // With the cutout showing, mesh exactly that PNG; its alpha is the subject.
        ...(usingCut ? { sourceTake: cut!.takeId, removeBackground: false }
          : { removeBackground: cutout, ...(source.takeId ? { sourceTake: source.takeId } : { image: source.token }) }),
        shotName: `object_${(source.prompt || source.name || 'still').slice(0, 30)}`,
        userPrompt: source.prompt ? `3D: ${source.prompt}` : `3D from ${source.name}`,
      });
      setSelected(r.takeIds[0]);
      toast(`${PRODUIT_3D} : ${c.buildingModels(r.takeIds.length)}`);
    } catch (e) {
      toast(c.requestFailure, true);
    } finally {
      setBusy(null);
    }
  }

  /** Plusieurs vues du même objet : Pixal3D, brouillon, une prise (sur les GPU Turing qui portent ce modèle). */
  async function goVues() {
    if (!source || (!vueGauche && !vueDos && !vueDroite) || exceedsViewLimit || etatLimiteVues === 'unsupported') return;
    setBusy(c.inProgress);
    try {
      const versSpec = (s: Source | null) => (s ? (s.takeId ? { sourceTake: s.takeId } : { image: s.token }) : undefined);
      const r = await api.generate({
        kind: 'object', app: 'object', quality: 'draft', count: 1, removeBackground: cutout,
        ...(source.takeId ? { sourceTake: source.takeId } : { image: source.token }),
        vues: { left: versSpec(vueGauche), back: versSpec(vueDos), right: versSpec(vueDroite) },
        shotName: `${PRODUIT_3D.toLowerCase()}_vues_${(source.name || 'vue').slice(0, 24)}`, userPrompt: `3D à partir de plusieurs vues de ${source.name || 'l’objet'}`,
      });
      setSelected(r.takeIds[0]);
      toast(`${PRODUIT_3D} : ${c.modelFromViews(1 + [vueGauche, vueDos, vueDroite].filter(Boolean).length)}`);
    } catch (e) {
      toast(c.requestFailure, true);
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="rail-layout" lang={langue === 'fr' ? 'fr-CA' : 'en-CA'} style={{ gridTemplateColumns: '372px 1fr' }}>
      <aside className="rail">
        <Spill src={presetClip('turntable')} video />
        <div className="display" style={{ fontSize: 26 }}>{PRODUIT_3D}</div>
        <MeshLanguageSwitch langue={langue} onChange={onLangueChange} />
        <div className="dim" style={{ fontSize: 12.5, marginTop: -4 }}>{c.intro}</div>

        <div className="seg" role="group" aria-label={c.startingPoint}>
          <button type="button" className={mode === 'image' ? 'on' : ''} onClick={() => setMode('image')}>{c.imageTo3d}</button>
          <button type="button" className={mode === 'vues' ? 'on' : ''} onClick={() => setMode('vues')}>{c.multiView}</button>
          <button type="button" className={mode === 'texte' ? 'on' : ''} onClick={() => setMode('texte')}>{c.textTo3d}</button>
        </div>

        {mode === 'texte' ? (
          <div className="rail-section">
            <div className="label">{c.object}</div>
            <div className="st-champ">
              <textarea value={intention} onChange={(e) => setIntention(e.target.value)} maxLength={1000} style={{ minHeight: 90 }}
                placeholder={c.objectDescription} aria-label={c.object} />
            </div>
            <div className="dim" style={{ fontSize: 12 }}>{c.text3dIntro}</div>
          </div>
        ) : (
          <>
            <SourceSlot label={mode === 'vues' ? c.frontView : c.image} value={source} onChange={setSource} accept={['image']} langue={langue}
              title={mode === 'vues' ? c.addFrontView : c.addStill} sub={c.frontViewHint} />
            {mode === 'vues' && (
              <>
                {(vueGauche || showEmptyOptionalSlots) && <SourceSlot label={c.leftView} value={vueGauche} onChange={setVueGauche} accept={['image']} langue={langue} title={`${c.addLeftView}${c.optional}`} sub={c.sameObjectLeft} />}
                {(vueDos || showEmptyOptionalSlots) && <SourceSlot label={c.backView} value={vueDos} onChange={setVueDos} accept={['image']} langue={langue} title={`${c.addBackView}${c.optional}`} sub={c.sameObjectBack} />}
                {(vueDroite || showEmptyOptionalSlots) && <SourceSlot label={c.rightView} value={vueDroite} onChange={setVueDroite} accept={['image']} langue={langue} title={`${c.addRightView}${c.optional}`} sub={c.sameObjectRight} />}
                <div className="dim" style={{ fontSize: 12 }}>{c.multiViewInfo(vuesMax)}</div>
                {etatLimiteVues === 'loading' && <div className="dim" role="status">{c.viewLimitLoading}</div>}
                {etatLimiteVues === 'unavailable' && <div className="dim" role="status">{c.viewLimitUnavailable(vuesMax)}</div>}
                {etatLimiteVues === 'unsupported' && <div className="dim" role="alert">{c.multiViewUnavailable}</div>}
                {exceedsViewLimit && <div className="dim" role="alert" style={{ color: 'var(--danger, #e5534b)' }}>{c.viewLimitExceeded(vuesMax)}</div>}
              </>
            )}
          </>
        )}

        {mode !== 'vues' && <div className="rail-section">
            <div className="label">{c.detail}</div>
          <div className="seg">
            {(['draft', 'quality'] as const).map((level) => <button key={level} type="button" className={quality === level ? 'on' : ''} onClick={() => setQuality(level)}>{level === 'draft' ? c.draft : c.high}</button>)}
          </div>
          <div className="dim" style={{ fontSize: 12 }}>{quality === 'draft' ? c.draftInfo : c.highInfo}</div>
        </div>}

        {mode === 'image' && source && (
          <div className="rail-section">
            {cutReady && (
              <>
                <div className="seg">
                  <button type="button" className={!showCut ? 'on' : ''} onClick={() => setShowCut(false)}>{c.original}</button>
                  <button type="button" className={showCut ? 'on' : ''} onClick={() => setShowCut(true)}>{c.cutout}</button>
                </div>
                {showCut && (
                  <div className="checker" style={{ borderRadius: 12, overflow: 'hidden', aspectRatio: '4 / 3', display: 'grid', placeItems: 'center' }}>
                    <img src={mediaUrl(cut!.takeId)} alt={c.cutoutAlt} style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain', display: 'block' }} />
                  </div>
                )}
              </>
            )}
            <button type="button" className="btn sm" disabled={cutting || (!!cut && cut.forSource === sourceKey && !cutReady && cutTake?.status !== 'failed')} onClick={() => void removeBackground()}>
              <Icon name="sparkle" size={13} />
              {cutting || (cut && cut.forSource === sourceKey && !cutReady && cutTake?.status !== 'failed') ? c.removingBackground : cutReady ? c.removeBackgroundAgain : c.removeBackground}
            </button>
            {cutReady && <div className="dim" style={{ fontSize: 12 }}>{showCut ? c.useThisCutout : c.useOriginal}</div>}
          </div>
        )}

        {mode === 'image' && !usingCut && <div className="rail-section">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10 }}>
            <span className="dim" style={{ fontSize: 12.5 }}>{c.cutFirst}</span>
            <Switch on={cutout} onChange={setCutout} label={c.cutFirst} />
          </div>
          <div className="label" style={{ textTransform: 'none', letterSpacing: 0 }}>
            {cutout ? c.cutoutBehavior : c.transparencyBehavior}
          </div>
        </div>}

        {mode === 'image' && <div className="chip-row" style={{ alignItems: 'center' }}>
          <Stepper value={count} min={1} max={4} onChange={setCount} fmt={(v) => `${v}/4`} labels={{ decrease: c.decreaseCount, increase: c.increaseCount }} />
          <span className="dim" style={{ fontSize: 12 }}>{c.eachTakeNewSeed}</span>
        </div>}

        {mode === 'texte' ? (
          <>
            {chaine && <EtapesTexte e={chaine} langue={langue} />}
            <button type="button" className="generate" style={{ marginTop: 'auto' }} disabled={!!busy || enCours || intention.trim().length < 3} onClick={() => void creerDepuisTexte()}>
              <span>{busy ?? (enCours ? c.inProgress : c.create3d)}</span>
              <span className="cost">{devisActuel ? `${devisActuel.credits !== null ? `${devisActuel.credits} ${c.credits} · ` : ''}≈ ${fmtSeconds(devisActuel.secondesEstimees)}` : c.estimateUnavailable}</span>
            </button>
          </>
        ) : (
          <button type="button" className="generate" style={{ marginTop: 'auto' }} disabled={!!busy || !source || (mode === 'vues' && ((!vueGauche && !vueDos && !vueDroite) || exceedsViewLimit || etatLimiteVues === 'unsupported'))} onClick={() => void (mode === 'vues' ? goVues() : go())}>
            <span>{busy ?? (mode === 'vues' ? c.modelFromViews(viewCount) : count > 1 ? `${PRODUIT_3D} · ${count}` : PRODUIT_3D)}</span>
            <span className="cost">{devisActuel?.credits != null ? `${devisActuel.credits * takeMultiplier} ${c.credits} · ` : ''}{displayedSeconds !== null ? `${mode === 'image' && est ? '' : '≈ '}${fmtSeconds(displayedSeconds)}` : c.estimateUnavailable}</span>
          </button>
        )}
      </aside>

      <section className="canvas">
        <div className="canvas-head">
          <div className="tabs" style={{ borderBottom: 0 }}>
            <button type="button" className="on">{c.models}</button>
          </div>
        </div>
        <div className="canvas-body">
          {takes.length === 0 ? (
            <div className="hero-empty">
              <div className="object-hero"><video src={presetClip('turntable')} muted loop autoPlay playsInline /></div>
              <div className="display" style={{ fontSize: 'clamp(34px,4.6vw,60px)' }}>{PRODUIT_3D} : <span className="hl">{c.emptyTitle}</span></div>
              <div className="steps3">
                <div><span className="label">01</span><b>{c.addStill}</b><span className="dim">{c.addStillHelp}</span></div>
                <div><span className="label">02</span><b>{c.chooseDetail}</b><span className="dim">{c.chooseDetailHelp}</span></div>
                <div><span className="label">03</span><b>{c.turnModel}</b><span className="dim">{c.turnModelHelp}</span></div>
              </div>
            </div>
          ) : (
            <>
              {shown && shown.status === 'done' && <ObjectFocus take={shown} look={look} onLook={setLook} onOpen={() => setViewing(shown.id)} langue={langue} />}
              <div className="grid dense" style={{ marginTop: 18 }}>
                {takes.map((t) => (
                  <MediaCard key={t.id} take={t} langue={langue} onOpen={() => setSelected(t.id)} actions={<>
                    {t.status === 'done' && <a className="icon-btn" title={c.downloadGlb} href={downloadUrl(t.id)}><Icon name="download" size={14} /></a>}
                    <button type="button" className="icon-btn" title={c.recreate} onClick={() => void recreate(t, { langue })}><Icon name="redo" size={14} /></button>
                    <button type="button" className="icon-btn" title={c.delete} onClick={() => void remove(t)}><Icon name="trash" size={14} /></button>
                  </>} />
                ))}
              </div>
            </>
          )}
        </div>
      </section>
      {viewing !== null && <Viewer takeId={viewing} onClose={() => setViewing(null)} onStep={() => {}} langue={langue} />}
    </div>
  );
}

/** The selected model, big: grab to orbit, switch looks, see what it was made from. */
function ObjectFocus({ take, look, onLook, onOpen, langue }: { take: Take; look: ModelLook; onLook: (l: ModelLook) => void; onOpen: () => void; langue: LangueClient }) {
  const c = meshCopy(langue);
  const s = settingsOf(take);
  const vue = useRef<HTMLDivElement>(null);
  const [fond, setFond] = useState<FondPlanCle>('studio');
  const [envoi, setEnvoi] = useState(false);
  async function animer() {
    const canevas = vue.current?.querySelector('canvas');
    if (!canevas) { toast(c.viewNotReady, true); return; }
    setEnvoi(true);
    try {
      const png = await planCleDepuisCanevas(canevas, fond);
      const jeton = await uploadFile(new File([png], `plan-cle-relief-${take.id}.png`, { type: 'image/png' }));
      // Aperçu en data URL : il survit à un rechargement de page, contrairement à une URL de blob.
      const apercu = await new Promise<string>((ok) => { const r = new FileReader(); r.onload = () => ok(String(r.result)); r.onerror = () => ok(''); r.readAsDataURL(png); });
      try { sessionStorage.setItem('nexora-plan-cle-apercu', apercu); } catch { /* aperçu facultatif */ }
      navigate(`/?mode=video&jeton=${encodeURIComponent(jeton)}&intention=${encodeURIComponent('L’objet de l’image, exactement le même, tourne lentement sur lui-même pendant que la caméra fait un arc autour de lui ; éclairage studio haut de gamme, reflets qui glissent sur ses matières.')}`);
    } catch (e) {
      toast(c.animationFailure, true);
    } finally {
      setEnvoi(false);
    }
  }
  return (
    <>
    <div className="object-focus" ref={vue}>
      <Suspense fallback={<div className="model-view"><img className="model-poster" src={posterUrl(take.id)} alt="" /></div>}>
        <ModelView src={mediaUrl(take.id)} poster={posterUrl(take.id)} look={look} langue={langue} />
      </Suspense>
      <div className="object-side">
        <div className="label">{c.from}</div>
        <img className="object-from" src={subjectUrl(take.id)} alt="" onError={(e) => { e.currentTarget.style.display = 'none'; }} />
        <div className="seg">
          {(['lit', 'clay', 'wire'] as const).map((l) => (
            <button key={l} type="button" className={look === l ? 'on' : ''} onClick={() => onLook(l)}>{l === 'lit' ? c.textured : l === 'clay' ? c.clay : c.wire}</button>
          ))}
        </div>
        <div className="dim" style={{ fontSize: 12 }}>
          {c.facesAndTextures(s.quality === 'quality' ? c.high : c.draft, meshNumber(Number(s.faces), langue), String(s.texture))}
          {take.render_seconds ? ` · ${Math.round(take.render_seconds)}${langue === 'fr' ? ' s' : ' sec'}` : ''}
        </div>
        <a className="btn sm accent" href={downloadUrl(take.id)}><Icon name="download" size={14} />{c.downloadGlb}</a>
        <button type="button" className="btn sm" onClick={onOpen}><Icon name="sparkle" size={14} />{c.open}</button>
        {take.status === 'done' && (
          <div className="relief-animer" title={c.animateInVideo}>
            <div className="label">{c.animateInVideo}</div>
            <div className="seg">
              {(Object.keys(FONDS_PLAN_CLE) as FondPlanCle[]).map((f) => <button key={f} type="button" className={fond === f ? 'on' : ''} onClick={() => setFond(f)}>{f === 'studio' ? c.darkStudio : f === 'clair' ? c.lightStudio : c.blueNight}</button>)}
            </div>
            <button type="button" className="btn sm accent" disabled={envoi} onClick={() => void animer()}><Icon name="sparkle" size={14} />{envoi ? c.capture : c.animateWithH3}</button>
          </div>
        )}
      </div>
    </div>
    <ReliefOutils take={take} langue={langue} />
    </>
  );
}

/** Les trois temps du texte → 3D, avec la note du juge quand elle est tombée. */
export function EtapesTexte({ e, langue }: { e: ObjetTexteEtat; langue: LangueClient }) {
  const c = meshCopy(langue);
  const ordre = ['image', 'objet', 'jugement', 'fini'] as const;
  const rang = e.etat === 'echec' ? -1 : ordre.indexOf(e.etat);
  const lignes = [[c.textReferenceImage, 0], [c.textModel, 1], [c.textCheck, 2]] as const;
  const derniere = e.notes[e.notes.length - 1];
  return (
    <div className="rail-section" aria-live="polite">
      {lignes.map(([nom, i]) => (
        <div key={nom} style={{ display: 'flex', gap: 8, fontSize: 12.5, opacity: rang >= i || e.etat === 'fini' ? 1 : 0.5 }}>
          <span aria-hidden="true">{e.etat === 'fini' || rang > i ? '✓' : rang === i ? '…' : '·'}</span>
          <span>{nom}{i === 1 && e.essai > 1 ? c.secondAttempt : ''}</span>
        </div>
      ))}
      {derniere && <div className="dim" style={{ fontSize: 12 }}>{c.judge} : {derniere.note}/10{derniere.raison ? ` · ${derniere.raison}` : ''}</div>}
      {e.avertissement === 'relance-echouee' && <div role="status" style={{ fontSize: 12.5 }}>{c.retryFailedKept}</div>}
      {e.etat === 'echec' && <div role="alert" style={{ fontSize: 12.5, color: 'var(--danger, #e5534b)' }}>{c.failed}</div>}
    </div>
  );
}
