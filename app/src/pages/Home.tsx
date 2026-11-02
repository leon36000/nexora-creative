/** Explore (home), Apps gallery, Library, and the "coming" placeholder. */
import { useState } from 'react';
import { mediaUrl, posterUrl } from '../api';
import { APPS, type AppDef } from '../catalog';
import { APPS_NEXORA, CATEGORIES_NEXORA, MODELES, type ModeleProduction } from '../studio/apps';
import { linkProps, navigate, setParams, useRoute } from '../router';
import { isImage, isModel, settingsOf, useStore, inFeed } from '../store';
import { Clip, Icon, MediaCard, presetClip } from '../ui';
import Viewer, { recreate, remove } from '../Viewer';

/** Cover art for an app: a curated rendered clip, so a fresh install never shows an empty card. */
function AppArt({ app }: { app: AppDef }) {
  return <Clip src={app.clip ?? presetClip(app.cover)} />;
}

/** Explorer : modèles prêts à produire (un clic → le Producteur propose plan et devis), outils, créations récentes. */
export function Explore() {
  const recent = useStore((s) => s.takes.filter((t) => inFeed(t) && t.status === 'done' && !settingsOf(t).nexoraFilm && t.kind !== 'audio').slice(0, 8));
  const [viewing, setViewing] = useState<number | null>(null);
  const [cat, setCat] = useState<'tout' | ModeleProduction['cat']>('tout');
  return (
    <div className="page-scroll">
      <div className="st">
        <section className="st-hero">
          <div>
            <h1>Choisis un modèle. <em>Le Producteur</em> fait le reste.</h1>
            <p>Un clic envoie l’objectif au Producteur IA : il propose le découpage, la musique, les textes et le devis. Tu ajustes ou tu lances.</p>
          </div>
          <div className="st-filtres" role="group" aria-label="Catégories">
            {([['tout', 'Tout'], ['pub', 'Publicité'], ['social', 'Réseaux'], ['film', 'Film']] as const).map(([v, l]) => (
              <button key={v} type="button" className={cat === v ? 'on' : ''} onClick={() => setCat(v)}>{l}</button>
            ))}
          </div>
        </section>
        <div className="ex-modeles">
          {MODELES.filter((m) => cat === 'tout' || m.cat === cat).map((m) => (
            <a key={m.id} className="ex-modele" {...linkProps(`/?objectif=${encodeURIComponent(m.objectif)}`)} title={m.objectif}>
              <Clip src={m.clip} />
              <span className="ex-modele-txt"><b>{m.nom}</b><small>{m.objectif}</small></span>
              <span className="ex-go">Produire ›</span>
            </a>
          ))}
        </div>

        <div className="st-g-tete"><h2>Outils</h2><a className="nx-lien" {...linkProps('/apps')}>Tous les outils</a></div>
        <div className="tiles">
          {APPS_NEXORA.slice(0, 9).map((a) => (
            <a key={a.id} className="tile" {...linkProps(a.route)}>
              <span className="ico"><Icon name={a.icon} /></span>
              <span><b>{a.name}</b> {a.badge === 'new' && <span className="badge" style={{ marginLeft: 6 }}>Nouveau</span>}<div className="dim" style={{ fontSize: 12.5, marginTop: 3 }}>{a.blurb}</div></span>
            </a>
          ))}
        </div>

        {recent.length > 0 && <>
          <div className="st-g-tete"><h2>Tes dernières créations</h2><a className="nx-lien" {...linkProps('/library')}>Bibliothèque</a></div>
          <div className="grid dense">{recent.map((t) => <MediaCard key={t.id} take={t} onOpen={() => setViewing(t.id)} />)}</div>
        </>}
      </div>
      {viewing !== null && <Viewer takeId={viewing} onClose={() => setViewing(null)} onStep={() => {}} />}
    </div>
  );
}

export function Apps() {
  const { params } = useRoute();
  const cat = params.get('cat') || 'all';
  const [q, setQ] = useState('');
  const list = APPS_NEXORA.filter((a) => (cat === 'all' || a.cat === cat) && (!q || `${a.name} ${a.blurb}`.toLowerCase().includes(q.toLowerCase())));
  return (
    <div className="page-scroll">
      <div className="st">
        <section className="st-hero">
          <div>
            <h1>Tous les <em>outils</em>.</h1>
            <p>MiniMax H3 pour la vidéo, Qwen-Image pour l’image, MiniMax-Music3 pour la musique. Chaque outil affiche son coût avant de lancer.</p>
          </div>
        </section>
        <div className="picker-top" style={{ margin: 0, flexWrap: 'wrap', gap: 8 }}>
          <div style={{ position: 'relative' }}>
            <input className="field" style={{ width: 240, maxWidth: '100%', padding: '8px 10px 8px 30px' }} placeholder="Chercher un outil" value={q} onChange={(e) => setQ(e.target.value)} />
            <span style={{ position: 'absolute', left: 10, top: 10, color: 'var(--mute)' }}><Icon name="search" size={14} /></span>
          </div>
          {CATEGORIES_NEXORA.map((c) => <button key={c.id} type="button" className={`pill ${cat === c.id ? 'active' : ''}`} onClick={() => setParams({ cat: c.id === 'all' ? null : c.id })}>{c.label}</button>)}
        </div>
        <div className="grid" style={{ gridTemplateColumns: 'repeat(auto-fill, minmax(230px, 1fr))' }}>
          {list.map((a) => (
            <div key={a.id} className="app-card">
              <a className="media" {...linkProps(a.route)}>
                <AppArt app={a} />
                {a.badge === 'new' && <span className="badge" style={{ position: 'absolute', top: 10, left: 10, zIndex: 2 }}>Nouveau</span>}
                <span className="name display">{a.name}</span>
              </a>
              <div className="body">
                <p>{a.blurb}</p>
                <a className="btn sm try" {...linkProps(a.route)}>Ouvrir</a>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export function Library() {
  const { params } = useRoute();
  const filter = params.get('filter') || 'all';
  const all = useStore((s) => s.takes.filter(inFeed));
  const takes = all.filter((t) =>
    filter === 'image' ? isImage(t) : filter === 'video' ? !isImage(t) && !isModel(t) : filter === '3d' ? isModel(t) : filter === 'favorites' ? !!t.starred : true);
  const done = takes.filter((t) => t.status === 'done');
  const [viewing, setViewing] = useState<number | null>(null);
  const step = (dir: 1 | -1) => {
    const i = done.findIndex((t) => t.id === viewing);
    const n = done[(i + dir + done.length) % done.length];
    if (n) setViewing(n.id);
  };
  return (
    <div className="page-scroll">
      <div className="page-pad" style={{ maxWidth: 1600 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 18, flexWrap: 'wrap' }}>
          <h1 className="display" style={{ fontSize: 40, margin: '0 14px 0 0' }}>Bibliothèque</h1>
          {([['all', 'Tout'], ['image', 'Images'], ['video', 'Vidéos'], ['3d', '3D'], ['favorites', 'Favoris']] as const).map(([f, l]) => (
            <button key={f} type="button" className={`pill ${filter === f ? 'active' : ''}`} onClick={() => setParams({ filter: f === 'all' ? null : f })}>{l}</button>
          ))}
          <span className="dim" style={{ marginLeft: 'auto' }}>{done.length} créations</span>
        </div>
        {takes.length === 0 ? <div className="empty">Rien pour l’instant. Tout ce que tu crées arrive ici automatiquement.</div> : (
          <div className="grid dense">
            {takes.map((t) => (
              <MediaCard key={t.id} take={t} onOpen={() => setViewing(t.id)} actions={<>
                {isImage(t) && t.status === 'done' && <button type="button" className="icon-btn" title="Animer avec MiniMax H3" onClick={() => navigate(`/?mode=video&cle=${t.id}`)}><Icon name="video" size={14} /></button>}
                {!isImage(t) && !isModel(t) && t.status === 'done' && !settingsOf(t).film && <button type="button" className="icon-btn" title="Prolonger" onClick={() => navigate(`/prolonger?take=${t.id}`)}><Icon name="plus" size={14} /></button>}
                <button type="button" className="icon-btn" title="Refaire" onClick={() => void recreate(t)}><Icon name="redo" size={14} /></button>
                <button type="button" className="icon-btn" title="Supprimer" onClick={() => void remove(t)}><Icon name="trash" size={14} /></button>
              </>} />
            ))}
          </div>
        )}
      </div>
      {viewing !== null && <Viewer takeId={viewing} onClose={() => setViewing(null)} onStep={step} />}
    </div>
  );
}

export function Soon({ appId }: { appId: string }) {
  const a = APPS.find((x) => x.id === appId)!;
  return (
    <div className="page-scroll">
      <div className="hero-empty">
        <div className="label" style={{ marginBottom: 14 }}>À l’atelier</div>
        <div className="display" style={{ fontSize: 'clamp(40px,6vw,80px)' }}>{a.name}</div>
        <p className="dim" style={{ maxWidth: 520, margin: '16px auto 0' }}>{a.blurb}</p>
        <a className="btn" style={{ marginTop: 22 }} {...linkProps('/apps')}>Retour aux outils</a>
      </div>
    </div>
  );
}
