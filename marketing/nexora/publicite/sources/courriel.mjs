// Courriel : en-tête 600×200 et 1200×400, bouton, pied, et trois modèles HTML en tableaux (infolettre, lancement, invitation).
import fs from "node:fs";
import path from "node:path";
import { famille, C, TXT, OUTILS, outil, mosaique, grille, regle, grain, voile, logo, glyphe, bouton, esc, BARRES, coordonnees } from "../../social/sources/moteur/marque.mjs";
import { fondPhoto, fondMosaique, titre2 } from "../../social/sources/moteur/compo.mjs";
const RAC = path.resolve(import.meta.dirname, "..");
const P = famille({ dossier: RAC });
const DIR = "courriel";
const split = (s) => [s.split(". ")[0] + ".", s.split(". ").slice(1).join(". ")];

function entete(lang, w, h) {
  const k = w / 600;
  const [a, b] = split(TXT.campagne[lang]);
  const body = fondPhoto({ w, h, nom: "aurore-lac", pos: "50% 55%", voiles: ["gauche"], grainOp: .08, mos: { x: w * .66, y: 0, w: w * .34, h, cell: 14 * k, seed: 901, toward: "right", fade: 1, opacity: .9 } })
    + logo({ type: "complet", ton: "blanc", h: 20 * k, x: 28 * k, y: 26 * k })
    + `<div style="position:absolute;left:${28 * k}px;bottom:${28 * k}px;width:${w * .6}px"><div class="aff" data-fit style="font-size:${34 * k}px;max-height:${80 * k}px;overflow:hidden">${titre2(a, b)}</div></div>`;
  return P.piece({ id: `entete-${w}x${h}.${lang}`, sousDossier: `${DIR}/images`, w, h, lang, body });
}
function boutonImg(lang) {
  const w = 520, h = 112;
  return P.piece({ id: `bouton-diagnostic.${lang}`, sousDossier: `${DIR}/images`, w, h, lang, fit: false, title: TXT.diag[lang],
    body: `<div style="position:absolute;inset:0;background:${C.or};border-radius:12px;display:flex;align-items:center;justify-content:center;gap:22px;color:${C.noir};font:600 40px/1 Inter,sans-serif">${esc(TXT.diag[lang])}<svg width="36" height="36" viewBox="0 0 20 20" shape-rendering="crispEdges"><path d="M2 9h12V7h2v2h2v2h-2v2h-2v-2H2zM12 5h2v2h-2zm0 8h2v2h-2z" fill="${C.noir}"/></svg></div>` });
}
function pied(lang) {
  const w = 1200, h = 200;
  return P.piece({ id: `pied.${lang}`, sousDossier: `${DIR}/images`, w, h, lang, fit: false,
    body: `<div style="position:absolute;inset:0;background:${C.noir}"></div>${voile("radial-gradient(60% 120% at 100% 0%,rgba(255,90,31,.14),transparent 70%)")}${logo({ type: "complet", ton: "sombre", h: 44, x: 56, y: 44 })}
    <div class="lib" style="position:absolute;left:56px;top:124px;font-size:24px;color:${C.gris}">${esc(TXT.quebec[lang])}</div>
    <div style="position:absolute;left:0;right:0;bottom:0;height:16px;display:flex">${BARRES.map((c) => `<i style="flex:1;background:${c}"></i>`).join("")}</div>` });
}
export function toutCourriel() {
  return ["fr", "en"].flatMap((l) => [entete(l, 600, 200), entete(l, 1200, 400), boutonImg(l), pied(l)]);
}

/* ---------- modèles HTML (tableaux, styles en ligne, polices système, bouton robuste pour Outlook) ---------- */
const T = {
  fr: {
    lancement: { sujet: "Nexora AI : le lancement", pre: "Rêvez grand. Gardez le contrôle.", titre: "Rêvez grand. Gardez le contrôle.",
      p1: "Nexora AI conçoit, installe et accompagne des systèmes d’IA pour votre entreprise, chez vous ou hébergés au Québec. Vos données ne servent jamais à entraîner un modèle.",
      p2: "Un compte, des crédits, huit outils. L’état de chacun est écrit en toutes lettres : aucun n’est promis d’avance.",
      cta: "Planifier un diagnostic", cta2: "Voir les solutions" },
    infolettre: { sujet: "Nexora AI : les nouvelles du mois", pre: "Ce que nous avons préparé pour vous.", titre: "Les nouvelles de Nexora AI",
      p1: "{{introduction}}", p2: "{{article_1_texte}}", cta: "Lire la suite", cta2: "Voir les solutions" },
    invitation: { sujet: "Vous êtes invité(e)", pre: "Rêvez grand. Gardez le contrôle.", titre: "Vous êtes invité(e).",
      p1: "Nous vous invitons à {{nom_evenement}}. Quand : {{date_evenement}}. Où : {{lieu_evenement}}.",
      p2: "Une occasion de voir comment l’IA peut travailler pour votre entreprise, sous votre contrôle.",
      cta: "Répondre à l’invitation", cta2: "Voir les solutions" },
    outils: "Les huit outils", etatTitre: "État", legal: "Vous recevez ce courriel parce que vous avez demandé à être informé(e) des nouvelles de Nexora AI.", desab: "Se désabonner", voir: "Voir dans le navigateur",
  },
  en: {
    lancement: { sujet: "Nexora AI: the launch", pre: "Dream big. Stay in control.", titre: "Dream big. Stay in control.",
      p1: "Nexora AI designs, installs and supports AI systems for your business, on your premises or hosted in Québec. Your data is never used to train a model.",
      p2: "One account, credits, eight tools. The status of each is spelled out: none is promised in advance.",
      cta: "Book a diagnostic", cta2: "See the solutions" },
    infolettre: { sujet: "Nexora AI: this month’s news", pre: "What we have prepared for you.", titre: "News from Nexora AI",
      p1: "{{introduction}}", p2: "{{article_1_texte}}", cta: "Read more", cta2: "See the solutions" },
    invitation: { sujet: "You are invited", pre: "Dream big. Stay in control.", titre: "You are invited.",
      p1: "We invite you to {{nom_evenement}}. When: {{date_evenement}}. Where: {{lieu_evenement}}.",
      p2: "A chance to see how AI can work for your business, under your control.",
      cta: "Reply to the invitation", cta2: "See the solutions" },
    outils: "The eight tools", etatTitre: "Status", legal: "You are receiving this email because you asked to hear news from Nexora AI.", desab: "Unsubscribe", voir: "View in browser",
  },
};
const FONT = `-apple-system,'Segoe UI','Helvetica Neue',Arial,sans-serif`;
const btn = (href, label, fill = "#FF5A1F", color = "#0A0A0E", border = "") =>
  `<!--[if mso]><v:roundrect xmlns:v="urn:schemas-microsoft-com:vml" href="${href}" style="height:48px;v-text-anchor:middle;width:260px;" arcsize="12%" stroke="f" fillcolor="${fill}"><w:anchorlock/><center style="color:${color};font-family:Arial,sans-serif;font-size:16px;font-weight:bold;">${esc(label)}</center></v:roundrect><![endif]-->
<!--[if !mso]><!--><a href="${href}" style="background:${fill};color:${color};${border}display:inline-block;font-family:${FONT};font-size:16px;font-weight:600;line-height:48px;text-align:center;text-decoration:none;padding:0 28px;border-radius:6px;-webkit-text-size-adjust:none;">${esc(label)}</a><!--<![endif]-->`;

function modele(type, lang) {
  const t = T[lang][type], g = T[lang];
  const rows = OUTILS.map((o) => `<tr><td style="padding:10px 0;border-top:1px solid #E4E2D9;font-family:${FONT};font-size:16px;color:#121218;font-weight:600">${esc(o.nom)}</td><td align="right" style="padding:10px 0;border-top:1px solid #E4E2D9;font-family:'Courier New',monospace;font-size:13px;color:#B53A0A;text-transform:uppercase;letter-spacing:.06em">${esc(o.etat[lang])}</td></tr>`).join("");
  const siteMarque = coordonnees.site, courriel = coordonnees.courriel_general, adresse = coordonnees.adresse;
  const showTools = type !== "invitation";
  return `<!doctype html>
<html lang="${lang}" xmlns="http://www.w3.org/1999/xhtml" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="x-apple-disable-message-reformatting"><meta name="color-scheme" content="light only">
<!--[if mso]><xml><o:OfficeDocumentSettings><o:AllowPNG/><o:PixelsPerInch>96</o:PixelsPerInch></o:OfficeDocumentSettings></xml><![endif]-->
<title>${esc(t.sujet)}</title>
<style>body{margin:0;padding:0;background:#F3F2EC}table{border-collapse:collapse}img{border:0;display:block;max-width:100%;height:auto}a{color:#B53A0A}@media (max-width:620px){.w{width:100%!important}.p{padding-left:20px!important;padding-right:20px!important}.h1{font-size:28px!important}}</style>
</head>
<body style="margin:0;padding:0;background:#F3F2EC">
<!-- Modèle « ${type} » (${lang}). Champs à remplacer : {{...}}. Images dans ./images (à héberger, chemins absolus à l’envoi). -->
<div style="display:none;max-height:0;overflow:hidden;opacity:0;color:#F3F2EC">${esc(t.pre)}&#847;&zwnj;&nbsp;&#847;&zwnj;&nbsp;&#847;&zwnj;&nbsp;</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F3F2EC"><tr><td align="center" style="padding:24px 12px">
<table role="presentation" class="w" width="600" cellpadding="0" cellspacing="0" style="width:600px;background:#FBFBF8">
<tr><td align="right" style="padding:0 0 10px;font-family:${FONT};font-size:12px;color:#54545F;background:#F3F2EC"><a href="{{lien_navigateur}}" style="color:#54545F">${esc(g.voir)}</a></td></tr>
<tr><td><a href="${siteMarque}"><img src="images/entete-1200x400.${lang}.png" width="600" height="200" alt="Nexora AI. ${esc(TXT.campagne[lang])}" style="width:100%;height:auto"></a></td></tr>
<tr><td class="p" style="padding:40px 40px 8px;font-family:${FONT}">
<h1 class="h1" style="margin:0 0 20px;font-family:'Helvetica Neue',${FONT};font-size:34px;line-height:1.1;letter-spacing:-.02em;font-weight:600;color:#0A0A0E">${esc(t.titre)}</h1>
<p style="margin:0 0 16px;font-size:17px;line-height:1.6;color:#121218">${esc(t.p1)}</p>
<p style="margin:0 0 28px;font-size:17px;line-height:1.6;color:#54545F">${esc(t.p2)}</p>
<table role="presentation" cellpadding="0" cellspacing="0"><tr><td>${btn("{{lien_principal}}", t.cta)}</td></tr></table>
<p style="margin:18px 0 0;font-size:15px"><a href="{{lien_solutions}}" style="color:#B53A0A;font-weight:600">${esc(t.cta2)} &rarr;</a></p>
</td></tr>
${showTools ? `<tr><td class="p" style="padding:36px 40px 8px"><table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td colspan="2" style="padding-bottom:10px;font-family:'Courier New',monospace;font-size:13px;letter-spacing:.06em;text-transform:uppercase;color:#54545F">${esc(g.outils)}</td></tr>${rows}<tr><td colspan="2" style="border-top:1px solid #E4E2D9;font-size:1px;line-height:1px">&nbsp;</td></tr></table></td></tr>` : ""}
${type === "infolettre" ? `<tr><td class="p" style="padding:24px 40px 8px;font-family:${FONT}"><h2 style="margin:0 0 10px;font-size:22px;line-height:1.2;color:#0A0A0E">{{article_2_titre}}</h2><p style="margin:0 0 16px;font-size:16px;line-height:1.6;color:#121218">{{article_2_texte}}</p><a href="{{article_2_lien}}" style="color:#B53A0A;font-weight:600">${esc(T[lang].infolettre.cta)} &rarr;</a></td></tr>` : ""}
<tr><td style="padding:32px 0 0"><img src="images/pied.${lang}.png" width="600" height="100" alt="Nexora AI. ${esc(TXT.quebec[lang])}" style="width:100%;height:auto"></td></tr>
<tr><td class="p" style="padding:20px 40px 32px;font-family:${FONT};font-size:12px;line-height:1.6;color:#54545F">
${esc(g.legal)}<br>Nexora AI, ${esc(adresse)} &middot; ${esc(courriel)}<br><a href="{{lien_desabonnement}}" style="color:#54545F">${esc(g.desab)}</a>
</td></tr>
</table></td></tr></table>
</body></html>`;
}
export function ecrireModeles() {
  const dir = path.join(RAC, "final", DIR, "modeles");
  fs.mkdirSync(path.join(dir, "images"), { recursive: true });
  const out = [];
  for (const lang of ["fr", "en"]) for (const type of ["lancement", "infolettre", "invitation"]) {
    const f = path.join(dir, `modele-${type}.${lang}.html`);
    fs.writeFileSync(f, modele(type, lang));
    out.push(f);
  }
  // les images référencées par les modèles
  const src = path.join(RAC, "final", DIR, "images");
  if (fs.existsSync(src)) for (const f of fs.readdirSync(src)) fs.copyFileSync(path.join(src, f), path.join(dir, "images", f));
  return out;
}
