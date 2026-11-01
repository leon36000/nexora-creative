// Discord / Slack : bannière, icônes de serveur et d'espace, huit émojis (glyphes) 128×128 sur fond transparent.
import { C, TXT, OUTILS, outil, mosaique, grille, regle, cadre, grain, voile, logo, glyphe, esc } from "./moteur/marque.mjs";
import { fondPhoto, fondMosaique, titre2 } from "./moteur/compo.mjs";
import { F, profil } from "./fb.mjs";
const LANGS = ["fr", "en"];
const split = (s) => [s.split(". ")[0] + ".", s.split(". ").slice(1).join(". ")];
export function banniere(lang) {
  const w = 960, h = 540, [c1, c2] = split(TXT.campagne[lang]);
  const body = fondMosaique({ w, h, mos: { x: w * .7, y: 0, w: w * .3, h, cell: 20, seed: 601, toward: "right", fade: 1 } }) + regle({ w, k: .6, side: "bottom" })
    + `${logo({ type: "complet", ton: "sombre", h: 28, x: 48, y: 48 })}<div style="position:absolute;left:48px;bottom:70px;width:560px;display:flex;flex-direction:column;gap:16px"><div class="lib" style="font-size:13px;color:${C.orTxt}">${esc(TXT.quebecCourt[lang])}</div><div class="aff" data-fit style="font-size:64px;max-height:140px;overflow:hidden">${titre2(c1, c2)}</div></div>`;
  return F.piece({ id: `banniere.${lang}`, sousDossier: "discord-slack", w, h, lang, body });
}
export function emojis() {
  return OUTILS.map((o) => F.piece({ id: `emoji-${o.id}`, sousDossier: "discord-slack/emojis", w: 128, h: 128, body: `<div style="position:absolute;left:14px;top:14px">${glyphe(o.id, { size: 100 })}</div>`, transparent: true, fit: false, title: `Émoji ${o.nom}` }));
}
export function toutChat() {
  return [profil("icone-discord-512", "discord-slack", 512), profil("icone-slack-512", "discord-slack", 512), ...LANGS.map(banniere), ...emojis()];
}
