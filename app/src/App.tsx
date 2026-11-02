/** Coque de Nexora Creative (fork d'OpenField) : barre du haut + page routée. « Créer » est l'accueil. */
import { lazy, Suspense, useEffect } from 'react';
import { APPS_NEXORA } from './studio/apps';
import { linkProps, navigate, useRoute } from './router';
import { startLive, useStore } from './store';
import { useGlobalDrop } from './drop';
import { JudgeBanner, Toast } from './ui';
import { Marque } from './studio/icons';
import { Moteurs } from './studio/Moteurs';
import ImagePage from './pages/Image';
import UpscalePage from './pages/Upscale';
import Prolonger from './pages/Prolonger';
import EditPage from './pages/Edit';
import CastPage from './pages/Cast';
import CutoutPage from './pages/Cutout';
// three.js is only needed by Stage and Object: load them when opened, not on every page
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
const APP_LINKS = APPS_NEXORA.filter((a) => ['parler', 'prolonger', 'raccord', 'cast', 'cutout', 'upscale', 'object'].includes(a.id));
/**
 * Pages d'OpenField qui reposaient sur LTX-2.x (bloqué par la politique de licences) : leur adresse mène à l'outil
 * Nexora qui les remplace, jamais à un écran « indisponible ».
 */
const REMPLACEES: Record<string, string> = {
  '/video': '/?mode=video', '/director': '/?mode=film', '/extend': '/prolonger', '/speak': '/?mode=video&depart=photo',
  '/mirror': '/apps', '/reshoot': '/apps', '/effects': '/apps', '/stage': '/apps',
};

export default function App() {
  const { path, params } = useRoute();
  useEffect(() => { startLive(); }, []);
  const drop = useGlobalDrop();
  const judge = useStore((s) => !!s.status?.judge);

  useEffect(() => {
    const vers = REMPLACEES[path];
    if (!vers) return;
    const mode = path === '/extend' && params.get('mode') === 'transition' ? '/prolonger?mode=raccord' : vers;
    navigate(mode, true);
  }, [path]);

  const page = (() => {
    if (REMPLACEES[path]) return null;
    if (path === '/image') return <ImagePage />;
    if (path === '/prolonger') return <Prolonger />;
    if (path === '/upscale') return <UpscalePage />;
    if (path === '/edit') return <EditPage />;
    if (path === '/cast') return <CastPage />;
    if (path === '/cutout') return <CutoutPage />;
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
      : SECTIONS.find((s) => s.to === path)?.label ?? APPS_NEXORA.find((a) => a.route.split('?')[0] === path)?.name;
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
              <a {...linkProps('/?mode=video')}>Vidéo</a>
              <a {...linkProps('/?mode=image')}>Image</a>
              <a {...linkProps('/?mode=film')}>Film</a>
              <a {...linkProps('/edit')}>Retouche</a>
              <hr />
              {APP_LINKS.map((a) => <a key={a.id} {...linkProps(a.route)}>{a.name}{a.badge === 'new' && <span className="badge">Nouveau</span>}</a>)}
              <hr />
              <a {...linkProps('/apps')}>Tous les outils</a>
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
