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
import { OBJECT_DETAIL } from '../catalog';
import { navigate, setParams, useRoute } from '../router';
import { SourceSlot, loadFile, useTakeParam, type Source } from '../SourcePick';
import { inFeed, isModel, settingsOf, toast, useStore } from '../store';
import { Icon, MediaCard, Spill, Stepper, Switch, fmtSeconds, presetClip, useEstimate } from '../ui';
import Viewer, { recreate, remove } from '../Viewer';
import { usePageDrop } from '../drop';
import type { ModelLook } from '../ModelView';
import { PRODUIT_3D } from '../produit3d.js';
import ReliefOutils from './ReliefOutils';

const ModelView = lazy(() => import('../ModelView'));

export default function ObjectPage() {
  const { params } = useRoute();
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
  const [intention, setIntention] = useState('');
  const [chaine, setChaine] = useState<ObjetTexteEtat | null>(null);
  const [devisT, setDevisT] = useState<{ secondesEstimees: number; credits: number | null } | null>(null);
  const [chaineId, setChaineId] = useState<number | null>(null);
  useEffect(() => {
    let mort = false;
    api.objetDevis({ qualite: mode === 'vues' ? 'draft' : quality, source: mode }).then((d) => { if (!mort) setDevisT(d); }).catch(() => {});
    return () => { mort = true; };
  }, [quality, mode]);
  useEffect(() => {
    if (chaineId === null) return;
    let mort = false;
    const tour = async () => {
      try {
        const e = await api.objetTexteEtat(chaineId);
        if (mort) return;
        setChaine(e);
        if (e.etat === 'fini' && e.objet) { setSelected(e.objet); return; }
        if (e.etat === 'echec') { toast(e.erreur ?? 'La création 3D a échoué', true); return; }
      } catch { /* réessaie au prochain tour */ }
      if (!mort) setTimeout(() => void tour(), 2500);
    };
    void tour();
    return () => { mort = true; };
  }, [chaineId]);

  async function creerDepuisTexte() {
    setBusy('Lancement...');
    try {
      const r = await api.objetTexte({ intention, qualite: quality });
      setChaine(null);
      setChaineId(r.id);
    } catch (e) {
      toast(e instanceof Error ? e.message : 'échec', true);
    } finally {
      setBusy(null);
    }
  }
  const enCours = chaine !== null && chaine.etat !== 'fini' && chaine.etat !== 'echec' || (chaineId !== null && chaine === null);

  // Deep link from the Viewer's Make 3D: /mesh?take=44 (and the /object, /relief aliases) preloads that still.
  useTakeParam(params.get('take'), (s) => { setSource(s); setParams({ take: null }); });
  usePageDrop('Drop a still to make it 3D', (files) => {
    void (async () => { const s = await loadFile(files[0], ['image']); if (s) setSource(s); })();
  });

  const takes = useStore((s) => s.takes.filter((t) => inFeed(t) && isModel(t)));
  const est = useEstimate({ kind: 'object', quality });
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
      toast(e instanceof Error ? e.message : 'failed', true);
    } finally {
      setCutting(false);
    }
  }

  async function go() {
    if (!source) return;
    setBusy('Queuing...');
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
      toast(`${PRODUIT_3D} : ${r.takeIds.length} modèle${r.takeIds.length > 1 ? 's' : ''} en construction`);
    } catch (e) {
      toast(e instanceof Error ? e.message : 'failed', true);
    } finally {
      setBusy(null);
    }
  }

  /** Plusieurs vues du même objet : Pixal3D, brouillon, une prise (sur les GPU Turing qui portent ce modèle). */
  async function goVues() {
    if (!source) return;
    setBusy('Mise en file...');
    try {
      const versSpec = (s: Source | null) => (s ? (s.takeId ? { sourceTake: s.takeId } : { image: s.token }) : undefined);
      const r = await api.generate({
        kind: 'object', app: 'object', quality: 'draft', count: 1, removeBackground: cutout,
        ...(source.takeId ? { sourceTake: source.takeId } : { image: source.token }),
        vues: { left: versSpec(vueGauche), back: versSpec(vueDos), right: versSpec(vueDroite) },
        shotName: `${PRODUIT_3D.toLowerCase()}_vues_${(source.name || 'vue').slice(0, 24)}`, userPrompt: `3D à partir de plusieurs vues de ${source.name || 'l’objet'}`,
      });
      setSelected(r.takeIds[0]);
      toast(`${PRODUIT_3D} : modèle en construction à partir de plusieurs vues`);
    } catch (e) {
      toast(e instanceof Error ? e.message : 'échec', true);
    } finally {
      setBusy(null);
    }
  }

  const q = OBJECT_DETAIL.find((x) => x.id === quality)!;
  return (
    <div className="rail-layout" style={{ gridTemplateColumns: '372px 1fr' }}>
      <aside className="rail">
        <Spill src={presetClip('turntable')} video />
        <div className="display" style={{ fontSize: 26 }}>{PRODUIT_3D}</div>
        <div className="dim" style={{ fontSize: 12.5, marginTop: -4 }}>Une image, plusieurs vues ou une phrase deviennent un modèle 3D texturé : à tourner, à exporter (GLB, OBJ, STL, 3MF, USDZ) et à poser dans une scène. Sur nos GPU.</div>

        <div className="seg" role="group" aria-label="Point de départ">
          <button type="button" className={mode === 'image' ? 'on' : ''} onClick={() => setMode('image')}>Image → 3D</button>
          <button type="button" className={mode === 'vues' ? 'on' : ''} onClick={() => setMode('vues')}>Multi-vues</button>
          <button type="button" className={mode === 'texte' ? 'on' : ''} onClick={() => setMode('texte')}>Texte → 3D</button>
        </div>

        {mode === 'texte' ? (
          <div className="rail-section">
            <div className="label">L’objet</div>
            <div className="st-champ">
              <textarea value={intention} onChange={(e) => setIntention(e.target.value)} maxLength={1000} style={{ minHeight: 90 }}
                placeholder="Une chaise en bois clair aux pieds fuselés, un robot jouet en métal rouge…" aria-label="Description de l’objet" />
            </div>
            <div className="dim" style={{ fontSize: 12 }}>Nexora dessine d’abord une photo de produit propre de l’objet seul, puis la reconstruit en 3D, puis vérifie quatre côtés. Une seule relance si le contrôle est sévère.</div>
          </div>
        ) : (
          <>
            <SourceSlot label={mode === 'vues' ? 'Vue de face' : 'Still'} value={source} onChange={setSource} accept={['image']}
              title={mode === 'vues' ? 'Ajoute la vue de face' : 'Add a still of the thing'} sub="One subject, whole in frame, on a plain background works best." />
            {mode === 'vues' && (
              <>
                <SourceSlot label="Vue de gauche" value={vueGauche} onChange={setVueGauche} accept={['image']} title="Gauche (facultatif)" sub="Le même objet, vu de son côté gauche." />
                <SourceSlot label="Vue de dos" value={vueDos} onChange={setVueDos} accept={['image']} title="Dos (facultatif)" sub="Le même objet, vu de derrière." />
                <SourceSlot label="Vue de droite" value={vueDroite} onChange={setVueDroite} accept={['image']} title="Droite (facultatif)" sub="Le même objet, vu de son côté droit." />
                <div className="dim" style={{ fontSize: 12 }}>Pixal3D recoupe les vues pour deviner ce qu’une seule photo cache. Au moins une vue en plus de la face, trois vues au plus pour l’instant (mémoire des GPU Turing) ; brouillon seulement, environ 3 à 4 minutes.</div>
              </>
            )}
          </>
        )}

        {mode !== 'vues' && <div className="rail-section">
          <div className="label">Detail</div>
          <div className="seg">
            {OBJECT_DETAIL.map((x) => <button key={x.id} type="button" className={quality === x.id ? 'on' : ''} onClick={() => setQuality(x.id)}>{x.label}</button>)}
          </div>
          <div className="dim" style={{ fontSize: 12 }}>{q.note}</div>
        </div>}

        {mode === 'image' && source && (
          <div className="rail-section">
            {cutReady && (
              <>
                <div className="seg">
                  <button type="button" className={!showCut ? 'on' : ''} onClick={() => setShowCut(false)}>Original</button>
                  <button type="button" className={showCut ? 'on' : ''} onClick={() => setShowCut(true)}>Cut out</button>
                </div>
                {showCut && (
                  <div className="checker" style={{ borderRadius: 12, overflow: 'hidden', aspectRatio: '4 / 3', display: 'grid', placeItems: 'center' }}>
                    <img src={mediaUrl(cut!.takeId)} alt="The subject with the background removed" style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'contain', display: 'block' }} />
                  </div>
                )}
              </>
            )}
            <button type="button" className="btn sm" disabled={cutting || (!!cut && cut.forSource === sourceKey && !cutReady && cutTake?.status !== 'failed')} onClick={() => void removeBackground()}>
              <Icon name="sparkle" size={13} />
              {cutting || (cut && cut.forSource === sourceKey && !cutReady && cutTake?.status !== 'failed') ? 'Removing the background...' : cutReady ? 'Remove the background again' : 'Remove background'}
            </button>
            {cutReady && <div className="dim" style={{ fontSize: 12 }}>{showCut ? 'Make 3D builds exactly this cutout.' : 'Make 3D uses the original picture.'}</div>}
          </div>
        )}

        {mode === 'image' && !usingCut && <div className="rail-section">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10 }}>
            <span className="dim" style={{ fontSize: 12.5 }}>Cut the subject out first</span>
            <Switch on={cutout} onChange={setCutout} label="cut the subject out first" />
          </div>
          <div className="label" style={{ textTransform: 'none', letterSpacing: 0 }}>
            {cutout ? 'BiRefNet finds the subject and drops the background.' : 'Uses the picture\'s own transparency. Turn this off only for a PNG that is already cut out.'}
          </div>
        </div>}

        {mode !== 'texte' && <div className="chip-row" style={{ alignItems: 'center' }}>
          <Stepper value={count} min={1} max={4} onChange={setCount} fmt={(v) => `${v}/4`} />
          <span className="dim" style={{ fontSize: 12 }}>Each take uses a new seed.</span>
        </div>}

        {mode === 'texte' ? (
          <>
            {chaine && <EtapesTexte e={chaine} />}
            <button type="button" className="generate" style={{ marginTop: 'auto' }} disabled={!!busy || enCours || intention.trim().length < 3} onClick={() => void creerDepuisTexte()}>
              <span>{busy ?? (enCours ? 'En cours…' : 'Créer en 3D')}</span>
              <span className="cost">{devisT ? `${devisT.credits !== null ? `${devisT.credits} crédits · ` : ''}≈ ${fmtSeconds(devisT.secondesEstimees)}` : 'TRELLIS.2'}</span>
            </button>
          </>
        ) : (
          <button type="button" className="generate" style={{ marginTop: 'auto' }} disabled={!!busy || !source || (mode === 'vues' && !vueGauche && !vueDos && !vueDroite)} onClick={() => void (mode === 'vues' ? goVues() : go())}>
            <span>{busy ?? (count > 1 ? `${PRODUIT_3D} · ${count}` : mode === 'vues' ? `${PRODUIT_3D} depuis ${1 + [vueGauche, vueDos, vueDroite].filter(Boolean).length} vues` : PRODUIT_3D)}</span>
            <span className="cost">{devisT?.credits != null ? `${devisT.credits * count} crédits · ` : ''}{est ? fmtSeconds(est * count) : devisT ? `≈ ${fmtSeconds(devisT.secondesEstimees * count)}` : 'TRELLIS.2'}</span>
          </button>
        )}
      </aside>

      <section className="canvas">
        <div className="canvas-head">
          <div className="tabs" style={{ borderBottom: 0 }}>
            <button type="button" className="on">Models</button>
          </div>
        </div>
        <div className="canvas-body">
          {takes.length === 0 ? (
            <div className="hero-empty">
              <div className="object-hero"><video src={presetClip('turntable')} muted loop autoPlay playsInline /></div>
              <div className="display" style={{ fontSize: 'clamp(34px,4.6vw,60px)' }}>{PRODUIT_3D} : <span className="hl">en volume</span></div>
              <div className="steps3">
                <div><span className="label">01</span><b>Add a still</b><span className="dim">Or press Make 3D on any image in the Library.</span></div>
                <div><span className="label">02</span><b>Pick the detail</b><span className="dim">Draft to check the shape, High for the keeper.</span></div>
                <div><span className="label">03</span><b>Turn it</b><span className="dim">Drag to orbit, download the GLB, block it into a scene.</span></div>
              </div>
            </div>
          ) : (
            <>
              {shown && shown.status === 'done' && <ObjectFocus take={shown} look={look} onLook={setLook} onOpen={() => setViewing(shown.id)} />}
              <div className="grid dense" style={{ marginTop: 18 }}>
                {takes.map((t) => (
                  <MediaCard key={t.id} take={t} onOpen={() => setSelected(t.id)} actions={<>
                    {t.status === 'done' && <a className="icon-btn" title="Download GLB" href={downloadUrl(t.id)}><Icon name="download" size={14} /></a>}
                    <button type="button" className="icon-btn" title="Recreate" onClick={() => void recreate(t)}><Icon name="redo" size={14} /></button>
                    <button type="button" className="icon-btn" title="Delete" onClick={() => void remove(t)}><Icon name="trash" size={14} /></button>
                  </>} />
                ))}
              </div>
            </>
          )}
        </div>
      </section>
      {viewing !== null && <Viewer takeId={viewing} onClose={() => setViewing(null)} onStep={() => {}} />}
    </div>
  );
}

/** The selected model, big: grab to orbit, switch looks, see what it was made from. */
function ObjectFocus({ take, look, onLook, onOpen }: { take: Take; look: ModelLook; onLook: (l: ModelLook) => void; onOpen: () => void }) {
  const s = settingsOf(take);
  const vue = useRef<HTMLDivElement>(null);
  const [fond, setFond] = useState<FondPlanCle>('studio');
  const [envoi, setEnvoi] = useState(false);
  async function animer() {
    const canevas = vue.current?.querySelector('canvas');
    if (!canevas) { toast('La vue 3D n’est pas prête.', true); return; }
    setEnvoi(true);
    try {
      const png = await planCleDepuisCanevas(canevas, fond);
      const jeton = await uploadFile(new File([png], `plan-cle-relief-${take.id}.png`, { type: 'image/png' }));
      // Aperçu en data URL : il survit à un rechargement de page, contrairement à une URL de blob.
      const apercu = await new Promise<string>((ok) => { const r = new FileReader(); r.onload = () => ok(String(r.result)); r.onerror = () => ok(''); r.readAsDataURL(png); });
      try { sessionStorage.setItem('nexora-plan-cle-apercu', apercu); } catch { /* aperçu facultatif */ }
      navigate(`/?mode=video&jeton=${encodeURIComponent(jeton)}&intention=${encodeURIComponent('L’objet de l’image, exactement le même, tourne lentement sur lui-même pendant que la caméra fait un arc autour de lui ; éclairage studio haut de gamme, reflets qui glissent sur ses matières.')}`);
    } catch (e) {
      toast(e instanceof Error ? e.message : 'Capture impossible.', true);
    } finally {
      setEnvoi(false);
    }
  }
  return (
    <>
    <div className="object-focus" ref={vue}>
      <Suspense fallback={<div className="model-view"><img className="model-poster" src={posterUrl(take.id)} alt="" /></div>}>
        <ModelView src={mediaUrl(take.id)} poster={posterUrl(take.id)} look={look} />
      </Suspense>
      <div className="object-side">
        <div className="label">From</div>
        <img className="object-from" src={subjectUrl(take.id)} alt="" onError={(e) => { e.currentTarget.style.display = 'none'; }} />
        <div className="seg">
          {(['lit', 'clay', 'wire'] as const).map((l) => (
            <button key={l} type="button" className={look === l ? 'on' : ''} onClick={() => onLook(l)}>{l === 'lit' ? 'Textured' : l === 'clay' ? 'Clay' : 'Wire'}</button>
          ))}
        </div>
        <div className="dim" style={{ fontSize: 12 }}>
          {s.quality === 'quality' ? 'High' : 'Draft'} · up to {Number(s.faces).toLocaleString()} faces · {s.texture}px textures
          {take.render_seconds ? ` · ${Math.round(take.render_seconds)}s` : ''}
        </div>
        <a className="btn sm accent" href={downloadUrl(take.id)}><Icon name="download" size={14} />Download GLB</a>
        <button type="button" className="btn sm" onClick={onOpen}><Icon name="sparkle" size={14} />Open</button>
        {take.status === 'done' && (
          <div className="relief-animer" title="Tourne le modèle à l’angle voulu, puis anime-le : la vidéo part exactement de cette vue">
            <div className="label">Animer en vidéo</div>
            <div className="seg">
              {(Object.keys(FONDS_PLAN_CLE) as FondPlanCle[]).map((f) => <button key={f} type="button" className={fond === f ? 'on' : ''} onClick={() => setFond(f)}>{FONDS_PLAN_CLE[f].nom}</button>)}
            </div>
            <button type="button" className="btn sm accent" disabled={envoi} onClick={() => void animer()}><Icon name="sparkle" size={14} />{envoi ? 'Capture…' : 'Animer avec H3'}</button>
          </div>
        )}
      </div>
    </div>
    <ReliefOutils take={take} />
    </>
  );
}

/** Les trois temps du texte → 3D, avec la note du juge quand elle est tombée. */
function EtapesTexte({ e }: { e: ObjetTexteEtat }) {
  const ordre = ['image', 'objet', 'jugement', 'fini'] as const;
  const rang = e.etat === 'echec' ? -1 : ordre.indexOf(e.etat);
  const lignes = [
    ['Image de référence', 0], ['Modèle 3D', 1], ['Contrôle sur quatre côtés', 2],
  ] as const;
  const derniere = e.notes[e.notes.length - 1];
  return (
    <div className="rail-section" aria-live="polite">
      {lignes.map(([nom, i]) => (
        <div key={nom} style={{ display: 'flex', gap: 8, fontSize: 12.5, opacity: rang >= i || e.etat === 'fini' ? 1 : 0.5 }}>
          <span aria-hidden="true">{e.etat === 'fini' || rang > i ? '✓' : rang === i ? '…' : '·'}</span>
          <span>{nom}{i === 1 && e.essai > 1 ? ' (2e essai)' : ''}</span>
        </div>
      ))}
      {derniere && <div className="dim" style={{ fontSize: 12 }}>Juge : {derniere.note}/10{derniere.raison ? ` · ${derniere.raison}` : ''}</div>}
      {e.etat === 'echec' && <div style={{ fontSize: 12.5, color: 'var(--danger, #e5534b)' }}>{e.erreur ?? 'Échec.'}</div>}
    </div>
  );
}
