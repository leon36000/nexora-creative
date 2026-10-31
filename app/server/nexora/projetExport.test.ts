import { describe, expect, it } from 'vitest';
import { xmlFcp7 } from './projetExport.js';

describe('séquence Final Cut Pro 7 XML (Premiere, DaVinci Resolve, Final Cut)', () => {
  const xml = xmlFcp7({
    titre: 'Robot & voiture <rouge>',
    largeur: 832, hauteur: 480, son: true,
    plans: [{ fichier: 'plan01.mp4', images: 124, nom: 'La voiture' }, { fichier: 'plan02.mp4', images: 243, nom: 'Transformation' }],
  });

  it('déclare une séquence à 24 i/s de la bonne durée et taille', () => {
    expect(xml).toMatch(/^<\?xml version="1.0" encoding="UTF-8"\?>\n<!DOCTYPE xmeml>\n<xmeml version="5">/);
    expect(xml).toMatch(/<sequence id="sequence-1">[\s\S]*<duration>367<\/duration>/);
    expect(xml).toMatch(/<timebase>24<\/timebase>/);
    expect(xml).toMatch(/<width>832<\/width>[\s\S]*<height>480<\/height>/);
  });

  it('place les plans bout à bout sur la piste vidéo et la piste son', () => {
    expect(xml).toMatch(/<clipitem id="video-2">[\s\S]*?<start>124<\/start>\s*<end>367<\/end>/);
    expect(xml).toMatch(/<clipitem id="audio-2">[\s\S]*?<start>124<\/start>/);
    expect(xml).toMatch(/<pathurl>plan02.mp4<\/pathurl>/);
  });

  it('échappe le XML', () => {
    expect(xml).toMatch(/Robot &amp; voiture &lt;rouge&gt;/);
    expect(xml).not.toMatch(/<rouge>/);
  });

  it('n’écrit pas de piste son quand le film est muet', () => {
    const muet = xmlFcp7({ titre: 't', largeur: 832, hauteur: 480, son: false, plans: [{ fichier: 'a.mp4', images: 121, nom: 'a' }] });
    expect(muet).not.toMatch(/audio-1/);
  });
});
