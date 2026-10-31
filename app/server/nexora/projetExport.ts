/**
 * Export d'un film comme projet de montage : les plans en MP4, une séquence Final Cut Pro 7 XML (« xmeml » v5, que
 * Premiere Pro, DaVinci Resolve et Final Cut importent) et le storyboard Nexora (format pivot, rien n'est perdu).
 * Les chemins des médias sont relatifs : le logiciel les retrouve à côté du fichier XML (ou propose de les relier).
 */

export interface PlanExporte { fichier: string; images: number; nom: string }

const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const RATE = '<rate><timebase>24</timebase><ntsc>FALSE</ntsc></rate>';

export function xmlFcp7(o: { titre: string; largeur: number; hauteur: number; son: boolean; plans: PlanExporte[] }): string {
  let debut = 0;
  const clips = o.plans.map((p, i) => {
    const c = { ...p, n: i + 1, start: debut, end: debut + p.images };
    debut += p.images;
    return c;
  });
  const fichier = (c: (typeof clips)[number], premier: boolean) =>
    premier
      ? `<file id="file-${c.n}"><name>${esc(c.fichier)}</name><pathurl>${esc(c.fichier)}</pathurl>${RATE}<duration>${c.images}</duration>` +
        `<media><video><samplecharacteristics><width>${o.largeur}</width><height>${o.hauteur}</height></samplecharacteristics></video>` +
        `${o.son ? '<audio><channelcount>2</channelcount></audio>' : ''}</media></file>`
      : `<file id="file-${c.n}"/>`;
  const clip = (c: (typeof clips)[number], piste: 'video' | 'audio') =>
    `<clipitem id="${piste}-${c.n}"><name>${esc(c.nom)}</name><duration>${c.images}</duration>${RATE}` +
    `<start>${c.start}</start>\n<end>${c.end}</end><in>0</in><out>${c.images}</out>${fichier(c, piste === 'video')}` +
    `${piste === 'audio' ? '<sourcetrack><mediatype>audio</mediatype><trackindex>1</trackindex></sourcetrack>' : ''}</clipitem>`;
  return [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<!DOCTYPE xmeml>',
    '<xmeml version="5">',
    `<sequence id="sequence-1"><name>${esc(o.titre)}</name><duration>${debut}</duration>${RATE}`,
    '<media>',
    `<video><format><samplecharacteristics>${RATE}<width>${o.largeur}</width><height>${o.hauteur}</height><pixelaspectratio>square</pixelaspectratio></samplecharacteristics></format>`,
    `<track>${clips.map((c) => clip(c, 'video')).join('\n')}</track></video>`,
    o.son ? `<audio><track>${clips.map((c) => clip(c, 'audio')).join('\n')}</track></audio>` : '',
    '</media>',
    '</sequence>',
    '</xmeml>',
    '',
  ].join('\n');
}
