// Modèles de pièces partagés (publications, stories, couvertures) : réutilisés par le social et la publicité.
import { C, BARRES, TXT, OUTILS, outil, mosaique, grille, regle, bande, cadre, grain, photo, voile, logo, glyphe, pastille, bouton, esc, affiche } from "./marque.mjs";
import { fondPhoto, fondMosaique, titre2, br, lignes, grilleOutils, VOILES } from "./compo.mjs";

/** Plan photographique de chaque outil (plans générés ; voir generer_bibliotheque.py). */
export const PLAN = {
  workstudio: { nom: "atelier", pos: "50% 55%" },
  code: { nom: "bureau-nuit", pos: "50% 50%" },
  rag: { nom: "carres-flottants", pos: "24% 50%" },
  bot: { nom: "cabane-neige", pos: "50% 50%" },
  creative: { nom: "aurore-foret", pos: "62% 50%" },
  webpilot: { nom: "fleuve-aube", pos: "50% 50%" },
  privacy: { nom: "phare", pos: "50% 50%" },
  vps: { nom: "salle-calcul", pos: "50% 50%" },
};
export const PLAN_V = {
  workstudio: { nom: "braises-montantes", pos: "50% 50%" }, code: { nom: "foret-vertical", pos: "50% 50%" }, rag: { nom: "mosaique-vertical", pos: "50% 50%" },
  bot: { nom: "foret-vertical", pos: "50% 50%" }, creative: { nom: "aurore-vertical", pos: "50% 50%" }, webpilot: { nom: "fleuve-vertical", pos: "50% 50%" },
  privacy: { nom: "phare-vertical", pos: "50% 50%" }, vps: { nom: "ville-vertical", pos: "50% 50%" },
};
const idx = (o) => OUTILS.findIndex((x) => x.id === o.id);

/** Publication 1080×1350 « photo » : un plan, un titre, une pastille. */
export function postPhoto(o, lang, { w = 1080, h = 1350, plan = PLAN[o.id], mos = true } = {}) {
  const k = w / 1080;
  const fond = fondPhoto({
    w, h, nom: plan.nom, pos: plan.pos, voiles: ["bas"],
    mos: mos ? { x: w * 0.56, y: 170 * k, w: w * 0.44, h: h * 0.42, cell: 26 * k, seed: 11 + idx(o) * 7, toward: "right", fade: 1, opacity: 0.92 } : null,
  });
  return affiche({ w, h, lang, k, fond, titre: lignes(o.titre[lang]), sous: o.sous[lang], pastilleOutil: o });
}
/** Publication 1080×1350 « mosaïque » : tout en code, grand glyphe dans un cadre de filets. */
export function postMosaique(o, lang, { w = 1080, h = 1350 } = {}) {
  const k = w / 1080, m = 80 * k;
  const g = 252 * k;
  const fond = fondMosaique({ w, h, k, mos: [{ x: w * 0.44, y: 170 * k, w: w * 0.56, h: h * 0.30 - 4 * k, cell: 30 * k, seed: 21 + idx(o) * 5, toward: "right", fade: 1, opacity: 1 }] });
  const cx = m, cy = 168 * k, cw = w - 2 * m, ch = h * 0.30;
  const centre = `${cadre({ x: cx, y: cy, w: cw, h: ch, k })}<div style="position:absolute;left:${cx + 52 * k}px;top:${cy + (ch - g) / 2}px">${glyphe(o.id, { size: g })}</div>`;
  return affiche({ w, h, lang, k, fond: fond + centre, titre: lignes(o.titre[lang]), sous: o.sous[lang], pastilleOutil: o });
}
export const postOutil = (o, lang, opts = {}) => (idx(o) % 2 === 0 ? postPhoto(o, lang, opts) : postMosaique(o, lang, opts));

/** Publication « manifeste » : une phrase, très grande, fond photo ou code. */
export function postManifeste({ w = 1080, h = 1350, lang, ligne1, ligne2, sous, kicker, plan, mos, taille = 132, centre = false }) {
  const k = w / 1080;
  const fond = plan
    ? fondPhoto({ w, h, nom: plan.nom, pos: plan.pos, voiles: plan.voiles ?? ["bas"], mos: mos ?? null })
    : fondMosaique({ w, h, k, mos: mos ?? [{ x: w * 0.25, y: 0, w: w * 0.75, h: h * 0.5, cell: 30 * k, seed: 5, toward: "right", fade: 1 }] });
  return affiche({ w, h, lang, k, fond, kicker, titre: ligne2 ? titre2(ligne1, ligne2) : esc(ligne1), sous, titreTaille: Math.round(taille * k) });
}

/** Story 1080×1920 : zones de sécurité (250 px en haut, 340 px en bas libres de tout élément essentiel). */
export function story({ lang, plan, mos, titre, sous, kicker, pastilleOutil, glyphId, k = 1, w = 1080, h = 1920, centre = false, grilleHuit = false, cta }) {
  const m = 80;
  const fond = plan
    ? fondPhoto({ w, h, nom: plan.nom, pos: plan.pos, voiles: plan.voiles ?? ["bas2"], mos })
    : fondMosaique({ w, h, k, mos });
  const parts = [fond];
  parts.push(`<div style="position:absolute;left:${m}px;top:250px">${logo({ type: "complet", ton: "blanc", h: 44 })}<div style="height:44px"></div></div>`);
  if (pastilleOutil) parts.push(`<div style="position:absolute;left:${m}px;top:330px">${pastille(pastilleOutil, lang, { k: 1.6, etat: false })}</div>`);
  if (glyphId) parts.push(`<div style="position:absolute;left:${m}px;top:${h * 0.34}px">${glyphe(glyphId, { size: 300 })}</div>`);
  if (grilleHuit) parts.push(grilleOutils({ x: m, y: 420, w: w - 2 * m, h: 700, cols: 2, k: 1.0, lang, glyph: 64, horizontal: true, label: 28 }));
  const bottom = 340 + 30;
  parts.push(`<div style="position:absolute;left:${m}px;right:${m}px;bottom:${bottom}px;display:flex;flex-direction:column;gap:30px">
    ${kicker ? `<div class="lib" style="font-size:30px;color:${C.orTxt}">${esc(kicker)}</div>` : ""}
    <div class="aff" data-fit style="font-size:126px;max-height:560px;overflow:hidden">${titre}</div>
    ${sous ? `<div class="txt" data-fit style="font-size:36px;color:${C.gris};max-height:200px;overflow:hidden;max-width:860px">${esc(sous)}</div>` : ""}
    ${cta ? `<div style="margin-top:6px">${bouton(cta, { k: 1.3 })}</div>` : ""}
  </div>`);
  return parts.join("");
}
