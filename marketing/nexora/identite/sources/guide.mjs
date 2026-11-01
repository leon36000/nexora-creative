// Guide de marque « Kit de marque Nexora AI » : PDF 16:9 (1920 × 1080), fr-CA et en-CA, rendu HTML → PDF.
//   bun identite/sources/guide.mjs
import { M, ID, IM, C, PALETTES, esc, lireCoordonnees, COORDONNEES, TEXTE } from "./moteur.mjs";
import { join } from "node:path";
import { existsSync, mkdirSync } from "node:fs";

const FINAL = join(ID, "final", "guide"), HTML = join(ID, "sources", "html", "guide");
mkdirSync(FINAL, { recursive: true }); mkdirSync(HTML, { recursive: true });
const c = lireCoordonnees(COORDONNEES);
const IMP = join(IM, "final"), GEN = join(IM, "sources", "generees");
const img = (p) => M.htmlRel(HTML, p);
const jpgOuPng = (nom) => { const f = join(GEN, `${nom}-x4.jpg`); return img(existsSync(f) ? f : join(GEN, `${nom}.png`)); };
const existe = (p) => existsSync(p);
const nav = await M.navigateur();

const CSS = `
@page{size:1920px 1080px;margin:0}
.p{position:relative;width:1920px;height:1080px;overflow:hidden;break-after:page;page-break-after:always}
.p:last-child{break-after:auto;page-break-after:auto}
.sombre{background:var(--noir);color:var(--texte-clair)} .clair{background:var(--papier);color:var(--encre)} .creme{background:var(--creme);color:var(--encre)}
.rail{position:absolute;top:0;bottom:0;width:1px;background:var(--ligne)}
.rail i{position:absolute;top:60px;left:-5px;width:10px;height:10px;background:var(--orange)}
.sombre{--ligne:rgba(245,244,239,.16);--sec:var(--gris);--acc:var(--orange-s);--surf:#121218}
.clair,.creme{--ligne:rgba(18,18,24,.16);--sec:var(--gris-sombre);--acc:var(--orange-c);--surf:var(--creme)}
.tete{position:absolute;left:96px;right:96px;top:50px;display:flex;justify-content:space-between;font-size:15px;color:var(--sec)}
.pied{position:absolute;left:96px;right:96px;bottom:42px;display:flex;justify-content:space-between;align-items:center;font-size:14px;color:var(--sec)}
.pied svg{height:22px;width:auto}
h1{font-family:Geist,sans-serif;font-weight:500;letter-spacing:-.03em;line-height:1.02;font-size:92px}
h2{font-family:Geist,sans-serif;font-weight:500;letter-spacing:-.025em;line-height:1.08;font-size:56px}
h3{font-family:Geist,sans-serif;font-weight:500;letter-spacing:-.018em;line-height:1.18;font-size:30px}
.lead{font-size:26px;line-height:1.5;color:var(--sec)}
.txt{font-size:21px;line-height:1.55;color:var(--sec)}
.lab{font-family:'JetBrains Mono',monospace;text-transform:uppercase;letter-spacing:.06em;font-weight:500;font-size:14px;line-height:1.4}
.acc{color:var(--acc)}
.abs{position:absolute}
.filet{border-top:1px solid var(--ligne)}
.cadre{border:1px solid var(--ligne)}
.chip{position:relative;display:flex;flex-direction:column;justify-content:flex-end;padding:20px 22px;border:1px solid var(--ligne)}
.chip b{font-family:Geist;font-weight:500;font-size:24px;letter-spacing:-.02em;display:block}
.chip span{font-family:'JetBrains Mono';font-size:14px;letter-spacing:.04em}
.non{position:absolute;right:18px;top:16px;font-family:'JetBrains Mono';font-size:13px;letter-spacing:.06em;color:#FF7A45;font-weight:500}
`;

const L = {
  fr: {
    kit: "Kit de marque", version: "Version 1 · Novembre 2026",
    sousCouv: "Le nom, le logo, les couleurs, les lettres et la matière : tout ce qu’il faut pour que chaque pièce se reconnaisse à trois mètres.",
    sommaireT: "Sommaire", sommaire: ["Le nom et la signature", "Le logo", "Construction et zone de protection", "Versions", "Tailles minimales", "Usages interdits", "Couleurs", "La braise", "Typographies", "Hiérarchie", "La mosaïque", "Grille, règle et bande", "Le monde visuel", "Ton de voix", "Imprimés", "Affiches", "La famille d’outils", "Les fichiers du kit"],
    nomT: "Le nom.", nomTxt: ["Nexora AI : l’entreprise et la marque. On l’écrit ainsi partout où le nom désigne l’entreprise.", "Les produits gardent leur nom : Nexora WorkStudio, Nexora Code, Nexora RAG… On n’écrit jamais « Nexora AI WorkStudio ».", "Jamais « Nexora Ai », jamais « NEXORA AI » (les libellés en capitales sont réservés à la police mono)."],
    sigT: "La signature", signature: TEXTE.fr.signature, campagneT: "La ligne de campagne", campagne: TEXTE.fr.campagne, quebecT: "La ligne Québec", quebec: TEXTE.fr.quebec,
    logoT: "Un « N » en pixels.", logoTxt: "Deux montants d’encre et une diagonale de trois carrés orange qui les relie. La diagonale est le point de passage : ce qui entre, ce qui est approuvé, ce qui est contrôlé. Les pixels sont l’unité de construction de toute la marque. Aucun robot, aucun cerveau.",
    consT: "Construction.", consTxt: ["Grille de 64 unités ; l’encre occupe de 6 à 58.", "Cinq colonnes et cinq rangées de 10,4 unités, sans jeu. Deux montants pleins (colonnes 1 et 5) ; diagonale des cellules (2, 2), (3, 3) et (4, 4), qui se touchent par un angle.", "Logotype : « Nexora » et « A » en contours de Geist 500 (−0,03 em) ; le « I » est dessiné avec des empattements pour ne pas se lire « Al »."], zoneT: "Zone de protection", zoneTxt: "Un vide d’au moins la largeur d’un montant (10 unités sur 64, soit 0,2 fois la hauteur du symbole) sur les quatre côtés. Aucun texte, bord de page ni image ne l’entame.",
    versT: "Versions.", versTxt: "Les fichiers officiels ne se modifient pas : on choisit la bonne version pour le fond.", versCap: ["Logo, fond clair", "Logo, fond sombre", "Monochrome noir", "Monochrome blanc, sur orange"], versNote: "Monochromes : gravure, tampon, fax, impression une couleur, et sur l’orange.",
    minT: "Tailles minimales.", minTxt: "En dessous, on passe au symbole seul.", minLogo: "Logo complet", minLogoV: "110 px de large à l’écran · 18 mm en impression", minSym: "Symbole seul", minSymV: "16 px (favicon)",
    interT: "Usages interdits.", inter: ["Changer l’orange", "Ajouter dégradé, ombre ou lueur", "Modifier la diagonale", "Pivoter, incliner, arrondir", "Étirer ou écraser", "Recomposer le logotype", "Poser sur la mosaïque ou sur l’orange", "Répéter en motif ou en puce"], interNote: "Aussi : sous 3:1 de contraste, avec un robot, un cerveau lumineux ou une étincelle « IA ».",
    coulT: "Couleurs.", coulLead: "Une seule teinte d’accent : l’orange signal. Le reste est noir, papier et gris.",
    brT: "La braise.", brLead: "Une rampe chaude, du bord qui se dissout au cœur. Elle sert de matière, jamais de texte.", brAutres: "Autres rampes : une par maquette de produit",
    typT: "Typographies.", typLead: "Libres et servies localement. Trois voix, pas une de plus.", typRoles: ["Titres, graisse 500", "Texte courant", "Libellés techniques"],
    hierT: "Hiérarchie.", hierLead: "Peu de niveaux, de grands écarts, des titres jamais gras.", hierCols: ["Niveau", "Taille", "Interligne", "Interlettrage"],
    mosT: "La mosaïque.", mosTxt: "Un champ de carrés dont la teinte suit la rampe braise et qui se dissout en pixels vers un bord, comme une image qui se calcule. Générée en code, graine fixe : même image à chaque rendu. Le texte ne se pose jamais dessus.",
    gT: "Grille, règle et bande.", gA: "Grille de mesure", gAt: "Filets fins qui s’effacent vers les bords.", gB: "Règle graduée", gBt: "Une graduation courte, une plus haute toutes les huit.", gC: "Bande braise", gCt: "Quatre barres franches : ambre, orange, vermillon, framboise.", gD: "Rayons de 2 à 12 px, aucune pilule, aucune ombre décorative, filets de 1 px.",
    monT: "Le monde visuel : la braise.", monTxt: "Nuit québécoise, matière de lumière, pixels qui deviennent des mondes. Orange signal contre noir profond et bleu nuit. Cinématographique, jamais « stock ». Une idée par image, un seul point focal.", monNon: "Jamais : robot, cerveau lumineux, étincelle « IA », puce en néon bleu, mains robotiques, photo d’archive, faux client. Aucun texte dans une image générée : le texte se pose en code.", monCap: ["Aurore sur la forêt boréale", "Ville au crépuscule", "L’atelier où la lumière fabrique"],
    tonT: "Ton de voix.", tonLead: "Précis, calme, direct. On vouvoie. On promet peu et on le dit en clair.",
    tonRegles: ["Phrases courtes. Un verbe, une idée.", "Le vouvoiement, toujours.", "Aucun chiffre, prix, date, statistique ni certification qu’on ne peut prouver.", "Un outil non livré est « Bientôt » ou « Plus tard », jamais au présent.", "Pas de « meilleur », de « numéro 1 » ni de garantie."],
    tonOui: "Oui", tonNon: "Non", tonExOui: ["L’IA qui travaille pour votre entreprise. Sous votre contrôle.", "Vos données restent chez vous ou au Québec.", "Nous n’annonçons que ce que nous pouvons tenir."], tonExNon: ["Révolutionnez votre business avec l’IA ultime !", "La meilleure IA du marché, garantie.", "Disponible bientôt, 100 % sécurisé."],
    appT: "Imprimés.", appLead: "Même grille, mêmes marges, même matière : une pièce se reconnaît à trois mètres.", appCap: ["Carte d’affaires, recto", "Carte d’affaires, verso", "Papier à en-tête", "Enveloppe DL", "Carte de remerciement"],
    affT: "Affiches.", affLead: "Un titre court, un point focal, de grandes respirations de noir.",
    famT: "La famille d’outils.", famLead: "Un compte, des crédits, tous les outils. Chaque outil affiche son état réel.", famNote: "Le symbole est suivi du nom du produit, en Geist 500 : le logo n’est jamais modifié.",
    filT: "Les fichiers du kit.", filLead: "Tout se régénère par commande depuis les sources.",
    fil: [["identite/final/logos/", "Logos : SVG officiels, PNG de 256 à 4096 px, PDF vectoriels"], ["identite/final/profils/", "Photos de profil, 1080 px"], ["identite/final/verrouillages/", "Verrouillages de produit : SVG et PNG"], ["identite/final/icones/", "Icônes d’application et bannière 1024"], ["imprimes/final/", "Cartes, papeterie, affiches, dépliants, salon, présentation"], ["identite/sources/", "Moteur de gabarits, polices, scripts de génération"]],
    finT: "Rêvez grand.\nGardez le contrôle.", finL: "Parlons-en",
    entete: "Nexora AI · Kit de marque", etat: "État", etats: TEXTE.fr.etats,
  },
  en: {
    kit: "Brand kit", version: "Version 1 · November 2026",
    sousCouv: "The name, the logo, the colours, the letters and the matter: everything a piece needs to be recognized from three metres away.",
    sommaireT: "Contents", sommaire: ["Name and signature", "The logo", "Construction and clear space", "Versions", "Minimum sizes", "Misuse", "Colours", "The ember", "Typefaces", "Hierarchy", "The mosaic", "Grid, ruler and band", "The visual world", "Tone of voice", "Print", "Posters", "The tool family", "Kit files"],
    nomT: "The name.", nomTxt: ["Nexora AI: the company and the brand. Written this way wherever the name stands for the company.", "Products keep their own names: Nexora WorkStudio, Nexora Code, Nexora RAG… We never write “Nexora AI WorkStudio”.", "Never “Nexora Ai”, never “NEXORA AI” (all-caps labels belong to the mono typeface only)."],
    sigT: "The signature", signature: TEXTE.en.signature, campagneT: "The campaign line", campagne: TEXTE.en.campagne, quebecT: "The Québec line", quebec: TEXTE.en.quebec,
    logoT: "An “N” in pixels.", logoTxt: "Two ink uprights and a diagonal of three orange squares that joins them. The diagonal is the point of passage: what comes in, what is approved, what is controlled. Pixels are the building unit of the whole brand. No robot, no brain.",
    consT: "Construction.", consTxt: ["A 64-unit grid; the ink spans 6 to 58.", "Five columns and five rows of 10.4 units, no gaps. Two solid uprights (columns 1 and 5); a diagonal of cells (2, 2), (3, 3) and (4, 4), touching at their corners.", "Wordmark: “Nexora” and “A” as outlines of Geist 500 (−0.03 em); the “I” is drawn with serifs so it does not read as “Al”."], zoneT: "Clear space", zoneTxt: "A margin of at least one upright’s width (10 units out of 64, or 0.2 times the symbol height) on all four sides. No text, page edge or image enters it.",
    versT: "Versions.", versTxt: "The official files are never edited: pick the right version for the background.", versCap: ["Logo, light background", "Logo, dark background", "Black monochrome", "White monochrome, on orange"], versNote: "Monochromes: engraving, stamps, fax, one-colour printing, and on orange.",
    minT: "Minimum sizes.", minTxt: "Below these, switch to the symbol alone.", minLogo: "Full logo", minLogoV: "110 px wide on screen · 18 mm in print", minSym: "Symbol alone", minSymV: "16 px (favicon)",
    interT: "Misuse.", inter: ["Changing the orange", "Adding a gradient, shadow or glow", "Altering the diagonal", "Rotating, slanting, rounding", "Stretching or squashing", "Re-typesetting the wordmark", "Placing on the mosaic or on orange", "Repeating as a pattern or bullet"], interNote: "Also: below 3:1 contrast, with a robot, a glowing brain or an “AI” spark.",
    coulT: "Colours.", coulLead: "A single accent hue: signal orange. The rest is black, paper and grey.",
    brT: "The ember.", brLead: "A warm ramp, from the dissolving edge to the core. It is matter, never text.", brAutres: "Other ramps: one per product mock-up",
    typT: "Typefaces.", typLead: "Free and served locally. Three voices, not one more.", typRoles: ["Headings, weight 500", "Body text", "Technical labels"],
    hierT: "Hierarchy.", hierLead: "Few levels, large steps, headings never bold.", hierCols: ["Level", "Size", "Leading", "Tracking"],
    mosT: "The mosaic.", mosTxt: "A field of squares whose hue follows the ember ramp and that dissolves into pixels toward one edge, like an image being computed. Generated in code with a fixed seed: the same image at every render. Text never sits on it.",
    gT: "Grid, ruler and band.", gA: "Measuring grid", gAt: "Fine lines that fade toward the edges.", gB: "Graduated ruler", gBt: "A short tick, a taller one every eight.", gC: "Ember band", gCt: "Four flat bars: amber, orange, vermilion, raspberry.", gD: "Radii from 2 to 12 px, no pills, no decorative shadows, 1 px rules.",
    monT: "The visual world: the ember.", monTxt: "Québec night, matter made of light, pixels becoming worlds. Signal orange against deep black and midnight blue. Cinematic, never “stock”. One idea per image, one focal point.", monNon: "Never: a robot, a glowing brain, an “AI” spark, a neon blue chip, robotic hands, archive photos, fake clients. No text inside a generated image: type is set in code.", monCap: ["Aurora over the boreal forest", "City at dusk", "The workshop where light makes things"],
    tonT: "Tone of voice.", tonLead: "Precise, calm, direct. We promise little and say so plainly.",
    tonRegles: ["Short sentences. One verb, one idea.", "French uses the formal “vous”, always.", "No figure, price, date, statistic or certification we cannot prove.", "A tool not yet shipped is “Soon” or “Later”, never in the present tense.", "No “best”, no “number one”, no guarantee."],
    tonOui: "Yes", tonNon: "No", tonExOui: ["AI that works for your business. Under your control.", "Your data stays with you or in Quebec.", "We only announce what we can deliver."], tonExNon: ["Revolutionize your business with the ultimate AI!", "The best AI on the market, guaranteed.", "Coming soon, 100% secure."],
    appT: "Print.", appLead: "Same grid, same margins, same matter: a piece is recognized from three metres.", appCap: ["Business card, front", "Business card, back", "Letterhead", "DL envelope", "Thank-you card"],
    affT: "Posters.", affLead: "A short title, one focal point, large breaths of black.",
    famT: "The tool family.", famLead: "One account, shared credits, every tool. Each tool shows its real status.", famNote: "The symbol is followed by the product name, in Geist 500: the logo itself is never modified.",
    filT: "Kit files.", filLead: "Everything regenerates by command from the sources.",
    fil: [["identite/final/logos/", "Logos: official SVG, PNG from 256 to 4096 px, vector PDF"], ["identite/final/profils/", "Profile pictures, 1080 px"], ["identite/final/verrouillages/", "Product lockups: SVG and PNG"], ["identite/final/icones/", "App icons and 1024 banner"], ["imprimes/final/", "Cards, stationery, posters, brochures, trade show, presentation"], ["identite/sources/", "Template engine, fonts, generation scripts"]],
    finT: "Dream big.\nStay in control.", finL: "Let’s talk",
    entete: "Nexora AI · Brand kit", etat: "Status", etats: TEXTE.en.etats,
  },
};

function pages(l) {
  const t = L[l], TOT = 21; let n = 0;
  const lang = l;
  const chrome = (theme, section, body, opts = {}) => {
    n++;
    const logo = theme === "sombre" ? M.logo("sombre", "") : M.logo("clair", "");
    return `<section class="p ${theme}">${opts.sansRails ? "" : `<div class="rail" style="left:96px"><i></i></div><div class="rail" style="right:96px"><i style="left:auto;right:-5px"></i></div>`}
<div class="tete lab"><span>${t.entete}</span><span>${section}</span></div>${body}
<div class="pied lab"><span>${logo}</span><span>${String(n).padStart(2, "0")} / ${TOT}</span></div></section>`;
  };
  const P = [];
  // 1 couverture
  n++;
  P.push(`<section class="p sombre"><div class="grille" style="--pas:80px;--e:1px;--g:rgba(245,244,239,.06);--masque:linear-gradient(to right,#000,transparent 70%)"></div>
${M.mosaique({ cols: 48, rows: 27, seed: 44, vers: "right", fade: 0.97, gap: 0.09, keep: (k) => k.col >= 27, ancre: "xMaxYMid" })}
<div class="abs" style="left:96px;top:90px;width:420px">${M.logo("sombre", "")}</div>
<div class="abs lab acc" style="left:96px;top:380px">${t.version}</div>
<h1 class="abs" style="left:96px;top:440px;font-size:132px;line-height:1">${t.kit}<br>Nexora AI.</h1>
<div class="abs lead" style="left:96px;top:790px;width:760px;color:var(--gris);font-size:24px">${esc(t.sousCouv)}</div>
<div class="abs bande-x" style="left:0;right:0;bottom:0;height:20px"></div></section>`);
  // 2 sommaire
  P.push(chrome("clair", "00", `<h2 class="abs" style="left:160px;top:170px">${t.sommaireT}</h2>
<div class="abs" style="left:160px;right:160px;top:340px;display:grid;grid-template-columns:repeat(3,1fr);gap:0 56px;grid-auto-flow:column;grid-template-rows:repeat(6,auto)">${t.sommaire.map((s, i) => `<div class="filet" style="padding:15px 0 14px;display:flex;gap:22px;align-items:baseline"><span class="lab acc">${String(i + 3).padStart(2, "0")}</span><span style="font-family:Geist;font-weight:500;font-size:27px;letter-spacing:-.02em">${s}</span></div>`).join("")}</div>`));
  // 3 nom et signature
  P.push(chrome("creme", `01 · ${t.nomT.replace(".", "")}`, `<h1 class="abs" style="left:160px;top:160px;font-size:150px">Nexora AI</h1>
<div class="abs" style="left:160px;top:380px;width:760px">${t.nomTxt.map((s) => `<p class="txt filet" style="padding:18px 0 20px">${esc(s)}</p>`).join("")}</div>
<div class="abs" style="left:1040px;top:200px;width:720px">
<div class="lab acc">${t.sigT}</div><h2 style="margin-top:16px;font-size:50px">${esc(t.signature)}</h2>
<div class="lab acc" style="margin-top:56px">${t.campagneT}</div><h2 style="margin-top:16px;font-size:50px">${esc(t.campagne)}</h2>
<div class="lab acc" style="margin-top:56px">${t.quebecT}</div><h2 style="margin-top:16px;font-size:50px">${esc(t.quebec)}</h2></div>`));
  // 4 logo
  P.push(chrome("clair", "02 · Logo", `<div class="grille" style="--pas:80px;--e:1px;--g:rgba(18,18,24,.06)"></div>
<div class="abs" style="left:160px;top:230px;width:1000px">${M.logo("clair", "")}</div>
<h2 class="abs" style="left:160px;top:520px">${t.logoT}</h2><p class="abs lead" style="left:160px;top:620px;width:1000px">${esc(t.logoTxt)}</p>
<div class="abs cadre" style="left:1300px;top:230px;width:420px;height:420px;display:flex;align-items:center;justify-content:center;background:var(--noir)">${M.symbole("sombre", "", "width:200px;height:200px")}</div>
<div class="abs lab" style="left:1300px;top:670px;color:var(--sec)">Symbol · 64 u</div>`));
  // 5 construction
  const U = 8; // px par unité
  const sym = M.symboleBrut("sombre").trim().replace(/^<svg[^>]*>/, "").replace(/<\/svg>$/, "");
  const cons = (() => {
    const zoom = 9.4, o = 6 - 10.4; // origine du dessin
    const cells = []; for (let i = 0; i <= 5; i++) cells.push(`<line x1="${6 + i * 10.4}" y1="6" x2="${6 + i * 10.4}" y2="58" stroke="#8A8A98" stroke-width=".18" stroke-dasharray=".6 .5"/><line x1="6" y1="${6 + i * 10.4}" x2="58" y2="${6 + i * 10.4}" stroke="#8A8A98" stroke-width=".18" stroke-dasharray=".6 .5"/>`);
    return `<svg viewBox="${o - 2} ${o - 2} ${52 + 2 * 12.4} ${52 + 2 * 12.4}" style="width:${(52 + 24.8) * zoom}px;height:${(52 + 24.8) * zoom}px"><rect x="${6 - 10.4}" y="${6 - 10.4}" width="${52 + 20.8}" height="${52 + 20.8}" fill="none" stroke="#FF7A45" stroke-width=".3" stroke-dasharray="1.2 .8"/>${sym}${cells.join("")}
<g font-family="JetBrains Mono" font-size="2.2" fill="#FF7A45"><text x="${6 - 10.4}" y="${6 - 10.4 - 1.2}">x = 10,4</text></g>
<rect x="${6 - 10.4}" y="28" width="10.4" height="8" fill="#FF7A45" opacity=".18"/><rect x="58" y="28" width="10.4" height="8" fill="#FF7A45" opacity=".18"/><rect x="26" y="${6 - 10.4}" width="12" height="10.4" fill="#FF7A45" opacity=".18"/><rect x="26" y="58" width="12" height="10.4" fill="#FF7A45" opacity=".18"/></svg>`;
  })();
  P.push(chrome("sombre", "03 · " + t.consT.replace(".", ""), `<div class="abs" style="left:150px;top:140px">${cons}</div>
<div class="abs" style="left:1000px;top:170px;width:760px"><h2>${t.consT}</h2><div style="margin-top:28px">${t.consTxt.map((s) => `<p class="txt filet" style="padding:15px 0 17px;font-size:20px">${esc(s)}</p>`).join("")}</div>
<div class="lab acc" style="margin-top:28px">${t.zoneT}</div><p class="txt" style="margin-top:10px;font-size:20px">${esc(t.zoneTxt)}</p></div>`));
  // 6 versions
  const tile = (bg, inner, cap, border = true) => `<div><div class="${border ? "cadre" : ""}" style="height:300px;background:${bg};display:flex;align-items:center;justify-content:center;position:relative">${inner}</div><div class="lab" style="margin-top:14px;color:var(--sec)">${cap}</div></div>`;
  P.push(chrome("clair", "04 · " + t.versT.replace(".", ""), `<h2 class="abs" style="left:160px;top:150px">${t.versT}</h2><p class="abs lead" style="left:160px;top:240px;width:1100px">${t.versTxt}</p>
<div class="abs" style="left:160px;right:160px;top:340px;display:grid;grid-template-columns:repeat(4,1fr);gap:24px">
${tile("var(--papier)", M.logo("clair", "", "width:300px"), t.versCap[0])}${tile("var(--noir)", M.logo("sombre", "", "width:300px"), t.versCap[1])}${tile("var(--creme)", M.logo("noir", "", "width:300px"), t.versCap[2])}${tile("var(--orange)", M.logo("blanc", "", "width:300px"), t.versCap[3])}</div>
<div class="abs" style="left:160px;right:160px;top:720px;display:grid;grid-template-columns:repeat(4,1fr);gap:24px">
${["clair", "sombre", "noir", "blanc"].map((v, i) => `<div class="cadre" style="height:120px;background:${["var(--papier)", "var(--noir)", "var(--creme)", "var(--orange)"][i]};display:flex;align-items:center;justify-content:center">${M.symbole(v, "", "width:64px;height:64px")}</div>`).join("")}</div>
<p class="abs lab" style="left:160px;top:880px;color:var(--sec)">${t.versNote}</p>`));
  // 7 tailles minimales (réel : 110 px et 16 px)
  P.push(chrome("creme", "05 · " + t.minT.replace(".", ""), `<h2 class="abs" style="left:160px;top:150px">${t.minT}</h2><p class="abs lead" style="left:160px;top:240px">${t.minTxt}</p>
<div class="abs cadre" style="left:160px;top:360px;width:760px;height:420px;background:var(--papier)"><div class="abs" style="left:60px;top:110px">${M.logo("clair", "", "width:110px")}</div>
<div class="abs" style="left:60px;top:210px;width:110px;border-top:1px solid var(--encre)"></div><div class="abs lab" style="left:60px;top:226px;color:var(--encre)">110 px</div>
<div class="abs lab acc" style="left:60px;bottom:40px">${t.minLogo}</div><div class="abs txt" style="left:60px;bottom:10px;font-size:17px;white-space:nowrap">${t.minLogoV}</div></div>
<div class="abs cadre" style="left:1000px;top:360px;width:760px;height:420px;background:var(--papier)"><div class="abs" style="left:60px;top:110px">${M.symbole("clair", "", "width:16px;height:16px")}</div>
<div class="abs" style="left:60px;top:150px;width:16px;border-top:1px solid var(--encre)"></div><div class="abs lab" style="left:60px;top:166px;color:var(--encre)">16 px</div>
<div class="abs" style="left:240px;top:110px">${M.symbole("clair", "", "width:64px;height:64px")}</div><div class="abs lab" style="left:240px;top:190px;color:var(--encre)">64 px</div>
<div class="abs lab acc" style="left:60px;bottom:40px">${t.minSym}</div><div class="abs txt" style="left:60px;bottom:10px;font-size:17px">${t.minSymV}</div></div>`));
  // 8 usages interdits
  const symRaw = (v, st = "") => M.symbole(v, "", `width:150px;height:150px;${st}`);
  const faux = `<svg viewBox="6 6 52 52" style="width:150px;height:150px"><path fill="#F5F4EF" d="M6 6h10.4v52h-10.4zM47.6 6h10.4v52h-10.4z"/><path fill="#FF5A1F" d="M16.4 16.4h10.4v10.4h-10.4zM26.8 26.8h10.4v10.4h-10.4zM37.2 37.2h10.4v10.4h-10.4zM16.4 37.2h10.4v10.4h-10.4z"/></svg>`;
  const tuilesNon = [
    ["var(--papier)", symRaw("clair", "filter:hue-rotate(205deg) saturate(1.4)")],
    ["var(--noir)", symRaw("sombre", "filter:drop-shadow(0 0 22px #FF5A1F) drop-shadow(8px 10px 10px rgba(0,0,0,.8))")],
    ["var(--noir)", faux],
    ["var(--papier)", symRaw("clair", "transform:rotate(-14deg) skewX(-10deg)")],
    ["var(--papier)", symRaw("clair", "transform:scale(1.7,.62)")],
    ["var(--papier)", `<div style="display:flex;align-items:center;gap:14px">${M.symbole("clair", "", "width:70px;height:70px")}<span style="font-family:'Times New Roman',serif;font-style:italic;font-size:62px;color:#121218">Nexora Ai</span></div>`],
    ["var(--noir)", `<div class="abs" style="inset:0">${M.mosaique({ cols: 14, rows: 8, seed: 5, vers: "center", fade: 0.55, gap: 0.08 })}</div>${M.symbole("sombre", "", "width:130px;height:130px;position:relative")}`],
    ["var(--papier)", `<div style="display:grid;grid-template-columns:repeat(5,44px);gap:10px">${Array.from({ length: 15 }, () => M.symbole("clair", "", "width:44px;height:44px")).join("")}</div>`],
  ];
  P.push(chrome("clair", "06 · " + t.interT.replace(".", ""), `<h2 class="abs" style="left:160px;top:130px">${t.interT}</h2>
<div class="abs" style="left:160px;right:160px;top:250px;display:grid;grid-template-columns:repeat(4,1fr);gap:20px 22px">${tuilesNon.map(([bg, inner], i) => `<div><div class="cadre" style="height:250px;background:${bg};display:flex;align-items:center;justify-content:center;position:relative;overflow:hidden">${inner}<span class="non">× NON</span></div><div class="lab" style="margin-top:12px;color:var(--encre)">${t.inter[i]}</div></div>`).join("")}</div>
<p class="abs lab" style="left:160px;bottom:96px;color:var(--sec)">${t.interNote}</p>`));
  // 9 couleurs
  const coul = [["#0A0A0E", "Noir profond", "fond sombre", "#F5F4EF"], ["#121218", "Surface / encre", "cartes, texte clair", "#F5F4EF"], ["#FBFBF8", "Papier", "fond clair", "#121218"], ["#F3F2EC", "Crème", "fond alterné", "#121218"], ["#F5F4EF", "Texte clair", "17,9:1 sur noir", "#121218"], ["#A8A8B6", "Gris", "8,4:1 sur noir", "#0A0A0E"], ["#FF5A1F", "Orange signal", "l’accent · texte noir dessus", "#0A0A0E"], ["#FF7A45", "Accent texte, sombre", "7,6:1 sur noir", "#0A0A0E"], ["#B53A0A", "Accent texte, clair", "5,7:1 sur papier", "#FFFFFF"], ["#11112A", "Bande nuit", "16,8:1 pour le texte", "#F5F4EF"]];
  const coulEn = { "Noir profond": "Deep black", "Surface / encre": "Surface / ink", Papier: "Paper", "Crème": "Cream", "Texte clair": "Light text", Gris: "Grey", "Orange signal": "Signal orange", "Accent texte, sombre": "Accent text, dark", "Accent texte, clair": "Accent text, light", "Bande nuit": "Night band" };
  const roleEn = { "fond sombre": "dark background", "cartes, texte clair": "cards, light text", "fond clair": "light background", "fond alterné": "alternate background", "17,9:1 sur noir": "17.9:1 on black", "8,4:1 sur noir": "8.4:1 on black", "l’accent · texte noir dessus": "the accent · black text on it", "7,6:1 sur noir": "7.6:1 on black", "5,7:1 sur papier": "5.7:1 on paper", "16,8:1 pour le texte": "16.8:1 for text" };
  P.push(chrome("clair", "07 · " + t.coulT.replace(".", ""), `<h2 class="abs" style="left:160px;top:130px">${t.coulT}</h2><p class="abs lead" style="left:160px;top:215px;width:1200px;font-size:24px">${t.coulLead}</p>
<div class="abs" style="left:160px;right:160px;top:310px;display:grid;grid-template-columns:repeat(5,1fr);gap:16px">${coul.map(([hex, nom, role, fg], i) => `<div class="chip" style="height:${i === 6 ? "auto" : "330px"};background:${hex};color:${fg};border-color:rgba(18,18,24,.18);${i === 6 ? "grid-row:span 2;grid-column:3" : ""}"><b>${l === "en" ? coulEn[nom] : nom}</b><span>${hex}</span><span style="opacity:.85;margin-top:4px;font-family:Inter;font-size:14px">${l === "en" ? roleEn[role] : role}</span></div>`).join("")}</div>`.replace(/grid-row:span 2;grid-column:3/, "grid-row:span 2")));
  // 10 braise
  P.push(chrome("sombre", "08 · " + t.brT.replace(".", ""), `<h2 class="abs" style="left:160px;top:130px">${t.brT}</h2><p class="abs lead" style="left:160px;top:215px;width:1100px;font-size:24px">${t.brLead}</p>
<div class="abs" style="left:160px;right:160px;top:330px;display:grid;grid-template-columns:repeat(6,1fr);gap:0">${C.braise.map((h, i) => `<div style="height:270px;background:${h};position:relative"><span class="lab" style="position:absolute;left:16px;bottom:14px;color:#0A0A0E;${i === 5 ? "color:#F5F4EF" : ""}">${h}</span></div>`).join("")}</div>
<div class="abs" style="left:160px;top:640px;width:760px;height:300px">${M.mosaique({ cols: 38, rows: 15, seed: 9, vers: "right", fade: 0.9, gap: 0.08, ancre: "xMaxYMid" })}</div>
<div class="abs" style="left:1000px;top:640px;right:160px"><div class="lab acc">${t.brAutres}</div>
<div style="margin-top:20px;display:grid;gap:12px">${["ciel", "or", "menthe", "nuit"].map((k) => `<div style="display:grid;grid-template-columns:repeat(6,1fr);height:40px;border:1px solid var(--ligne)">${PALETTES[k].map((h) => `<div style="background:${h}"></div>`).join("")}</div>`).join("")}</div></div>`));
  // 11 typographies
  const spec = (nom, famille, poids, ex, role, style = "") => `<div class="filet" style="padding-top:26px"><div class="lab acc">${role}</div><div style="font-family:${famille};font-weight:${poids};font-size:150px;line-height:1.05;letter-spacing:${famille === "Geist" ? "-.03em" : "0"};margin-top:10px">Aa</div>
<div style="font-family:Geist;font-weight:500;font-size:30px;margin-top:6px">${nom}</div><div style="font-family:${famille};font-weight:${poids};font-size:23px;line-height:1.35;margin-top:14px;color:var(--sec);${style}">${ex}</div></div>`;
  P.push(chrome("creme", "09 · " + t.typT.replace(".", ""), `<h2 class="abs" style="left:160px;top:130px">${t.typT}</h2><p class="abs lead" style="left:160px;top:215px;width:1100px;font-size:24px">${t.typLead}</p>
<div class="abs" style="left:160px;right:160px;top:330px;display:grid;grid-template-columns:repeat(3,1fr);gap:48px">
${spec("Geist 500", "Geist", 500, "Rêvez grand. Gardez le contrôle.", t.typRoles[0])}${spec("Inter 400", "Inter", 400, l === "fr" ? "L’IA qui travaille pour votre entreprise, sous votre contrôle, avec vos données." : "AI that works for your business, under your control, with your data.", t.typRoles[1])}${spec("JetBrains Mono 500", "'JetBrains Mono'", 500, "Nexora AI · État : Bientôt", t.typRoles[2], "text-transform:uppercase;letter-spacing:.06em")}</div>`));
  // 12 hiérarchie
  const niv = [["Affiche", "44–96 px", "1,0", "−0,03 em", 76], ["H1", "40–68 px", "1,04", "−0,028 em", 62], ["H2", "32–56 px", "1,08", "−0,024 em", 50], ["H3", "22–32 px", "1,18", "−0,018 em", 34], ["H4", "18 px", "1,35", "−0,01 em", 24], [l === "fr" ? "Chapeau" : "Lead", "18–21 px", "1,55", "0", 21], [l === "fr" ? "Texte" : "Body", "16 px", "1,6", "0", 18], [l === "fr" ? "Libellé" : "Label", "12 px", "1,4", "+0,06 em", 14]];
  P.push(chrome("clair", "10 · " + t.hierT.replace(".", ""), `<h2 class="abs" style="left:160px;top:130px">${t.hierT}</h2><p class="abs lead" style="left:160px;top:215px;width:1100px;font-size:24px">${t.hierLead}</p>
<div class="abs" style="left:160px;right:160px;top:310px"><div style="display:grid;grid-template-columns:1.9fr .7fr .5fr .6fr;padding-bottom:10px" class="lab acc"><span>${t.hierCols[0]}</span><span>${t.hierCols[1]}</span><span>${t.hierCols[2]}</span><span>${t.hierCols[3]}</span></div>
${niv.map(([a, b, c2, d, px], i) => `<div class="filet" style="display:grid;grid-template-columns:1.9fr .7fr .5fr .6fr;align-items:center;min-height:${Math.max(60, px + 24)}px;overflow:hidden"><span style="${i < 5 ? "font-family:Geist;font-weight:500;letter-spacing:-.025em" : i === 7 ? "font-family:'JetBrains Mono';text-transform:uppercase;letter-spacing:.06em;font-weight:500" : "font-family:Inter"};font-size:${px}px;line-height:1.1;white-space:nowrap">${a === "Affiche" && l === "en" ? "Poster" : a}</span><span class="lab">${b}</span><span class="lab">${c2}</span><span class="lab">${d}</span></div>`).join("")}</div>`));
  // 13 mosaïque
  P.push(chrome("sombre", "11 · " + t.mosT.replace(".", ""), `<div class="abs" style="left:0;top:0;right:0;bottom:0">${M.mosaique({ cols: 48, rows: 27, seed: 2, vers: "right", fade: 0.93, gap: 0.07, keep: (k) => k.col >= 23, ancre: "xMaxYMid" })}</div>
<div class="abs" style="left:160px;top:200px;width:720px"><h1 style="font-size:100px">${t.mosT}</h1><p class="lead" style="margin-top:34px;color:var(--gris);font-size:23px">${esc(t.mosTxt)}</p>
<p class="lab acc" style="margin-top:36px">seed 2 · 48 × 27 · gap .07 · braise</p></div>`, { sansRails: false }));
  // 14 grille / règle / bande
  P.push(chrome("clair", "12 · " + t.gT.replace(".", ""), `<h2 class="abs" style="left:160px;top:130px">${t.gT}</h2>
<div class="abs" style="left:160px;right:160px;top:290px;display:grid;grid-template-columns:repeat(3,1fr);gap:40px">
<div><div class="cadre" style="height:340px;background:var(--noir);position:relative;overflow:hidden"><div class="grille" style="--pas:56px;--e:2px;--g:rgba(245,244,239,.34);--masque:radial-gradient(70% 90% at 50% 45%,#000 25%,transparent 78%)"></div></div><div class="lab acc" style="margin-top:18px">${t.gA}</div><p class="txt" style="margin-top:6px;font-size:19px">${t.gAt}</p></div>
<div><div class="cadre" style="height:340px;background:var(--noir);position:relative;overflow:hidden"><div class="regle" style="position:absolute;left:30px;right:30px;bottom:110px;--pas:7px;--h:64px;--e:2px;--c:rgba(245,244,239,.9);--c2:rgba(245,244,239,.55)"></div></div><div class="lab acc" style="margin-top:18px">${t.gB}</div><p class="txt" style="margin-top:6px;font-size:19px">${t.gBt}</p></div>
<div><div class="cadre" style="height:340px;background:var(--noir);position:relative;overflow:hidden"><div class="bande" style="position:absolute;left:0;right:0;bottom:0;height:120px"></div></div><div class="lab acc" style="margin-top:18px">${t.gC}</div><p class="txt" style="margin-top:6px;font-size:19px">${t.gCt}</p></div></div>
<p class="abs lab" style="left:160px;bottom:96px;color:var(--sec)">${t.gD}</p>`));
  // 15 monde visuel
  P.push(chrome("sombre", "13 · " + (l === "fr" ? "Monde visuel" : "Visual world"), `<h2 class="abs" style="left:160px;top:120px;font-size:50px">${t.monT}</h2><p class="abs txt" style="left:160px;top:200px;width:820px;font-size:20px">${esc(t.monTxt)}</p><p class="abs txt acc" style="left:160px;top:330px;width:820px;font-size:18px">${esc(t.monNon)}</p>
<div class="abs" style="left:160px;right:160px;top:470px;display:grid;grid-template-columns:repeat(3,1fr);gap:20px">${[["aurore-hero-9x16", t.monCap[0], "50% 45%"], ["quebec-fleuve-9x16", t.monCap[1], "50% 66%"], ["creative-atelier-9x16", t.monCap[2], "50% 58%"]].map(([k, cap, pos]) => `<div><div style="height:470px;overflow:hidden;border:1px solid var(--ligne)"><img src="${jpgOuPng(k)}" style="width:100%;height:100%;object-fit:cover;object-position:${pos}"></div><div class="lab" style="margin-top:12px;color:var(--gris)">${cap}</div></div>`).join("")}</div>`));
  // 16 ton de voix
  P.push(chrome("creme", "14 · " + t.tonT.replace(".", ""), `<h2 class="abs" style="left:160px;top:130px">${t.tonT}</h2><p class="abs lead" style="left:160px;top:215px;width:900px;font-size:24px">${t.tonLead}</p>
<div class="abs" style="left:160px;top:330px;width:700px">${t.tonRegles.map((s, i) => `<div class="filet" style="padding:16px 0 17px;display:flex;gap:20px"><span class="lab acc">0${i + 1}</span><span style="font-size:22px;line-height:1.4">${esc(s)}</span></div>`).join("")}</div>
<div class="abs" style="left:1000px;right:160px;top:330px;display:grid;gap:14px">
${t.tonExOui.map((s) => `<div class="cadre" style="padding:20px 24px;background:var(--papier)"><div class="lab acc">${t.tonOui}</div><div style="font-family:Geist;font-weight:500;font-size:28px;letter-spacing:-.02em;margin-top:6px;line-height:1.15">${esc(s)}</div></div>`).join("")}
${t.tonExNon.map((s) => `<div class="cadre" style="padding:14px 24px;background:transparent;color:var(--sec)"><div class="lab" style="color:#B53A0A">${t.tonNon}</div><div style="font-size:20px;margin-top:4px;text-decoration:line-through;text-decoration-color:rgba(181,58,10,.5)">${esc(s)}</div></div>`).join("")}</div>`));
  // 17 imprimés
  const imgOk = (p) => (existe(p) ? img(p) : "");
  const cartes = join(IMP, "cartes", "personne-1"), pap = join(IMP, "papeterie");
  const pr = [[join(cartes, "carte-personne-1-recto.png"), "card"], [join(cartes, "carte-personne-1-verso-fr.png"), "card"], [join(pap, "papier-en-tete-lettre-fr.png"), "page"], [join(pap, "enveloppe-dl-dos.png"), "env"], [join(pap, "carte-remerciement-5x7-fr-recto.png"), "tall"]];
  P.push(chrome("clair", "15 · " + t.appT.replace(".", ""), `<h2 class="abs" style="left:160px;top:130px">${t.appT}</h2><p class="abs lead" style="left:160px;top:215px;width:1100px;font-size:24px">${t.appLead}</p>
<div class="abs" style="left:160px;right:160px;top:330px;height:600px;background:#E4E2D9"></div>
<img class="abs" src="${imgOk(pr[0][0])}" style="left:200px;top:384px;width:420px;box-shadow:0 14px 30px rgba(0,0,0,.18)"><img class="abs" src="${imgOk(pr[1][0])}" style="left:200px;top:640px;width:420px;box-shadow:0 14px 30px rgba(0,0,0,.18)">
<img class="abs" src="${imgOk(pr[2][0])}" style="left:700px;top:360px;height:540px;box-shadow:0 14px 30px rgba(0,0,0,.18)"><img class="abs" src="${imgOk(pr[4][0])}" style="left:1130px;top:384px;height:500px;box-shadow:0 14px 30px rgba(0,0,0,.18)">
<img class="abs" src="${imgOk(pr[3][0])}" style="left:1420px;top:560px;width:300px;box-shadow:0 14px 30px rgba(0,0,0,.18)">`));
  // 18 affiches
  const aff = ["heros/affiche-heros-" + l + "-18x24po.png", "famille/affiche-famille-" + l + "-18x24po.png", "quebec/affiche-quebec-" + l + "-18x24po.png", "typo/affiche-typo-" + l + "-18x24po.png", "creative/affiche-creative-" + l + "-18x24po.png"].map((p) => join(IMP, "affiches", p));
  P.push(chrome("sombre", "16 · " + t.affT.replace(".", ""), `<h2 class="abs" style="left:160px;top:120px">${t.affT}</h2><p class="abs lead" style="left:160px;top:205px;width:1100px;color:var(--gris);font-size:24px">${t.affLead}</p>
<div class="abs" style="left:160px;right:160px;top:300px;display:grid;grid-template-columns:repeat(5,1fr);gap:22px">${aff.map((p) => `<img src="${imgOk(p)}" style="width:100%;aspect-ratio:3/4;object-fit:cover;border:1px solid var(--ligne)">`).join("")}</div>`));
  // 19 famille d'outils
  P.push(chrome("clair", "17 · " + t.famT.replace(".", ""), `<h2 class="abs" style="left:160px;top:120px">${t.famT}</h2><p class="abs lead" style="left:160px;top:205px;width:1100px;font-size:24px">${t.famLead}</p>
<div class="abs cadre" style="left:160px;right:160px;top:300px;display:grid;grid-template-columns:repeat(2,1fr);gap:1px;background:var(--ligne)">${M.OUTILS.map((o) => {
    const f = join(ID, "final", "verrouillages", "svg-texte-editable", `nexora-${o.id}${l === "en" && o.nomEn !== o.nom ? "-en" : ""}-horizontal-clair.svg`);
    const svg = existe(f) ? require_(f) : "";
    return `<div style="background:var(--papier);padding:26px 32px;display:flex;justify-content:space-between;align-items:center;height:132px">${svg}<span class="lab" style="color:var(--encre);display:flex;align-items:center;gap:10px"><i style="display:inline-block;width:12px;height:12px;${o.etat === "disponible" ? "background:var(--orange)" : o.etat === "bientot" ? "background:var(--gris-sombre)" : "border:2px solid var(--gris-sombre)"}"></i>${t.etats[o.etat]}</span></div>`;
  }).join("")}</div><p class="abs lab" style="left:160px;bottom:96px;color:var(--sec)">${t.famNote}</p>`));
  // 20 fichiers
  P.push(chrome("creme", "18 · " + t.filT.replace(".", ""), `<h2 class="abs" style="left:160px;top:130px">${t.filT}</h2><p class="abs lead" style="left:160px;top:215px;width:1100px;font-size:24px">${t.filLead}</p>
<div class="abs" style="left:160px;right:160px;top:340px">${t.fil.map(([a, b]) => `<div class="filet" style="display:grid;grid-template-columns:620px 1fr;padding:22px 0"><span class="lab acc" style="font-size:16px">${a}</span><span style="font-size:23px">${b}</span></div>`).join("")}</div>`));
  // 21 fin
  n++;
  P.push(`<section class="p sombre"><div class="grille" style="--pas:80px;--e:1px;--g:rgba(245,244,239,.06);--masque:linear-gradient(to right,#000,transparent 70%)"></div>
${M.mosaique({ cols: 48, rows: 27, seed: 77, vers: "right", fade: 0.97, gap: 0.09, keep: (k) => k.col >= 30, ancre: "xMaxYMid" })}
<div class="abs lab acc" style="left:96px;top:150px">${t.finL}</div>
<h1 class="abs" style="left:96px;top:200px;font-size:118px">${t.finT.replace("\n", "<br>")}</h1>
<div class="abs txt" style="left:96px;top:620px;font-size:22px;color:var(--texte-clair);line-height:1.6">${[c.courriel_general, c.telephone, c.site, c.adresse].map(esc).join("<br>")}</div>
<div class="abs" style="left:96px;bottom:90px;width:380px">${M.logo("sombre", "")}</div><div class="abs bande-x" style="left:0;right:0;bottom:0;height:20px"></div></section>`);
  return P;
}
import { readFileSync } from "node:fs";
function require_(f) { return readFileSync(f, "utf8").replace(/<defs>.*?<\/defs>/s, "").replace(/ role="img" aria-label="[^"]*"/, ' aria-hidden="true"').replace("<svg ", `<svg style="height:56px;width:auto" `); }

for (const l of ["fr", "en"]) {
  const P = pages(l);
  console.log(l, "pages :", P.length);
  const doc = M.document_({ titre: `${L[l].kit} Nexora AI`, dossier: HTML, css: CSS, pages: P.join("\n"), lang: l });
  const f = join(HTML, `guide-${l}.html`); M.ecrire(f, doc);
  const nom = l === "fr" ? "kit-de-marque-nexora-ai-fr-CA" : "nexora-ai-brand-kit-en-CA";
  await M.rendre(nav, { fichierHtml: f, pdf: join(FINAL, `${nom}.pdf`), png: (i) => join(HTML, `g-${l}-${String(i + 1).padStart(2, "0")}.png`), dpi: 48, selecteur: ".p", largeurPx: 1920 });
}
await nav.close();
