import { describe, expect, it } from 'vitest';
import { boiteOpaque } from './planCle3d';

describe('plan clé depuis Nexora Mesh', () => {
  it('trouve la boîte de l’objet dans une image à fond transparent', () => {
    const w = 10, h = 6, d = new Uint8ClampedArray(w * h * 4);
    for (const [x, y] of [[3, 1], [7, 4], [5, 2]]) d[(y * w + x) * 4 + 3] = 255;
    expect(boiteOpaque(d, w, h)).toEqual({ x: 3, y: 1, w: 5, h: 4 });
  });
  it('rend null quand la vue est vide', () => {
    expect(boiteOpaque(new Uint8ClampedArray(4 * 4 * 4), 4, 4)).toBeNull();
  });
});
