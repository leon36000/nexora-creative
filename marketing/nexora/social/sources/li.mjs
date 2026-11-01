// LinkedIn : bannière de page, bannière personnelle, 6 publications 1200×627, image de partage, carrousel PDF de 8 pages.
import path from "node:path";
import { C, TXT, OUTILS, outil, mosaique, grille, regle, cadre, grain, voile, logo, glyphe, pastille, bouton, esc, BARRES, rendrePdf } from "./moteur/marque.mjs";
import { fondPhoto, fondMosaique, titre2, grilleOutils, lignes } from "./moteur/compo.mjs";
import { F, partage } from "./fb.mjs";
const LANGS = ["fr", "en"];
const D = "linkedin";
const split = (s) => [s.split(". ")[0] + ".", s.split(". ").slice(1).join(". ")];

export function bannieres(lang) {
  const w = 1584, h = 396, [c1, c2] = split(TXT.campagne[lang]);
  const page = fondMosaique({ w, h, grid: true, mos: [{ x: w * 0.55, y: 0, w: w * 0.45, h, cell: 22, seed: 301, toward: "right", fade: 1 }] }) + regle({ w, k: 1, side: "bottom" })
    + `<div style="position:absolute;left:340px;top:0;height:${h}px;width:760px;display:flex;flex-direction:column;justify-content:center;gap:20px">
    <div class="lib" style="font-size:17px;color:${C.orTxt}">${esc(TXT.quebecCourt[lang])}</div>
    <div class="aff" data-fit style="font-size:66px;max-height:150px;overflow:hidden">${titre2(c1, c2)}</div></div>
    ${logo({ type: "complet", ton: "sombre", h: 28, x: 56, y: 36 })}`;
  const perso = fondPhoto({ w, h, nom: "aurore-lac", pos: "50% 18%", voiles: ["gauche"], grainOp: .1, mos: { x: 0, y: 0, w: 380, h, cell: 22, seed: 302, toward: "left", fade: 1, opacity: .85 } })
    + `<div style="position:absolute;left:560px;top:0;height:${h}px;width:900px;display:flex;flex-direction:column;justify-content:center;gap:18px">
    <div class="aff" data-fit style="font-size:56px;max-height:140px;overflow:hidden">${esc(TXT.signature[lang].split(". ")[0] + ".")}<br><span style="color:${C.orTxt}">${esc(TXT.signature[lang].split(". ")[1])}</span></div>
    <div class="lib" style="font-size:16px;color:${C.gris}">${esc(TXT.quebec[lang])}</div></div>`;
  return [F.piece({ id: `banniere-page.${lang}`, sousDossier: D, w, h, lang, body: page }), F.piece({ id: `banniere-personnelle.${lang}`, sousDossier: D, w, h, lang, body: perso })];
}

/** Publication paysage 1200×627 : texte à gauche, visuel à droite. */
function postPaysage({ lang, kicker, titre, sous, visuel, cta, id }) {
  const w = 1200, h = 627, m = 64;
  const fond = visuel === "photo-reve" ? fondPhoto({ w, h, nom: "aurore-foret", pos: "60% 40%", voiles: ["gauche"] })
    : visuel === "photo-quebec" ? fondPhoto({ w, h, nom: "fleuve-aube", pos: "50% 50%", voiles: ["gauche"] })
    : visuel === "photo-phare" ? fondPhoto({ w, h, nom: "phare", pos: "50% 50%", voiles: ["gauche"] })
    : visuel === "huit" ? fondMosaique({ w, h }) + grilleOutils({ x: w * 0.5, y: 96, w: w * 0.5 - m, h: h - 192, cols: 2, k: 0.8, lang, glyph: 56, horizontal: true, label: 26 })
    : visuel === "workstudio" ? fondMosaique({ w, h, mos: { x: w * 0.45, y: 0, w: w * 0.55, h, cell: 26, seed: 311, toward: "right", fade: 1 } }) + `<div style="position:absolute;right:${m}px;top:${(h - 270) / 2}px;width:270px;height:270px;background:${C.noir};border:1px solid rgba(245,244,239,.26);display:flex;align-items:center;justify-content:center">${glyphe("workstudio", { size: 170 })}</div>`
    : fondMosaique({ w, h, mos: { x: w * 0.4, y: 0, w: w * 0.6, h, cell: 26, seed: 312, toward: "right", fade: 1 } });
  const body = `${fond}${logo({ type: "complet", ton: "blanc", h: 36, x: m, y: m })}
    <div style="position:absolute;left:${m}px;bottom:${m + 14}px;width:${w * 0.54}px;display:flex;flex-direction:column;gap:20px">
      ${kicker ? `<div class="lib" style="font-size:24px;color:${C.orTxt}">${esc(kicker)}</div>` : ""}
      <div class="aff" data-fit style="font-size:72px;max-height:250px;overflow:hidden">${titre}</div>
      ${sous ? `<div class="txt" data-fit style="font-size:30px;color:${C.gris};max-height:100px;overflow:hidden">${esc(sous)}</div>` : ""}
      ${cta ? `<div>${bouton(cta, { k: .7 })}</div>` : ""}
    </div>`;
  return F.piece({ id, sousDossier: `${D}/publications`, w, h, lang, body });
}
export function publications(lang) {
  const [c1, c2] = split(TXT.campagne[lang]);
  const fr = lang === "fr";
  return [
    postPaysage({ lang, id: `publication-01-reve.${lang}`, visuel: "photo-reve", kicker: fr ? "Le lancement" : "The launch", titre: titre2(c1, c2) }),
    postPaysage({ lang, id: `publication-02-un-compte.${lang}`, visuel: "huit", titre: titre2(fr ? "Un compte." : "One account.", fr ? "Tous vos outils." : "All your tools."), sous: fr ? "Huit outils, des crédits, un seul accès." : "Eight tools, credits, one access." }),
    postPaysage({ lang, id: `publication-03-quebec.${lang}`, visuel: "photo-quebec", titre: esc(TXT.quebec[lang]), sous: fr ? "Chez vous ou hébergée au Québec." : "On your premises or hosted in Québec." }),
    postPaysage({ lang, id: `publication-04-workstudio.${lang}`, visuel: "workstudio", kicker: outil("workstudio").nom, titre: lignes(outil("workstudio").titre[lang]), sous: outil("workstudio").sous[lang] }),
    postPaysage({ lang, id: `publication-05-controle.${lang}`, visuel: "photo-phare", kicker: outil("privacy").nom, titre: lignes(outil("privacy").titre[lang]), sous: outil("privacy").sous[lang] }),
    postPaysage({ lang, id: `publication-06-diagnostic.${lang}`, visuel: "code", titre: titre2(fr ? "Parlons de" : "Let’s talk about", fr ? "votre projet." : "your project."), sous: fr ? "Sans engagement." : "No commitment.", cta: TXT.diag[lang] }),
  ];
}

/** Carrousel PDF : huit pages 1080×1350, pensé pour la lecture en défilement (un message par page). */
export function carrouselPages(lang) {
  const w = 1080, h = 1350, m = 80, fr = lang === "fr", N = 8;
  const [c1, c2] = split(TXT.campagne[lang]);
  const pg = (i) => `<div style="position:absolute;left:${m}px;bottom:${m * 0.8}px;display:flex;gap:10px">${Array.from({ length: N }, (_, j) => `<i style="display:block;width:${j === i ? 44 : 14}px;height:14px;background:${j === i ? C.or : "rgba(245,244,239,.28)"}"></i>`).join("")}</div>`;
  const head = logo({ type: "complet", ton: "blanc", h: 40, x: m, y: m });
  const titreBloc = (t, s, { bottom = 190, size = 112 } = {}) => `<div style="position:absolute;left:${m}px;right:${m}px;bottom:${bottom}px;display:flex;flex-direction:column;gap:30px"><div class="aff" data-fit style="font-size:${size}px;max-height:${Math.round(size * 3.3)}px;overflow:hidden">${t}</div>${s ? `<div class="txt" data-fit style="font-size:34px;color:${C.gris};max-height:150px;overflow:hidden;max-width:880px">${esc(s)}</div>` : ""}</div>`;
  const pages = [];
  pages.push(fondPhoto({ w, h, nom: "aurore-foret", pos: "60% 40%", voiles: ["bas"], mos: { x: w * .55, y: 160, w: w * .45, h: 520, cell: 26, seed: 331, toward: "right", fade: 1, opacity: .9 } }) + head + titreBloc(titre2(c1, c2), TXT.quebec[lang], { size: 128 }) + pg(0));
  pages.push(fondMosaique({ w, h, mos: { x: w * 0.42, y: 0, w: w * 0.58, h: 168, cell: 28, seed: 332, toward: "right", fade: 1, opacity: .85 } }) + head + `<div style="position:absolute;left:${m}px;right:${m}px;top:200px"><div class="aff" style="font-size:104px">${titre2(fr ? "Un compte." : "One account.", fr ? "Tous les outils." : "Every tool.")}</div></div>` + grilleOutils({ x: m, y: 470, w: w - 2 * m, h: 700, cols: 2, k: 1, lang, glyph: 76, horizontal: true, label: 30 }) + pg(1));
  pages.push(fondPhoto({ w, h, nom: "salle-calcul", pos: "50% 50%", voiles: ["bas"] }) + head + titreBloc(titre2(fr ? "Vos données" : "Your data", fr ? "restent les vôtres." : "stays yours."), fr ? "Chez vous ou au Québec. Jamais utilisées pour entraîner un modèle." : "With you or in Québec. Never used to train a model.") + pg(2));
  pages.push(fondPhoto({ w, h, nom: "phare", pos: "50% 50%", voiles: ["bas"] }) + head + `<div style="position:absolute;left:${m}px;top:200px">${glyphe("privacy", { size: 180 })}</div>` + titreBloc(esc(outil("privacy").titre[lang]), outil("privacy").sous[lang]) + pg(3));
  pages.push(fondMosaique({ w, h, mos: { x: w * .3, y: 0, w: w * .7, h: h * .5, cell: 30, seed: 335, toward: "right", fade: 1 } }) + head + `<div style="position:absolute;left:${m}px;top:200px">${glyphe("workstudio", { size: 180 })}</div>` + titreBloc(titre2(fr ? "Une personne approuve" : "A person approves", fr ? "avant que ça parte." : "before it goes out."), fr ? "Par défaut, une action d’un agent qui écrit ou supprime attend l’accord d’une personne." : "By default, an agent action that writes or deletes waits for a person’s approval.", { size: 100 }) + pg(4));
  {
    const box = (x, tt, d) => `<div style="position:absolute;left:${x}px;top:420px;width:${(w - 2 * m - 40) / 2}px;height:520px;border:1px solid rgba(245,244,239,.22);padding:40px;display:flex;flex-direction:column;justify-content:flex-start;gap:90px"><div class="lib" style="font-size:24px;color:${C.orTxt}">${esc(tt[0])}</div><div><div class="aff" style="font-size:56px;margin-bottom:22px">${esc(tt[1])}</div><div class="txt" style="font-size:28px;color:${C.gris}">${esc(d)}</div></div></div>`;
    pages.push(fondMosaique({ w, h, mos: { x: w * 0.42, y: 0, w: w * 0.58, h: 168, cell: 28, seed: 336, toward: "right", fade: 1, opacity: .85 } }) + head + `<div style="position:absolute;left:${m}px;right:${m}px;top:200px"><div class="aff" style="font-size:96px">${titre2(fr ? "Deux façons de" : "Two ways to", fr ? "garder le contrôle." : "stay in control.")}</div></div>`
      + box(m, fr ? ["Sur place", "Chez vous"] : ["On premises", "With you"], fr ? "Vos données restent sur votre serveur." : "Your data stays on your server.")
      + box(m + (w - 2 * m - 40) / 2 + 40, fr ? ["Hébergé", "Au Québec"] : ["Hosted", "In Québec"], fr ? "Dans l’infrastructure de Nexora AI, située au Québec, sauvegardes comprises." : "In Nexora AI’s infrastructure, located in Québec, backups included.") + pg(5));
  }
  {
    const etapes = fr ? ["Comprendre", "Intégrer", "Vérifier", "Former", "Exploiter et améliorer"] : ["Understand", "Integrate", "Verify", "Train", "Operate and improve"];
    const rows = etapes.map((e, i) => `<div style="display:flex;align-items:center;gap:34px;border-top:1px solid rgba(245,244,239,.2);height:118px"><i style="display:block;width:26px;height:26px;background:${BARRES[Math.min(i, 3)]}"></i><div class="aff" style="font-size:56px">${esc(e)}</div></div>`).join("");
    pages.push(fondMosaique({ w, h, mos: { x: w * 0.42, y: 0, w: w * 0.58, h: 168, cell: 28, seed: 337, toward: "right", fade: 1, opacity: .85 } }) + head + `<div style="position:absolute;left:${m}px;right:${m}px;top:200px"><div class="aff" style="font-size:96px">${titre2(fr ? "Une méthode" : "A method", fr ? "en cinq temps." : "in five steps.")}</div></div><div style="position:absolute;left:${m}px;right:${m}px;top:520px">${rows}</div>` + pg(6));
  }
  pages.push(fondPhoto({ w, h, nom: "aurore-lac", pos: "50% 50%", voiles: ["bas"], mos: null }) + head + `<div style="position:absolute;left:${m}px;right:${m}px;bottom:190px;display:flex;flex-direction:column;gap:34px"><div class="aff" style="font-size:112px">${titre2(c1, c2)}</div><div>${bouton(TXT.diag[lang], { k: 1.25 })}</div></div>` + pg(7));
  return pages.map((body, i) => F.piece({ id: `carrousel-page-${i + 1}-sur-${N}.${lang}`, sousDossier: `${D}/carrousel`, w, h, lang, body }));
}
export const pdfsLinkedin = () => LANGS.map((lang) => ({ pieces: carrouselPages(lang), out: path.join(F.finalDir, D, `carrousel-nexora-ai.${lang}.pdf`), w: 1080, h: 1350 }));

export function toutLinkedin() {
  const out = [];
  for (const lang of LANGS) out.push(...bannieres(lang), ...publications(lang), partage(lang, { id: "image-partage", sousDossier: D, w: 1200, h: 627 }), ...carrouselPages(lang));
  return out;
}
