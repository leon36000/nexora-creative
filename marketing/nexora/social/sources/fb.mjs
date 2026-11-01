// Facebook : profil, couvertures (3 variantes), événement, partage de lien, groupe, 8 publications, 5 stories, arrière-plans.
import path from "node:path";
import { famille, C, TXT, OUTILS, outil, mosaique, grille, regle, bande, cadre, grain, photo, voile, logo, glyphe, pastille, esc, BARRES } from "./moteur/marque.mjs";
import { fondPhoto, fondMosaique, titre2, grilleOutils } from "./moteur/compo.mjs";
import { postOutil, postManifeste, story, PLAN, PLAN_V } from "./moteur/modeles.mjs";

export const F = famille({ dossier: path.resolve(import.meta.dirname, "..") });
const LANGS = ["fr", "en"];
const col = (left, w, h, inner, align = "center", top = 0) => `<div style="position:absolute;left:${left}px;top:${top}px;width:${w}px;height:${h}px;display:flex;flex-direction:column;justify-content:center;align-items:${align === "center" ? "center" : "flex-start"};text-align:${align};gap:30px">${inner}</div>`;

/** Profil carré : symbole officiel centré dans le disque de découpe (zone de protection respectée). */
export function profil(id = "profil", dossier = "facebook", size = 1080) {
  const s = size * 0.42, x = (size - s) / 2;
  const body = `<div style="position:absolute;inset:0;background:${C.noir}"></div>${voile("radial-gradient(60% 60% at 50% 50%,rgba(255,90,31,.10),transparent 70%)")}${logo({ type: "symbole", ton: "sombre", w: s, x, y: x })}${grain(0.06)}`;
  return F.piece({ id, sousDossier: dossier, w: size, h: size, body, title: "Nexora AI : photo de profil" });
}

/** Couvertures de page 1640×624 : zone sûre mobile = les 1000 px du centre (x de 320 à 1320). */
export function couverture(variant, lang, { w = 1640, h = 624, sousDossier = "facebook", prefix = "couverture", k = 1, zone } = {}) {
  const z = zone ?? { x: (w - 1000) / 2, w: 1000 };
  let fond = "", inner = "";
  if (variant === "aurore") {
    fond = fondPhoto({ w, h, nom: "aurore-foret", pos: "100% 22%", scale: 1.45, voiles: ["linear-gradient(90deg,rgba(10,10,14,.05) 0%,rgba(10,10,14,.35) 30%,rgba(10,10,14,.78) 52%,rgba(10,10,14,.86) 100%)", "vignette"], grainOp: 0.1 });
    inner = col(z.x, z.w, h, `${logo({ type: "complet", ton: "blanc", h: 46 * k, style: "position:static" })}
      <div class="aff" data-fit style="font-size:${88 * k}px;max-height:${200 * k}px;overflow:hidden">${titre2(TXT.campagne[lang].split(". ")[0] + ".", TXT.campagne[lang].split(". ")[1])}</div>
      <div class="lib" style="font-size:${20 * k}px;color:${C.gris}">${esc(TXT.quebecCourt[lang])}</div>`);
  } else if (variant === "nuit") {
    fond = fondPhoto({ w, h, nom: "ville-crepuscule", pos: "50% 62%", voiles: ["gauche"], grainOp: 0.1,
      mos: { x: w - 560 * k, y: 0, w: 560 * k, h: h, cell: 24 * k, seed: 41, toward: "right", fade: 1, opacity: 0.85 } });
    inner = col(z.x - 10, z.w, h, `${logo({ type: "complet", ton: "blanc", h: 38 * k, style: "position:static" })}
      <div class="aff" data-fit style="font-size:${78 * k}px;max-height:${190 * k}px;overflow:hidden;max-width:${700 * k}px">${esc(TXT.signature[lang].split(". ")[0] + ".")}<br><span style="color:${C.orTxt}">${esc(TXT.signature[lang].split(". ")[1])}</span></div>
      <div class="lib" style="font-size:${19 * k}px;color:${C.gris}">${esc(TXT.quebec[lang])}</div>`, "left");
  } else {
    fond = fondMosaique({ w, h, k, grid: true, ruler: true, mos: [
      { x: 0, y: 0, w: 330 * k, h, cell: 26 * k, seed: 61, toward: "left", fade: 1 },
      { x: w - 330 * k, y: 0, w: 330 * k, h, cell: 26 * k, seed: 62, toward: "right", fade: 1 },
    ] });
    inner = col(z.x, z.w, h, `<div class="lib" style="font-size:${20 * k}px;color:${C.orTxt}">${esc(TXT.famille[lang])}</div>
      <div class="aff" data-fit style="font-size:${104 * k}px;max-height:${230 * k}px;overflow:hidden">${esc(TXT.campagne[lang].split(". ")[0] + ".")}<br>${esc(TXT.campagne[lang].split(". ")[1])}</div>`);
  }
  return F.piece({ id: `${prefix}-${variant}.${lang}`, sousDossier, w, h, lang, body: fond + inner, title: `Nexora AI : couverture ${variant} (${lang})` });
}

export function evenement(lang) {
  const w = 1920, h = 1005, k = 1.2;
  const fond = fondPhoto({ w, h, nom: "aurore-lac", pos: "50% 55%", voiles: ["centre", "vignette"],
    mos: [{ x: 0, y: h - 300, w: w, h: 300, cell: 30, seed: 77, toward: "bottom", fade: 1, opacity: 0.7 }] });
  const inner = col(0, w, h, `${logo({ type: "complet", ton: "blanc", h: 54, style: "position:static" })}
    <div class="lib" style="font-size:24px;color:${C.orTxt};margin-top:14px">${lang === "fr" ? "Le lancement" : "The launch"}</div>
    <div class="aff" data-fit style="font-size:128px;max-height:300px;overflow:hidden;text-align:center">${titre2(TXT.campagne[lang].split(". ")[0] + ".", TXT.campagne[lang].split(". ")[1])}</div>
    <div class="txt" style="font-size:34px;color:${C.gris}">${esc(TXT.quebec[lang])}</div>`);
  return F.piece({ id: `evenement.${lang}`, sousDossier: "facebook", w, h, lang, body: fond + inner });
}

export function partage(lang, { id = "partage-lien", sousDossier = "facebook", w = 1200, h = 630 } = {}) {
  const k = w / 1200;
  const fond = fondMosaique({ w, h, k, grid: true, mos: [{ x: w * 0.52, y: 0, w: w * 0.48, h, cell: 28 * k, seed: 91, toward: "right", fade: 1 }] }) + regle({ w, k, side: "bottom" });
  const inner = `${logo({ type: "complet", ton: "sombre", h: 44 * k, x: 72 * k, y: 64 * k })}
  <div style="position:absolute;left:${72 * k}px;bottom:${96 * k}px;width:${w * 0.54}px;display:flex;flex-direction:column;gap:${22 * k}px">
    <div class="lib" style="font-size:${17 * k}px;color:${C.orTxt}">${esc(TXT.quebecCourt[lang])}</div>
    <div class="aff" data-fit style="font-size:${68 * k}px;max-height:${250 * k}px;overflow:hidden">${esc(TXT.signature[lang].split(". ")[0] + ".")}<br><span style="color:${C.orTxt}">${esc(TXT.signature[lang].split(". ")[1])}</span></div>
  </div>`;
  return F.piece({ id: `${id}.${lang}`, sousDossier, w, h, lang, body: fond + inner });
}

export function groupe(lang) {
  const w = 1640, h = 856;
  const fond = fondPhoto({ w, h, nom: "cabane-neige", pos: "50% 58%", voiles: ["centre", "vignette"], grainOp: 0.1,
    mos: [{ x: 0, y: h - 260, w: 360, h: 260, cell: 26, seed: 17, toward: "left", fade: 1, opacity: .8 }, { x: w - 360, y: h - 260, w: 360, h: 260, cell: 26, seed: 18, toward: "right", fade: 1, opacity: .8 }] });
  const inner = col(320, 1000, h, `${logo({ type: "complet", ton: "blanc", h: 46, style: "position:static" })}
    <div class="lib" style="font-size:21px;color:${C.orTxt};margin-top:10px">${lang === "fr" ? "Le groupe" : "The group"}</div>
    <div class="aff" data-fit style="font-size:100px;max-height:240px;overflow:hidden">${lang === "fr" ? "Ce que vous bâtissez,<br><span style=\"color:" + C.orTxt + "\">parlons-en.</span>" : "What you are building,<br><span style=\"color:" + C.orTxt + "\">let’s talk.</span>"}</div>`);
  return F.piece({ id: `couverture-groupe.${lang}`, sousDossier: "facebook", w, h, lang, body: fond + inner });
}

export function posts(lang) {
  return OUTILS.map((o, i) => F.piece({ id: `publication-${String(i + 1).padStart(2, "0")}-${o.id}.${lang}`, sousDossier: "facebook/publications", w: 1080, h: 1350, lang, body: postOutil(o, lang), title: `${o.nom} : ${o.titre[lang]}` }));
}

export function stories(lang) {
  const [a, b] = [TXT.campagne[lang].split(". ")[0] + ".", TXT.campagne[lang].split(". ")[1]];
  const list = [
    { id: "01-reve", s: { lang, plan: { nom: "aurore-vertical", pos: "50% 40%", voiles: ["bas2"] }, titre: titre2(a, b), kicker: lang === "fr" ? "Le lancement" : "The launch" } },
    { id: "02-un-compte", s: { lang, mos: [{ x: 480, y: 0, w: 600, h: 380, cell: 30, seed: 5, toward: "right", fade: 1, opacity: .8 }], titre: titre2(lang === "fr" ? "Un compte." : "One account.", lang === "fr" ? "Tous vos outils." : "All your tools."), sous: lang === "fr" ? "Huit outils, un seul accès." : "Eight tools, one access.", grilleHuit: true } },
    { id: "03-quebec", s: { lang, plan: { nom: "fleuve-vertical", pos: "50% 50%", voiles: ["bas2"] }, titre: esc(TXT.quebec[lang]), sous: lang === "fr" ? "Vos données restent chez vous ou au Québec. Jamais utilisées pour entraîner un modèle." : "Your data stays with you or in Québec. Never used to train a model." } },
    { id: "04-controle", s: { lang, plan: { nom: "phare-vertical", pos: "50% 45%", voiles: ["bas2"] }, pastilleOutil: outil("privacy"), titre: esc(outil("privacy").titre[lang]), sous: outil("privacy").sous[lang] } },
    { id: "05-diagnostic", s: { lang, mos: [{ x: 0, y: 380, w: 1080, h: 700, cell: 30, seed: 9, toward: "right", fade: 1, opacity: .7 }], titre: titre2(lang === "fr" ? "Parlons de votre projet." : "Let’s talk about your project.", ""), sous: lang === "fr" ? "Sans engagement." : "No commitment.", cta: TXT.diag[lang] } },
  ];
  return list.map(({ id, s }) => F.piece({ id: `story-${id}.${lang}`, sousDossier: "facebook/stories", w: 1080, h: 1920, lang, body: story(s) }));
}

export function arrieres() {
  const w = 1080, h = 1920;
  return [
    F.piece({ id: "fond-aurore", sousDossier: "facebook/arrieres-plans", w, h, body: fondPhoto({ w, h, nom: "aurore-vertical", pos: "50% 50%", voiles: ["aucun"] }), fit: false }),
    F.piece({ id: "fond-mosaique", sousDossier: "facebook/arrieres-plans", w, h, body: fondMosaique({ w, h, mos: [{ x: 0, y: h * 0.25, w, h: h * 0.75, cell: 36, seed: 3, toward: "bottom", fade: 1 }] }), fit: false }),
    F.piece({ id: "fond-nuit", sousDossier: "facebook/arrieres-plans", w, h, body: fondPhoto({ w, h, nom: "ville-vertical", pos: "50% 50%", voiles: ["aucun"] }), fit: false }),
    F.piece({ id: "fond-fleuve-1920", sousDossier: "facebook/arrieres-plans", w: 1920, h: 1080, body: fondPhoto({ w: 1920, h: 1080, nom: "fleuve-aube", pos: "50% 50%", voiles: ["aucun"] }), fit: false }),
  ];
}

export function toutFacebook() {
  const out = [profil()];
  for (const lang of LANGS) {
    for (const v of ["aurore", "nuit", "mosaique"]) out.push(couverture(v, lang));
    out.push(evenement(lang), partage(lang), groupe(lang), ...posts(lang), ...stories(lang));
  }
  out.push(...arrieres());
  return out;
}
