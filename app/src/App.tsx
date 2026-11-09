/** Coque de Nexora Creative (fork d'OpenField) : barre du haut + page routée. « Créer » est l'accueil. */
import { estRoute3D } from './produit3d.js';
import { lazy, Suspense, useEffect, useState } from 'react';
import { APPS_NEXORA } from './studio/apps';
import { navigate, useRoute } from './router';
import { prolongerRedirect } from './prolongerRedirect';
import { startLive, useStore } from './store';
import { useGlobalDrop } from './drop';
import { JudgeBanner, Toast } from './ui';
import { Moteurs } from './studio/Moteurs';
import { NEXORA_PRODUCT_NAMES } from '../shared/productNames.js';
import type { LangueClient } from '../shared/creationLanguage.js';
import { attributLangueDocument, enregistrerLangueInterface, lireLangueInterface, libellesNavigation, langueContenuPrincipal, nomAppNavigation } from './interfaceLanguage.js';
import { GlobalNavigation } from './GlobalNavigation.js';
import ImagePage from './pages/Image';
import UpscalePage from './pages/Upscale';
import Prolonger from './pages/Prolonger';
import EditPage from './pages/Edit';
import CastPage from './pages/Cast';
import ProjetPage from './pages/Projet';
import CutoutPage from './pages/Cutout';
import DetouragePage from './pages/Detourage';
// three.js is only needed by Stage and Object: load them when opened, not on every page
const ObjectPage = lazy(() => import('./pages/Object'));
import { Apps, Explore, Library, Soon } from './pages/Home';
import Setup from './pages/Setup';
import Creer from './pages/Creer';
import MarketingPage from './pages/Marketing';

const APP_LINKS = APPS_NEXORA.filter((a) => ['marketing', 'parler', 'prolonger', 'raccord', 'cast', 'projet', 'cutout', 'detourage', 'upscale', 'object'].includes(a.id));
const CREATIVE_NAME = NEXORA_PRODUCT_NAMES.creative;
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
  const [langueInterface, setLangueInterface] = useState<LangueClient>(lireLangueInterface);
  const copy = libellesNavigation(langueInterface);
  const langueContenu = langueContenuPrincipal(path, langueInterface);
  useEffect(() => { startLive(); }, []);
  useEffect(() => {
    enregistrerLangueInterface(langueInterface);
    document.documentElement.lang = attributLangueDocument(langueContenu);
  }, [langueContenu]);
  const drop = useGlobalDrop();
  const judge = useStore((s) => !!s.status?.judge);

  useEffect(() => {
    const vers = REMPLACEES[path];
    if (!vers) return;
    const destination = path === '/extend' ? prolongerRedirect(params) : vers;
    navigate(destination, true);
  }, [path]);

  const page = (() => {
    if (REMPLACEES[path]) return null;
    if (path === '/image') return <ImagePage />;
    if (path === '/prolonger') return <Prolonger />;
    if (path === '/upscale') return <UpscalePage />;
    if (path === '/edit') return <EditPage />;
    if (path === '/cast') return <CastPage />;
    if (path === '/projet') return <ProjetPage />;
    if (path === '/cutout') return <CutoutPage />;
    if (path === '/detourage') return <DetouragePage />;
    if (estRoute3D(path)) return <ObjectPage langue={langueInterface} onLangueChange={setLangueInterface} />;
    if (path === '/marketing') return <MarketingPage />;
    if (path === '/apps') return <Apps />;
    if (path === '/library') return <Library />;
    if (path === '/setup') return <Setup />;
    if (path === '/explorer') return <Explore />;
    return <Creer />;
  })();

  // le menu Atelier se referme à chaque navigation
  useEffect(() => { document.querySelectorAll('.st-atelier').forEach((d) => d.removeAttribute('open')); }, [path]);

  // Keep the browser tab language in step with the shared shell and Mesh language.
  useEffect(() => {
    const name = path === '/' ? copy.create : path === '/setup' ? copy.settings : path === '/library' ? copy.library
      : path === '/explorer' ? copy.explore : copy.pageTitles[path]
        ?? (() => {
          const app = APPS_NEXORA.find((a) => a.route.split('?')[0] === path);
          return app ? nomAppNavigation(app.id, app.name, langueInterface) : undefined;
        })();
    document.title = name ? `${name} · ${CREATIVE_NAME}` : CREATIVE_NAME;
  }, [path, langueInterface, copy]);

  const appLinks = APP_LINKS.map((a) => ({
    id: a.id, to: a.route, label: nomAppNavigation(a.id, a.name, langueInterface), badge: a.badge,
  }));

  return (
    <div className={`app ${judge ? 'has-judge' : ''}`} lang={attributLangueDocument(langueContenu)}>
      <GlobalNavigation langue={langueInterface} path={path} params={params} apps={appLinks}>
        <Moteurs langue={langueInterface} />
      </GlobalNavigation>
      <JudgeBanner />
      <main className="main" lang={attributLangueDocument(langueContenu)}><Suspense fallback={null}>{page}</Suspense></main>
      {drop.dragging && drop.label && <div className="drop-veil" aria-hidden><span>{drop.label}</span></div>}
      <Toast />
    </div>
  );
}
