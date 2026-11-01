// Page d'atterrissage de lancement : une seule page HTML/CSS autonome (polices, images, mosaïque intégrées), 390 à 1440 px.
// bun atterrissage.mjs  -> final/atterrissage/index.fr.html, index.en.html et aperçus 1440 / 390.
import fs from "node:fs";
import path from "node:path";
import { SRC, C, BARRES, TXT, OUTILS, mosaique, glyphe, esc, coordonnees } from "../../social/sources/moteur/marque.mjs";
import { chromium } from "/home/pc6/Desktop/NexoraSite/web/node_modules/@playwright/test/index.mjs";

const RAC = path.resolve(import.meta.dirname, "..");
const b64 = (f) => fs.readFileSync(f).toString("base64");
const font = (n) => `data:font/woff2;base64,${b64(path.join(SRC, "polices", `${n}-latin-wght-normal.woff2`))}`;
const jpg = (n) => `data:image/jpeg;base64,${b64(path.join(import.meta.dirname, "atterrissage-img", n))}`;
const svgUri = (f) => `data:image/svg+xml;base64,${b64(path.join(SRC, "logos", f))}`;

/** Mosaïque responsive : on retire la taille et le positionnement fixes, le CSS s'en charge. */
function mosa(opts, cls = "mo") {
  return mosaique(opts).replace(/ width="\d+" height="\d+" style="[^"]*"/, ` class="${cls}" preserveAspectRatio="xMaxYMid slice"`);
}
const site = coordonnees.site, placeholder = String(site).startsWith("«");
const LIEN = placeholder ? "#contact" : `${site.replace(/\/$/, "")}/contact`;
const split = (s) => [s.split(". ")[0] + ".", s.split(". ").slice(1).join(". ")];

const L = {
  fr: {
    titre: "Nexora AI | Rêvez grand. Gardez le contrôle.", desc: "Nexora AI : IA souveraine au Québec. Un compte, des crédits, huit outils. Vos données restent chez vous ou au Québec.",
    skip: "Aller au contenu", nav: ["Les outils", "Le contrôle", "La méthode"], cta: "Planifier un diagnostic", voir: "Voir les outils",
    intro: "Nexora AI conçoit, installe et accompagne des systèmes d’IA adaptés à votre métier, chez vous ou hébergés au Québec.",
    famille: "Un compte. Tous vos outils.", familleSous: "Huit outils, des crédits, un seul accès. L’état de chacun est écrit en toutes lettres : rien n’est promis d’avance.",
    ctrlK: "Le contrôle", ctrlT: "Vos données restent les vôtres.", ctrlS: "Deux façons de garder la main, et une règle qui ne change pas.",
    modes: [["Sur place", "Chez vous.", "Vos données restent sur votre serveur."], ["Hébergé", "Au Québec.", "Dans l’infrastructure de Nexora AI, située au Québec, sauvegardes comprises."], ["Toujours", "Jamais pour entraîner.", "Les données d’un client ne servent jamais à entraîner ni à ajuster un modèle."]],
    note: "Un serveur au Québec n’écarte pas, à lui seul, les lois qui s’appliquent : nous ne promettons ni risque nul ni conformité automatique.",
    metK: "La méthode", metT: "Cinq temps, un seul fil.", etapes: ["Comprendre", "Intégrer", "Vérifier", "Former", "Exploiter et améliorer"],
    finT: "Rêvez grand. Gardez le contrôle.", finS: "Parlons de votre projet, sans engagement.", contact: "Coordonnées", courriel: "Courriel", tel: "Téléphone", adr: "Adresse", web: "Site",
    pied: "Entreprise québécoise d’IA.", etat: "État", photoAlt: "Aurore orange au-dessus d’une forêt boréale enneigée", rivAlt: "Le fleuve Saint-Laurent à l’aube", quebec: "IA souveraine au Québec", sig: TXT.signature.fr,
  },
  en: {
    titre: "Nexora AI | Dream big. Stay in control.", desc: "Nexora AI: sovereign AI, made in Québec. One account, credits, eight tools. Your data stays with you or in Québec.",
    skip: "Skip to content", nav: ["The tools", "Control", "Method"], cta: "Book a diagnostic", voir: "See the tools",
    intro: "Nexora AI designs, installs and supports AI systems built for your business, on your premises or hosted in Québec.",
    famille: "One account. All your tools.", familleSous: "Eight tools, credits, one access. The status of each is spelled out: nothing is promised in advance.",
    ctrlK: "Control", ctrlT: "Your data stays yours.", ctrlS: "Two ways to keep your hands on it, and one rule that never changes.",
    modes: [["On premises", "With you.", "Your data stays on your server."], ["Hosted", "In Québec.", "In Nexora AI’s infrastructure, located in Québec, backups included."], ["Always", "Never to train.", "A client’s data is never used to train or tune a model."]],
    note: "A server in Québec does not, by itself, set aside the laws that apply: we promise neither zero risk nor automatic compliance.",
    metK: "Method", metT: "Five steps, one thread.", etapes: ["Understand", "Integrate", "Verify", "Train", "Operate and improve"],
    finT: "Dream big. Stay in control.", finS: "Let’s talk about your project, no commitment.", contact: "Contact", courriel: "Email", tel: "Phone", adr: "Address", web: "Website",
    pied: "A Québec AI company.", etat: "Status", photoAlt: "Orange aurora over a snowy boreal forest", rivAlt: "The Saint Lawrence river at dawn", quebec: "Sovereign AI, made in Québec", sig: TXT.signature.en,
  },
};

function html(lang) {
  const t = L[lang];
  const [c1, c2] = split(TXT.campagne[lang]);
  const hero = mosa({ x: 0, y: 0, w: 640, h: 780, cell: 26, seed: 1301, toward: "right", fade: 1, gap: 0.14 });
  const band = mosa({ x: 0, y: 0, w: 900, h: 200, cell: 26, seed: 1302, toward: "right", fade: 1, gap: 0.14 }, "mo mo-band");
  const cards = OUTILS.map((o, i) => `<li class="card"><div class="card__top">${glyphe(o.id, { size: 56 })}<span class="chip">${esc(o.etat[lang])}</span></div><p class="card__nom">${esc(o.nom)}</p><h3>${esc(o.titre[lang])}</h3><p class="card__sous">${esc(o.sous[lang])}</p></li>`).join("");
  const modes = t.modes.map((m) => `<li class="mode"><p class="lib">${esc(m[0])}</p><h3>${esc(m[1])}</h3><p>${esc(m[2])}</p></li>`).join("");
  const etapes = t.etapes.map((e, i) => `<li><i style="background:${BARRES[Math.min(i, 3)]}"></i><span>${esc(e)}</span></li>`).join("");
  const blink = [[14, 3], [19, 8], [10, 12], [22, 15], [16, 17], [21, 4], [23, 11], [12, 6]].map(([c, r], i) => `<rect class="bl" x="${c + 0.07}" y="${r + 0.07}" width="0.86" height="0.86" fill="${["#FFD37A", "#FFB11A", "#FF8A1F"][i % 3]}" style="animation-delay:${(i * 1.3).toFixed(1)}s"/>`).join("");
  const heroSvg = hero.replace("</svg>", `${blink}</svg>`);
  const css = `
@font-face{font-family:Geist;src:url(${font("geist")}) format("woff2");font-weight:100 900;font-display:swap}
@font-face{font-family:Inter;src:url(${font("inter")}) format("woff2");font-weight:100 900;font-display:swap}
@font-face{font-family:"JetBrains Mono";src:url(${font("jetbrains-mono")}) format("woff2");font-weight:100 800;font-display:swap}
:root{--noir:#0A0A0E;--surf:#121218;--clair:#F5F4EF;--gris:#A8A8B6;--or:#FF5A1F;--ort:#FF7A45;--line:rgba(245,244,239,.14);--lines:rgba(245,244,239,.26);--g:clamp(20px,4vw,40px);--sec:clamp(64px,9vw,120px)}
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth;-webkit-text-size-adjust:100%}
body{background:var(--noir);color:var(--clair);font:400 17px/1.6 Inter,system-ui,-apple-system,"Segoe UI",sans-serif;-webkit-font-smoothing:antialiased}
img,svg{display:block;max-width:100%}
a{color:inherit}
h1,h2,h3{font-family:Geist,Inter,system-ui,sans-serif;font-weight:500;letter-spacing:-.03em;line-height:1.04;text-wrap:balance}
.lib{font:500 12px/1.4 "JetBrains Mono",ui-monospace,monospace;letter-spacing:.06em;text-transform:uppercase}
.wrap{max-width:1280px;margin:0 auto;padding:0 var(--g)}
.skip{position:absolute;left:-999px;top:8px;background:var(--or);color:var(--noir);padding:12px 18px;border-radius:6px;font-weight:600;z-index:100}.skip:focus{left:8px}
:focus-visible{outline:2px solid var(--ort);outline-offset:3px;border-radius:4px}
.btn{display:inline-flex;align-items:center;gap:12px;min-height:52px;padding:0 26px;border-radius:6px;font:600 17px/1 Inter,system-ui,sans-serif;text-decoration:none;letter-spacing:-.01em;transition:background-color .2s,border-color .2s}
.btn--or{background:var(--or);color:var(--noir)}.btn--or:hover{background:var(--ort)}
.btn--ln{border:1px solid var(--lines);color:var(--clair)}.btn--ln:hover{border-color:var(--clair)}
.btn svg{width:18px;height:18px}
header.top{position:sticky;top:0;z-index:50;background:rgba(10,10,14,.86);backdrop-filter:blur(10px);border-bottom:1px solid var(--line)}
header.top .wrap{display:flex;align-items:center;justify-content:space-between;gap:16px;height:68px}
header.top img{height:28px;width:auto}
header.top nav{display:flex;gap:28px}header.top nav a{color:var(--gris);text-decoration:none;font-size:15px}header.top nav a:hover{color:var(--clair)}
header.top .btn{min-height:44px;padding:0 18px;font-size:15px}
@media (max-width:860px){header.top nav{display:none}header.top .btn span.l{display:none}}
/* héros */
.hero{position:relative;overflow:hidden;border-bottom:1px solid var(--line);background:radial-gradient(60rem 30rem at 100% -10%,rgba(255,90,31,.22),transparent 64%),radial-gradient(40rem 24rem at 0% 110%,rgba(74,135,255,.10),transparent 68%)}
.hero__grid{position:absolute;inset:0;background-image:linear-gradient(to right,var(--line) 1px,transparent 1px),linear-gradient(to bottom,var(--line) 1px,transparent 1px);background-size:64px 64px;opacity:.5;-webkit-mask-image:radial-gradient(70% 90% at 40% 40%,#000 20%,transparent 78%);mask-image:radial-gradient(70% 90% at 40% 40%,#000 20%,transparent 78%)}
.hero__photo{position:absolute;inset:0;background:url(${jpg("hero.jpg")}) 70% 40%/cover no-repeat;opacity:.55;-webkit-mask-image:linear-gradient(90deg,transparent 12%,#000 60%);mask-image:linear-gradient(90deg,transparent 12%,#000 60%)}
.hero .mo{position:absolute;right:0;top:0;height:100%;width:min(44%,640px)}
.hero .wrap{position:relative;padding-top:clamp(56px,9vw,128px);padding-bottom:clamp(96px,12vw,160px)}
.hero__txt{max-width:640px}
.hero h1{font-size:clamp(48px,12.6vw,112px);line-height:.98;margin:22px 0 28px}
.hero h1 span{display:block}.hero h1 .a{color:var(--ort)}
.hero .lede{font-size:clamp(18px,2vw,22px);line-height:1.5;color:var(--gris);max-width:36ch}
.hero .sig{font-family:Geist,sans-serif;font-weight:500;font-size:clamp(20px,2.4vw,28px);letter-spacing:-.02em;line-height:1.2;color:var(--clair);margin:0 0 28px;max-width:26ch}
.hero .cta{display:flex;flex-wrap:wrap;gap:14px;margin-top:36px}
.ruler{position:absolute;left:0;right:0;bottom:0;height:10px;background-image:linear-gradient(to right,rgba(245,244,239,.32) 1px,transparent 1px),linear-gradient(to right,rgba(245,244,239,.16) 1px,transparent 1px);background-size:64px 10px,8px 5px;background-position:left bottom;background-repeat:repeat-x}
.bl{opacity:0}
@media (max-width:860px){
 .hero .mo{position:relative;display:block;width:100%;height:150px;margin-bottom:0}
 .hero__photo{opacity:.35;-webkit-mask-image:linear-gradient(0deg,transparent 10%,#000 80%);mask-image:linear-gradient(0deg,transparent 10%,#000 80%)}
 .hero .wrap{padding-top:0}.hero .wrap>.hero__mob{display:block}
 .hero__txt{padding-top:36px}
}
@media (min-width:861px){.hero__mob{display:none}}
/* sections */
section{border-bottom:1px solid var(--line)}
.sec{padding:var(--sec) 0}
.sec h2{font-size:clamp(34px,5.4vw,64px);margin:14px 0 18px}
.sec .lead{color:var(--gris);font-size:clamp(17px,1.6vw,20px);max-width:52ch}
.sec h2 .a{color:var(--ort)}
/* outils */
.cards{list-style:none;display:grid;grid-template-columns:1fr;border:1px solid var(--line);margin-top:48px;background:var(--line);gap:1px}
.card{background:var(--noir);padding:28px;display:flex;flex-direction:column;gap:14px;min-height:300px;transition:background-color .2s}
.card:hover{background:var(--surf)}
.card__top{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;margin-bottom:auto}
.chip{font:500 11.5px/1 "JetBrains Mono",monospace;letter-spacing:.06em;text-transform:uppercase;color:var(--ort);border:1px solid var(--lines);border-radius:4px;padding:7px 9px}
.card__nom{font:500 12px/1.4 "JetBrains Mono",monospace;letter-spacing:.06em;text-transform:uppercase;color:var(--gris)}
.card h3{font-size:clamp(24px,2.3vw,30px)}
.card__sous{color:var(--gris);font-size:15.5px;line-height:1.5}
@media (min-width:600px){.cards{grid-template-columns:repeat(2,1fr)}}
@media (min-width:1080px){.cards{grid-template-columns:repeat(4,1fr)}}
/* contrôle */
.ctrl{position:relative;overflow:hidden;background:var(--surf)}
.ctrl__photo{position:absolute;inset:0;background:url(${jpg("quebec.jpg")}) 50% 50%/cover no-repeat;opacity:.42}
.ctrl__veil{position:absolute;inset:0;background:linear-gradient(90deg,var(--noir) 0%,rgba(10,10,14,.78) 45%,rgba(10,10,14,.35) 100%)}
.ctrl .wrap{position:relative}
.modes{list-style:none;display:grid;gap:1px;grid-template-columns:1fr;margin-top:44px;background:var(--lines);border:1px solid var(--lines)}
.mode{background:rgba(10,10,14,.82);padding:28px;display:flex;flex-direction:column;gap:12px;min-height:220px;backdrop-filter:blur(4px)}
.mode .lib{color:var(--ort)}.mode h3{font-size:clamp(26px,2.6vw,34px)}.mode p:last-child{color:var(--gris);font-size:16px}
@media (min-width:860px){.modes{grid-template-columns:repeat(3,1fr)}}
.note{margin-top:28px;color:var(--gris);font-size:14.5px;max-width:70ch}
/* méthode */
.steps{list-style:none;margin-top:44px;border-top:1px solid var(--line)}
.steps li{display:flex;align-items:center;gap:24px;padding:22px 0;border-bottom:1px solid var(--line);font:500 clamp(24px,3.4vw,40px)/1.1 Geist,sans-serif;letter-spacing:-.02em}
.steps i{width:22px;height:22px;display:block;flex:none}
/* fin */
.fin{position:relative;overflow:hidden;background:radial-gradient(50rem 24rem at 100% 100%,rgba(255,90,31,.20),transparent 64%)}
.fin .mo-band{position:absolute;right:0;top:0;width:min(60%,720px);height:clamp(90px,14vw,180px);opacity:.9}
.fin .wrap{position:relative;padding-top:calc(clamp(90px,14vw,180px) + clamp(48px,6vw,100px));padding-bottom:var(--sec)}
.fin h2{font-size:clamp(40px,7vw,88px);line-height:1}
.fin p.lead{margin-top:22px}
.fin .cta{display:flex;flex-wrap:wrap;gap:14px;margin-top:36px}
.coord{margin-top:56px;display:grid;gap:1px;background:var(--line);border:1px solid var(--line);grid-template-columns:1fr}
.coord div{background:var(--noir);padding:20px 24px}.coord dt{color:var(--gris)}.coord dd{margin-top:6px;overflow-wrap:anywhere}
@media (min-width:760px){.coord{grid-template-columns:repeat(2,1fr)}}
@media (min-width:1100px){.coord{grid-template-columns:repeat(4,1fr)}}
footer{background:var(--noir)}
footer .stripes{display:flex;flex-direction:column;height:16px}footer .stripes i{flex:1}
footer .wrap{display:flex;flex-wrap:wrap;gap:16px 32px;justify-content:space-between;align-items:center;padding-top:36px;padding-bottom:36px}
footer img{height:28px;width:auto}footer p{color:var(--gris);font-size:14px}
@media (prefers-reduced-motion:no-preference){
 .bl{animation:bl 9s ease-in-out infinite}
 @keyframes bl{0%,60%,100%{opacity:0}70%,85%{opacity:1}}
 .hero .mo{animation:drift 14s ease-in-out infinite alternate}
 @keyframes drift{to{transform:translateX(-10px)}}
 @supports (animation-timeline:view()){
  .card,.mode,.steps li{animation:rise both linear;animation-timeline:view();animation-range:entry 0% entry 40%}
  @keyframes rise{from{opacity:0;transform:translateY(18px)}}
 }
}`;
  const arrow = `<svg viewBox="0 0 20 20" aria-hidden="true" shape-rendering="crispEdges"><path d="M2 9h12V7h2v2h2v2h-2v2h-2v-2H2zM12 5h2v2h-2zm0 8h2v2h-2z" fill="currentColor"/></svg>`;
  const coord = [[t.courriel, coordonnees.courriel_general], [t.tel, coordonnees.telephone], [t.adr, coordonnees.adresse], [t.web, coordonnees.site]].map(([k, v]) => `<div><dt class="lib">${esc(k)}</dt><dd>${esc(v)}</dd></div>`).join("");
  return `<!doctype html>
<html lang="${lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>${esc(t.titre)}</title><meta name="description" content="${esc(t.desc)}"><meta name="theme-color" content="#0A0A0E"><meta name="color-scheme" content="dark">
<style>${css}</style></head><body>
<a class="skip" href="#principal">${esc(t.skip)}</a>
<header class="top"><div class="wrap"><a href="#debut" aria-label="Nexora AI"><img src="${svgUri("nexora-ai-logo-sombre.svg")}" alt="Nexora AI" width="154" height="28"></a>
<nav aria-label="${lang === "fr" ? "Sections" : "Sections"}"><a href="#outils">${esc(t.nav[0])}</a><a href="#controle">${esc(t.nav[1])}</a><a href="#methode">${esc(t.nav[2])}</a></nav>
<a class="btn btn--or" href="${LIEN}" aria-label="${esc(t.cta)}"><span class="l">${esc(t.cta)}</span><span class="lib" style="display:none"></span>${arrow}</a></div></header>
<main id="principal">
<section class="hero" id="debut"><div class="hero__photo" role="img" aria-label="${esc(t.photoAlt)}"></div><div class="hero__grid" aria-hidden="true"></div>
${heroSvg.replace("<svg ", '<svg role="presentation" aria-hidden="true" ')}
<div class="wrap"><div class="hero__txt"><p class="lib" style="color:var(--ort)">${esc(t.quebec)}</p>
<h1><span>${esc(c1)}</span><span class="a">${esc(c2)}</span></h1>
<p class="sig">${esc(t.sig)}</p><p class="lede">${esc(t.intro)}</p>
<div class="cta"><a class="btn btn--or" href="${LIEN}">${esc(t.cta)}${arrow}</a><a class="btn btn--ln" href="#outils">${esc(t.voir)}</a></div></div></div><div class="ruler" aria-hidden="true"></div></section>
<section id="outils" class="sec"><div class="wrap"><p class="lib" style="color:var(--ort)">${lang === "fr" ? "Huit outils" : "Eight tools"}</p><h2>${esc(t.famille.split(". ")[0] + ".")} <span class="a">${esc(t.famille.split(". ")[1])}</span></h2><p class="lead">${esc(t.familleSous)}</p><ul class="cards">${cards}</ul></div></section>
<section id="controle" class="sec ctrl"><div class="ctrl__photo" role="img" aria-label="${esc(t.rivAlt)}"></div><div class="ctrl__veil" aria-hidden="true"></div><div class="wrap"><p class="lib" style="color:var(--ort)">${esc(t.ctrlK)}</p><h2>${esc(t.ctrlT)}</h2><p class="lead">${esc(t.ctrlS)}</p><ul class="modes">${modes}</ul><p class="note">${esc(t.note)}</p></div></section>
<section id="methode" class="sec"><div class="wrap"><p class="lib" style="color:var(--ort)">${esc(t.metK)}</p><h2>${esc(t.metT)}</h2><ol class="steps">${etapes}</ol></div></section>
<section id="contact" class="fin"><div class="mo-wrap" aria-hidden="true">${band}</div><div class="wrap"><h2>${esc(c1)}<br><span class="a">${esc(c2)}</span></h2><p class="lead">${esc(t.finS)}</p><div class="cta"><a class="btn btn--or" href="${LIEN}">${esc(t.cta)}${arrow}</a></div><dl class="coord" aria-label="${esc(t.contact)}">${coord}</dl></div></section>
</main>
<footer><div class="stripes" aria-hidden="true">${BARRES.map((b) => `<i style="background:${b}"></i>`).join("")}</div><div class="wrap"><img src="${svgUri("nexora-ai-logo-sombre.svg")}" alt="Nexora AI" width="154" height="28"><p>${esc(t.pied)} ${esc(t.sig)}</p></div></footer>
</body></html>`.replace('<div class="mo-wrap" aria-hidden="true">', '<div class="mo-wrap" aria-hidden="true" style="display:contents">');
}

export async function construire() {
  const dir = path.join(RAC, "final", "atterrissage");
  fs.mkdirSync(dir, { recursive: true });
  const b = await chromium.launch();
  const out = [];
  for (const lang of ["fr", "en"]) {
    const f = path.join(dir, `index.${lang}.html`);
    fs.writeFileSync(f, html(lang));
    for (const w of [1440, 390]) {
      const p = await b.newPage({ viewport: { width: w, height: w === 1440 ? 900 : 844 }, reducedMotion: "reduce" });
      await p.goto("file://" + f); await p.waitForTimeout(600);
      await p.screenshot({ path: path.join(dir, `apercu-${w}.${lang}.png`), fullPage: true });
      const over = await p.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
      if (over > 0) console.log(`DÉBORDEMENT horizontal ${lang} ${w}px : ${over}px`);
      await p.close();
    }
    out.push(f, fs.statSync(f).size);
  }
  await b.close();
  return out;
}
if (import.meta.main) console.log(await construire());
