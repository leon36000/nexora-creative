// Instagram : profil, publications 1080×1350, carrousel de 7 images, 8 couvertures de stories à la une, modèle de Reels.
import path from "node:path";
import { C, TXT, OUTILS, outil, mosaique, grille, regle, cadre, grain, voile, logo, glyphe, pastille, bouton, esc, BARRES } from "./moteur/marque.mjs";
import { fondPhoto, fondMosaique, titre2, grilleOutils, lignes } from "./moteur/compo.mjs";
import { postManifeste, PLAN } from "./moteur/modeles.mjs";
import { F, profil } from "./fb.mjs";
const LANGS = ["fr", "en"];
const D = "instagram";
const split = (s) => [s.split(". ")[0] + ".", s.split(". ").slice(1).join(". ")];

export function publications(lang) {
  const [c1, c2] = split(TXT.campagne[lang]);
  const defs = [
    { id: "01-reve", p: { lang, ligne1: c1, ligne2: c2, plan: { nom: "aurore-lac", pos: "50% 45%", voiles: ["bas"] }, kicker: lang === "fr" ? "Le lancement" : "The launch" } },
    { id: "02-quebec", p: { lang, ligne1: lang === "fr" ? "IA souveraine" : "Sovereign AI,", ligne2: lang === "fr" ? "au Québec." : "made in Québec.", plan: { nom: "fleuve-aube", pos: "50% 50%", voiles: ["bas"] } } },
    { id: "03-un-compte", p: { lang, ligne1: lang === "fr" ? "Un compte." : "One account.", ligne2: lang === "fr" ? "Tous les outils." : "Every tool.", sous: lang === "fr" ? "Des crédits, huit outils, un seul accès." : "Credits, eight tools, one access." } },
    { id: "04-donnees", p: { lang, ligne1: lang === "fr" ? "Vos données" : "Your data", ligne2: lang === "fr" ? "restent les vôtres." : "stays yours.", sous: lang === "fr" ? "Chez vous ou au Québec. Jamais utilisées pour entraîner un modèle." : "With you or in Québec. Never used to train a model.", plan: { nom: "salle-calcul", pos: "50% 50%", voiles: ["bas"] } } },
    { id: "05-pixels", p: { lang, ligne1: lang === "fr" ? "Des pixels" : "Pixels", ligne2: lang === "fr" ? "qui deviennent des mondes." : "that become worlds.", plan: { nom: "carres-flottants", pos: "65% 50%", voiles: ["bas"] } } },
    { id: "06-diagnostic", p: { lang, ligne1: lang === "fr" ? "Parlons de" : "Let’s talk about", ligne2: lang === "fr" ? "votre projet." : "your project.", sous: lang === "fr" ? "Planifier un diagnostic, sans engagement." : "Book a diagnostic, no commitment." } },
  ];
  return defs.map(({ id, p }) => F.piece({ id: `publication-${id}.${lang}`, sousDossier: `${D}/publications`, w: 1080, h: 1350, lang, body: postManifeste(p) }));
}

/** Carrousel de 7 images : accroche, quatre doubles d'outils (huit outils), le compte, l'appel à l'action. */
export function carrousel(lang) {
  const w = 1080, h = 1350, m = 80, N = 7;
  const progress = (i) => `<div style="position:absolute;left:${m}px;bottom:${m * 0.8}px;display:flex;gap:10px;align-items:center">${Array.from({ length: N }, (_, j) => `<i style="display:block;width:${j === i ? 44 : 14}px;height:14px;background:${j === i ? C.or : "rgba(245,244,239,.28)"}"></i>`).join("")}</div>
    ${i < N - 1 ? `<div class="lib" style="position:absolute;right:${m}px;bottom:${m * 0.8 - 8}px;font-size:26px;color:${C.gris};display:flex;align-items:center;gap:14px">${lang === "fr" ? "Glissez" : "Swipe"}<svg width="26" height="26" viewBox="0 0 20 20" shape-rendering="crispEdges"><path d="M2 9h12V7h2v2h2v2h-2v2h-2v-2H2zM12 5h2v2h-2zm0 8h2v2h-2z" fill="${C.orTxt}"/></svg></div>` : ""}`;
  const head = `${logo({ type: "complet", ton: "blanc", h: 40, x: m, y: m })}`;
  const out = [];
  // 1 : accroche
  {
    const fond = fondPhoto({ w, h, nom: "aurore-foret", pos: "60% 40%", voiles: ["bas"], mos: { x: w * 0.55, y: 160, w: w * 0.45, h: 520, cell: 26, seed: 33, toward: "right", fade: 1, opacity: .9 } });
    const t = `<div style="position:absolute;left:${m}px;bottom:${190}px;width:${w - 2 * m}px;display:flex;flex-direction:column;gap:28px"><div class="lib" style="font-size:30px;color:${C.orTxt}">${lang === "fr" ? "Huit outils" : "Eight tools"}</div><div class="aff" data-fit style="font-size:128px;max-height:420px;overflow:hidden">${lang === "fr" ? "Un compte.<br><span style=\"color:" + C.orTxt + "\">Tous vos outils.</span>" : "One account.<br><span style=\"color:" + C.orTxt + "\">All your tools.</span>"}</div></div>`;
    out.push(fond + head + t + progress(0));
  }
  // 2 à 5 : deux outils par image
  const paires = [["workstudio", "code"], ["rag", "bot"], ["creative", "webpilot"], ["privacy", "vps"]];
  paires.forEach((pr, i) => {
    const fond = fondMosaique({ w, h, mos: [{ x: w * 0.42, y: 0, w: w * 0.58, h: 168, cell: 28, seed: 70 + i, toward: "right", fade: 1, opacity: .85 }] });
    const bloc = (id, y) => { const o = outil(id); return `<div style="position:absolute;left:${m}px;right:${m}px;top:${y}px;height:490px;border-top:1px solid rgba(245,244,239,.2);padding-top:40px;display:flex;flex-direction:column;gap:26px">
      <div style="display:flex;align-items:center;gap:28px">${glyphe(id, { size: 112 })}<div style="display:flex;flex-direction:column;gap:12px"><div class="lib" style="font-size:26px;color:${C.orTxt}">${esc(o.etat[lang])}</div><div class="lib" style="font-size:30px;color:${C.clair}">${esc(o.nom)}</div></div></div>
      <div class="aff" data-fit style="font-size:82px;max-height:176px;overflow:hidden;color:${C.clair}">${lignes(o.titre[lang])}</div>
      <div class="txt" data-fit style="font-size:36px;color:${C.gris};max-height:112px;overflow:hidden">${esc(o.sous[lang])}</div></div>`; };
    out.push(fond + head + bloc(pr[0], 180) + bloc(pr[1], 180 + 510) + progress(i + 1));
  });
  // 6 : le compte
  {
    const fond = fondMosaique({ w, h, mos: [{ x: w * 0.42, y: 0, w: w * 0.58, h: 168, cell: 28, seed: 90, toward: "right", fade: 1, opacity: .85 }] });
    const t = `<div style="position:absolute;left:${m}px;right:${m}px;top:200px;display:flex;flex-direction:column;gap:30px"><div class="aff" data-fit style="font-size:104px;max-height:300px;overflow:hidden">${lang === "fr" ? "Un seul accès.<br><span style=\"color:" + C.orTxt + "\">Des crédits.</span>" : "One access.<br><span style=\"color:" + C.orTxt + "\">Credits.</span>"}</div></div>`;
    out.push(fond + head + t + grilleOutils({ x: m, y: 470, w: w - 2 * m, h: 700, cols: 2, k: 1, lang, glyph: 76, horizontal: true, label: 30 }) + progress(5));
  }
  // 7 : appel à l'action
  {
    const [a, b] = lang === "fr" ? ["Rêvez grand.", "Gardez le contrôle."] : ["Dream big.", "Stay in control."];
    const fond = fondPhoto({ w, h, nom: "aurore-lac", pos: "50% 50%", voiles: ["bas"], mos: null });
    const t = `<div style="position:absolute;left:${m}px;right:${m}px;bottom:190px;display:flex;flex-direction:column;gap:34px"><div class="aff" data-fit style="font-size:112px;max-height:260px;overflow:hidden">${titre2(a, b)}</div><div>${bouton(TXT.diag[lang], { k: 1.25 })}</div></div>`;
    out.push(fond + head + t + progress(6));
  }
  return out.map((body, i) => F.piece({ id: `carrousel-${i + 1}-sur-${N}.${lang}`, sousDossier: `${D}/carrousel`, w, h, lang, body }));
}

/** Couvertures de stories à la une : 1080×1920, cadre de filets, un glyphe au centre (dans le disque de découpe). */
export function aLaUne() {
  const w = 1080, h = 1920;
  return OUTILS.map((o, i) => {
    const body = `<div style="position:absolute;inset:0;background:${C.noir}"></div>${voile("radial-gradient(60% 40% at 50% 50%,rgba(255,90,31,.16),transparent 70%)")}${grille({ size: 60, opacity: 0.06 })}
      ${cadre({ x: 150, y: 600, w: 780, h: 720, k: 1.2 })}
      <div style="position:absolute;left:${(w - 340) / 2}px;top:${h / 2 - 190}px">${glyphe(o.id, { size: 340 })}</div>
      <div class="lib" style="position:absolute;left:0;right:0;top:${h / 2 + 230}px;text-align:center;font-size:30px;color:${C.clair}">${esc(o.court)}</div>
      ${regle({ w, k: 1.5, side: "bottom", y: 0 })}${grain(0.06)}`;
    return F.piece({ id: `a-la-une-${String(i + 1).padStart(2, "0")}-${o.id}`, sousDossier: `${D}/a-la-une`, w, h, body, title: `À la une : ${o.nom}`, fit: false });
  });
}

/** Modèle de Reels : cadre de filets en PNG transparent à superposer à la vidéo, et version avec les zones de sécurité. */
export function reels(lang) {
  const w = 1080, h = 1920;
  // zones masquées par l'interface (haut 250, bas 480, droite 120) : tout élément essentiel reste dans la zone sûre
  const cadreR = cadre({ x: 40, y: 250, w: w - 160, h: h - 250 - 480, k: 1.2, color: "rgba(245,244,239,.55)" });
  const marque = `<div style="position:absolute;left:84px;top:296px">${logo({ type: "symbole", ton: "blanc", h: 46 })}</div>
    <div class="lib" style="position:absolute;left:156px;top:304px;font-size:22px;color:${C.clair}">${esc(TXT.quebecCourt[lang])}</div>
    <div style="position:absolute;left:40px;width:${w - 160}px;top:${h - 480 - 16}px;height:16px;display:flex">${BARRES.map((c) => `<i style="flex:1;background:${c}"></i>`).join("")}</div>`;
  const guides = `<div style="position:absolute;left:0;top:0;width:${w}px;height:250px;background:repeating-linear-gradient(45deg,rgba(255,90,31,.28) 0 14px,rgba(255,90,31,.12) 14px 28px)"></div>
    <div style="position:absolute;left:0;top:${h - 480}px;width:${w}px;height:480px;background:repeating-linear-gradient(45deg,rgba(255,90,31,.28) 0 14px,rgba(255,90,31,.12) 14px 28px)"></div>
    <div style="position:absolute;left:${w - 120}px;top:250px;width:120px;height:${h - 730}px;background:repeating-linear-gradient(45deg,rgba(255,90,31,.28) 0 14px,rgba(255,90,31,.12) 14px 28px)"></div>
    <div class="lib" style="position:absolute;left:40px;top:96px;font-size:28px;color:${C.clair}">${lang === "fr" ? "Zone masquée : profil et titre (250 px)" : "Hidden: profile and title (250 px)"}</div>
    <div class="lib" style="position:absolute;left:40px;top:${h - 300}px;font-size:28px;color:${C.clair}">${lang === "fr" ? "Zone masquée : légende et boutons (480 px)" : "Hidden: caption and buttons (480 px)"}</div>
    <div class="lib" style="position:absolute;left:${w / 2 - 300}px;top:${h / 2 - 20}px;width:600px;text-align:center;font-size:30px;color:${C.clair}">${lang === "fr" ? "Zone sûre : tout l’essentiel ici" : "Safe zone: keep everything here"}</div>`;
  return [
    F.piece({ id: `reels-cadre.${lang}`, sousDossier: `${D}/reels`, w, h, lang, body: cadreR + marque, transparent: true, fit: false, title: "Reels : cadre transparent" }),
    F.piece({ id: `reels-guides.${lang}`, sousDossier: `${D}/reels`, w, h, lang, body: `<div style="position:absolute;inset:0;background:${C.surface}"></div>${grille({ size: 60, opacity: .06 })}${guides}${cadreR}${marque}`, fit: false, title: "Reels : zones de sécurité" }),
  ];
}

export function toutInstagram() {
  const out = [profil("profil", D), ...aLaUne()];
  for (const lang of LANGS) out.push(...publications(lang), ...carrousel(lang), ...reels(lang));
  return out;
}
