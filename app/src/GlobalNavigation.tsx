import type { ReactNode } from 'react';
import { NEXORA_BRAND, NEXORA_PRODUCT_NAMES } from '../shared/productNames.js';
import type { LangueClient } from '../shared/creationLanguage.js';
import { libellesNavigation } from './interfaceLanguage.js';
import { linkProps } from './router.js';
import { Marque } from './studio/icons.js';

export interface LienNavigation {
  id: string;
  to: string;
  label: string;
  badge?: string;
}

interface Props {
  langue: LangueClient;
  path: string;
  params: URLSearchParams;
  apps: LienNavigation[];
  children?: ReactNode;
}

export function GlobalNavigation({ langue, path, params, apps, children }: Props) {
  const copy = libellesNavigation(langue);
  const creativeName = NEXORA_PRODUCT_NAMES.creative;
  const creativeLabel = creativeName.slice(NEXORA_BRAND.length + 1);
  const isActive = (to: string) => {
    if (to === '/') return path === '/';
    const [p, q] = to.split('?');
    if (p !== path) return false;
    if (!q) return !(path === '/video' && params.get('mode') === 'loop');
    return [...new URLSearchParams(q)].every(([k, v]) => params.get(k) === v);
  };

  return (
    <header className="st-top" lang={langue === 'en' ? 'en-CA' : 'fr-CA'}>
      <a className="st-brand" {...linkProps('/')}><Marque className="st-mark" /><span>{NEXORA_BRAND} <em>{creativeLabel}</em></span></a>
      <nav className="st-nav" aria-label={copy.navLabel}>
        <a className={`st-link ${isActive('/') ? 'active' : ''}`} {...linkProps('/')}>{copy.create}</a>
        <a className={`st-link ${isActive('/marketing') ? 'active' : ''}`} {...linkProps('/marketing')}>{copy.marketing}</a>
        <a className={`st-link ${isActive('/library') ? 'active' : ''}`} {...linkProps('/library')}>{copy.library}</a>
        <a className={`st-link ${isActive('/explorer') ? 'active' : ''}`} {...linkProps('/explorer')}>{copy.explore}</a>
        <a className="st-link st-link-studio" href="/mode-studio/" title={copy.studioTitle}>{copy.studioMode}</a>
        <details className="st-atelier">
          <summary className="st-link">{copy.workshop} ▾</summary>
          <div className="st-menu">
            <a {...linkProps('/?mode=video')}>{copy.video}</a>
            <a {...linkProps('/?mode=image')}>{copy.image}</a>
            <a {...linkProps('/?mode=film')}>{copy.film}</a>
            <a {...linkProps('/edit')}>{copy.edit}</a>
            <hr />
            {apps.map((app) => <a key={app.id} {...linkProps(app.to)}>{app.label}{app.badge === 'new' && <span className="badge">{copy.newBadge}</span>}</a>)}
            <hr />
            <a {...linkProps('/apps')}>{copy.allTools}</a>
          </div>
        </details>
      </nav>
      <div className="st-right">
        {children}
        <a className={`st-link ${isActive('/setup') ? 'active' : ''}`} {...linkProps('/setup')} title={copy.settingsTitle}>{copy.settings}</a>
      </div>
    </header>
  );
}
