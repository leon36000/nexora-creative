import { describe, expect, it } from 'vitest';
import { renderToStaticMarkup } from 'react-dom/server';
import { MeshLanguageSwitch } from './MeshLanguageSwitch';

describe('sélecteur de langue Mesh', () => {
  it('expose FR/EN et annonce la langue sélectionnée', () => {
    const html = renderToStaticMarkup(<MeshLanguageSwitch langue="en" onChange={() => {}} />);
    expect(html).toContain('aria-label="Interface language"');
    expect(html).toContain('aria-pressed="false">Français');
    expect(html).toContain('aria-pressed="true">English');
  });
});
