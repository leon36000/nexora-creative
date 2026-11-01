/** Coque de Nexora Creative (fork d'OpenField) : barre du haut + page routée. « Créer » est l'accueil. */
import { lazy, Suspense, useEffect } from 'react';
import { APPS, badgeLabel } from './catalog';
import { linkProps, useRoute } from './router';
import { startLive, useStore } from './store';
import { useGlobalDrop } from './drop';
import { JudgeBanner, Toast } from './ui';
import { Marque } from './studio/icons';
import { Moteurs } from './studio/Moteurs';
import VideoPage from './pages/Video';
import ImagePage from './pages/Image';
import DirectorPage from './pages/Director';
import MirrorPage from './pages/Mirror';
import ReshootPage from './pages/Reshoot';
import EffectsPage from './pages/Effects';
import UpscalePage from './pages/Upscale';
import ExtendPage from './pages/Extend';
import SpeakPage from './pages/Speak';
import EditPage from './pages/Edit';
import CastPage from './pages/Cast';
import CutoutPage from './pages/Cutout';
// three.js is only needed by Stage and Object: load them when opened, not on every page
const StagePage = lazy(() => import('./pages/Stage'));
const ObjectPage = lazy(() => import('./pages/Object'));
import { Apps, Explore, Library, Soon } from './pages/Home';
import Setup from './pages/Setup';
import Creer from './pages/Creer';

const SECTIONS = [
  { to: '/', label: 'Créer' },
  { to: '/explorer', label: 'Explorer' },
  { to: '/image', label: 'Image' },
  { to: '/edit', label: 'Retouche' },
  { to: '/video', label: 'Vidéo' },
  { to: '/apps', label: 'Outils' },
  { to: '/library', label: 'Bibliothèque' },
];
const APP_LINKS = APPS.filter((a) => ['director', 'stage', 'loop', 'mirror', 'reshoot', 'upscale'].includes(a.id));

export default function App() {
  const { path, params } = useRoute();
  useEffect(() => { startLive(); }, []);
  const drop = useGlobalDrop();
  const judge = useStore((s) => !!s.status?.judge);

  const page = (() => {
    if (path === '/image') return <ImagePage />;
    if (path === '/video') return <VideoPage />;
    if (path === '/director') return <DirectorPage />;
    if (path === '/mirror') return <MirrorPage />;
    if (path === '/reshoot') return <ReshootPage />;
    if (path === '/effects') return <EffectsPage />;
    if (path === '/upscale') return <UpscalePage />;
    if (path === '/extend') return <ExtendPage />;
    if (path === '/speak') return <SpeakPage />;
    if (path === '/edit') return <EditPage />;
    if (path === '/cast') return <CastPage />;
    if (path === '/cutout') return <CutoutPage />;
    if (path === '/stage') return <StagePage />;
    if (path === '/object') return <ObjectPage />;
    if (path === '/apps') return <Apps />;
    if (path === '/library') return <Library />;
    if (path === '/setup') return <Setup />;
    if (path === '/explorer') return <Explore />;
    return <Creer />;
  })();

  // le menu Atelier se referme à chaque navigation
  useEffect(() => { document.querySelectorAll('.st-atelier').forEach((d) => d.removeAttribute('open')); }, [path]);

  // the tab says where you are
  useEffect(() => {
    const name = path === '/' ? 'Créer' : path === '/setup' ? 'Réglages' : path === '/library' ? 'Bibliothèque'
      : SECTIONS.find((s) => s.to === path)?.label ?? APPS.find((a) => a.route.split('?')[0] === path)?.name;
    document.title = name ? `${name} · Nexora Creative` : 'Nexora Creative';
  }, [path]);

  const isActive = (to: string) => {
    if (to === '/') return path === '/';
    const [p, q] = to.split('?');
    if (p !== path) return false;
    if (!q) return !(path === '/video' && params.get('mode') === 'loop');
    return [...new URLSearchParams(q)].every(([k, v]) => params.get(k) === v);
  };

  return (
    <div className={`app ${judge ? 'has-judge' : ''}`}>
      <header className="st-top">
        <a className="st-brand" {...linkProps('/')}><Marque className="st-mark" /><span>Nexora <em>Creative</em></span></a>
        <nav className="st-nav" aria-label="Navigation principale">
          <a className={`st-link ${isActive('/') ? 'active' : ''}`} {...linkProps('/')}>Créer</a>
          <a className={`st-link ${isActive('/library') ? 'active' : ''}`} {...linkProps('/library')}>Bibliothèque</a>
          <a className={`st-link ${isActive('/explorer') ? 'active' : ''}`} {...linkProps('/explorer')}>Explorer</a>
          {/* Mode Studio : le montage expert (éditeur FreeCut servi sous /mode-studio/, page à part). */}
          <a className="st-link st-link-studio" href="/mode-studio/" title="Montage expert assisté par l’IA">Mode Studio</a>
          <details className="st-atelier">
            <summary className="st-link">Atelier ▾</summary>
            <div className="st-menu">
              {SECTIONS.filter((x) => ['/image', '/edit', '/video', '/apps'].includes(x.to)).map((x) => <a key={x.to} {...linkProps(x.to)}>{x.label}</a>)}
              <hr />
              {APP_LINKS.map((a) => <a key={a.id} {...linkProps(a.route)}>{a.name}{a.badge === 'new' && <span className="badge">{badgeLabel(a.badge)}</span>}</a>)}
            </div>
          </details>
        </nav>
        <div className="st-right">
          <Moteurs />
          <a className={`st-link ${isActive('/setup') ? 'active' : ''}`} {...linkProps('/setup')} title="Modèles et réglages">Réglages</a>
        </div>
      </header>
      <JudgeBanner />
      <main className="main"><Suspense fallback={null}>{page}</Suspense></main>
      {drop.dragging && drop.label && <div className="drop-veil" aria-hidden><span>{drop.label}</span></div>}
      <Toast />
    </div>
  );
}
