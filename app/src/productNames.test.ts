import { describe, expect, it } from 'vitest';
import { NEXORA_BRAND, NEXORA_PRODUCT_NAMES } from '../shared/productNames.js';
import { APPS } from './catalog';
import { PRODUIT_3D, ROUTE_3D } from './produit3d.js';
import { APPS_NEXORA } from './studio/apps';

describe('noms centraux des produits Nexora', () => {
  it('centralise les quinze noms produit et le nom de la coque', () => {
    expect(NEXORA_BRAND).toBe('Nexora');
    expect(Object.values(NEXORA_PRODUCT_NAMES)).toEqual([
      'Nexora Creative', 'Nexora Mesh', 'Nexora Matte', 'Nexora Director', 'Nexora Producer', 'Nexora Studio', 'Nexora Sync', 'Nexora Voice', 'Nexora Score', 'Nexora FX', 'Nexora Finish', 'Nexora Critic', 'Nexora Scribe', 'Nexora Campaign', 'Nexora Connect', 'Nexora Platform',
    ]);
  });

  it('relie le catalogue Nexora et PRODUIT_3D à cette source sans modifier leurs routes', () => {
    const app = (id: string) => APPS_NEXORA.find((entry) => entry.id === id)!;
    expect(PRODUIT_3D).toBe(NEXORA_PRODUCT_NAMES.mesh);
    expect(APPS.find((entry) => entry.id === 'object')).toMatchObject({ name: NEXORA_PRODUCT_NAMES.mesh, route: ROUTE_3D });
    expect(app('object')).toMatchObject({ name: NEXORA_PRODUCT_NAMES.mesh, route: ROUTE_3D });
    expect(app('producteur')).toMatchObject({ name: NEXORA_PRODUCT_NAMES.producer, route: '/' });
    expect(app('marketing')).toMatchObject({ name: NEXORA_PRODUCT_NAMES.campaign, route: '/marketing' });
    expect(app('detourage')).toMatchObject({ name: NEXORA_PRODUCT_NAMES.matte, route: '/detourage' });
  });

  it('ne présente pas le palier pro indisponible comme une fonction de Matte', () => {
    const matte = APPS_NEXORA.find((entry) => entry.id === 'detourage')!;
    expect(matte.name).toBe('Nexora Matte');
    expect(matte.blurb).not.toMatch(/\bpro\b|prores|16 bits|\bEXR\b/i);
    expect(matte.blurb).not.toMatch(/SAM 3\.1|ViTMatte/i);
    expect(matte.blurb).toBe('Détoure un sujet dans une vidéo, puis garde la transparence ou choisis un nouveau fond.');
  });
});
