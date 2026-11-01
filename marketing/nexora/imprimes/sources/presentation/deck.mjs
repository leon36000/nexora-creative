// Présentation PowerPoint Nexora AI : gabarit maître (6 dispositions) + 12 diapositives d'exemple, fr et en.
//   bun imprimes/sources/presentation/deck.mjs     (nécessite : bun add pptxgenjs ; voir LISEZMOI)
import pptxgen from "pptxgenjs";
import { M, IM, ID, lireCoordonnees, COORDONNEES, TEXTE } from "../../../identite/sources/moteur.mjs";
import { join } from "node:path";
import { existsSync, mkdirSync } from "node:fs";
import { execFileSync } from "node:child_process";

const A = join(IM, "sources", "presentation", "actifs"), GEN = join(IM, "sources", "generees");
const OUT = join(IM, "final", "presentation"); mkdirSync(OUT, { recursive: true });
const LG = (n) => join(ID, "final", "logos", "png", n);
const c = lireCoordonnees(COORDONNEES);
const GEIST = "Geist Medium", INTER = "Inter", MONO = "JetBrains Mono Medium";
const NOIR = "0A0A0E", SURF = "121218", PAPIER = "FBFBF8", CREME = "F3F2EC", CLAIR = "F5F4EF", GRIS = "A8A8B6", GRISS = "54545F", OR = "FF5A1F", ORS = "FF7A45", ORC = "B53A0A", ENC = "121218";
const BRAISE = ["FFB11A", "FF5A1F", "E0341C", "B01A3C"];

// images 16:9 rognées (PIL) pour les diapositives
function recadrer(src, dst, y0, y1, largeur = 2667) {
  if (existsSync(dst)) return;
  execFileSync("python3", ["-c", `
from PIL import Image
im=Image.open(r"${src}").convert("RGB"); w,h=im.size
a=int(h*${y0}); b=a+int(w*9/16)
im.crop((0,a,w,b)).resize((${largeur},int(${largeur}*9/16)),Image.LANCZOS).save(r"${dst}",quality=88)`]);
}
const gx = (n) => join(GEN, n);
recadrer(existsSync(gx("quebec-fleuve-9x16-x4.jpg")) ? gx("quebec-fleuve-9x16-x4.jpg") : gx("quebec-fleuve-9x16.png"), join(A, "img-quebec-16x9.jpg"), 0.30, 0.6);
const grand = ["aurore-large-16x9-x4.jpg", "aurore-large-16x9.png"].map(gx).find(existsSync);
if (grand) execFileSync("python3", ["-c", `from PIL import Image
im=Image.open(r"${grand}").convert("RGB"); im=im.resize((2667,int(2667*im.height/im.width)),Image.LANCZOS); im.save(r"${join(A, "img-aurore-16x9.jpg")}",quality=88)`]);

const D = {
  fr: {
    nom: "Nexora AI", label: "Présentation", lang: "fr-CA", t: TEXTE.fr,
    s: {
      titreLabel: "IA souveraine au Québec", titre: "Rêvez grand.\nGardez le contrôle.", sous: "Nexora AI : l’IA qui travaille pour votre entreprise.",
      citation1: TEXTE.fr.signature, attrib1: "Nexora AI",
      sec1: "Le principe", sec1n: "01", sec2: "Les outils", sec2n: "02",
      compteT: "Un seul compte pour toute la famille.", compte: ["Une connexion, un panneau « Mes outils », des crédits communs.", "Un compte, des crédits, tous les outils.", "Chaque outil affiche son état réel : livré, bientôt ou plus tard."],
      grilleT: "Huit outils, un compte.", grilleL: "La famille Nexora",
      imgT: "IA souveraine au Québec.", imgS: "Vos données restent chez vous ou au Québec.",
      donneesT: "Vos données restent chez vous.", donnees: ["Elles restent chez le client ou au Québec.", "Jamais utilisées pour entraîner un modèle.", "Privacy Router, incluse par défaut, contrôle ce qui sort."],
      wsT: "Nexora WorkStudio", wsL: "Disponible", wsN: "Livré et utilisable aujourd’hui.", ws: ["Des agents qui utilisent vos outils.", "Un Copilote qui prépare le flux, que vous relisez.", "Des réponses fondées sur vos documents."],
      vientT: "Ce qui vient, dit honnêtement.", vient: ["Nexora Code, RAG, Bot, WebPilot, Privacy Router et VPS au Québec : Bientôt.", "Nexora Creative : Plus tard.", "Aucune date n’est annoncée."],
      citation2: "Nous n’annonçons que ce que nous pouvons tenir.", attrib2: "Principe de la marque",
      finT: "Rêvez grand.\nGardez le contrôle.", finL: "Parlons-en",
    },
    notes: "Présentation d’exemple : remplacer le contenu, garder les dispositions du gabarit.",
  },
  en: {
    nom: "Nexora AI", label: "Presentation", lang: "en-CA", t: TEXTE.en,
    s: {
      titreLabel: "Sovereign AI, made in Québec", titre: "Dream big.\nStay in control.", sous: "Nexora AI: AI that works for your business.",
      citation1: TEXTE.en.signature, attrib1: "Nexora AI",
      sec1: "The principle", sec1n: "01", sec2: "The tools", sec2n: "02",
      compteT: "One account for the whole family.", compte: ["One sign-in, one “My tools” panel, shared credits.", "One account, shared credits, every tool.", "Each tool shows its real status: available, soon or later."],
      grilleT: "Eight tools, one account.", grilleL: "The Nexora family",
      imgT: "Sovereign AI, made in Québec.", imgS: "Your data stays with you or in Quebec.",
      donneesT: "Your data stays with you.", donnees: ["It stays with the client or in Quebec.", "Never used to train a model.", "Privacy Router, included by default, controls what leaves."],
      wsT: "Nexora WorkStudio", wsL: "Available", wsN: "Shipped and usable today.", ws: ["Agents that use your tools.", "A Copilot that drafts the workflow for you to review.", "Answers grounded in your documents."],
      vientT: "What is coming, said honestly.", vient: ["Nexora Code, RAG, Bot, WebPilot, Privacy Router and VPS in Quebec: Soon.", "Nexora Creative: Later.", "No date is announced."],
      citation2: "We only announce what we can deliver.", attrib2: "Brand principle",
      finT: "Dream big.\nStay in control.", finL: "Let’s talk",
    },
    notes: "Sample presentation: replace the content, keep the template layouts.",
  },
};

function fabriquer(l) {
  const d = D[l], s = d.s, pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE"; // 13,333 x 7,5 po (16:9)
  pres.title = `Nexora AI — ${d.label}`; pres.company = "Nexora AI"; pres.author = "Nexora AI"; pres.lang = d.lang;
  const W = 13.333, H = 7.5;
  const barre = (y) => BRAISE.map((col, i) => ({ rect: { x: (W / 4) * i, y, w: W / 4, h: 0.1, fill: { color: col }, line: { color: col, width: 0 } } }));
  const ph = (name, type, o) => ({ placeholder: { options: { name, type, margin: 0, align: "left", ...o }, text: "" } });

  pres.defineSlideMaster({ title: "TITRE", background: { color: NOIR }, objects: [
    { image: { path: join(A, "mosaique-titre.png"), x: W - 6.667, y: 0, w: 6.667, h: 7.5 } },
    { image: { path: LG("nexora-ai-logo-sombre-2048px.png"), x: 0.7, y: 0.6, w: 2.4, h: 2.4 * 52 / 285.55 } },
    ph("label", "body", { x: 0.7, y: 2.2, w: 5.6, h: 0.4, fontFace: MONO, fontSize: 11, color: ORS, charSpacing: 1.5 }),
    ph("titre", "title", { x: 0.7, y: 2.7, w: 6.6, h: 2.4, fontFace: GEIST, fontSize: 42, color: CLAIR, valign: "top", lineSpacingMultiple: 0.95, charSpacing: -1.4 }),
    ph("sous", "body", { x: 0.7, y: 5.4, w: 5.8, h: 0.9, fontFace: INTER, fontSize: 16, color: GRIS, valign: "top" }),
  ] });
  pres.defineSlideMaster({ title: "SECTION", background: { color: NOIR }, objects: [
    { image: { path: join(A, "mosaique-section.png"), x: 0, y: H - 2.5, w: W, h: 2.5 } },
    ph("numero", "body", { x: 0.7, y: 1.2, w: 3, h: 0.5, fontFace: MONO, fontSize: 14, color: ORS, charSpacing: 1.5 }),
    ph("titre", "title", { x: 0.7, y: 1.8, w: 10, h: 1.6, fontFace: GEIST, fontSize: 60, color: CLAIR, valign: "top", charSpacing: -1.8 }),
  ] });
  pres.defineSlideMaster({ title: "CONTENU", background: { color: PAPIER }, objects: [
    { image: { path: LG("nexora-ai-symbole-clair-256px.png"), x: 0.7, y: 0.5, w: 0.36, h: 0.36 } },
    ...barre(H - 0.1),
    ph("titre", "title", { x: 0.7, y: 1.2, w: 11.9, h: 1.2, fontFace: GEIST, fontSize: 38, color: ENC, valign: "top", charSpacing: -1.1 }),
    ph("etat", "body", { x: 0.7, y: 2.45, w: 8, h: 0.4, fontFace: MONO, fontSize: 11, color: ORC, charSpacing: 1.5 }),
    ph("corps", "body", { x: 0.7, y: 3.0, w: 8.4, h: 3.6, fontFace: INTER, fontSize: 24, color: ENC, valign: "top", lineSpacingMultiple: 1.25 }),
  ], slideNumber: { x: 12.0, y: 6.95, w: 0.7, h: 0.3, fontFace: MONO, fontSize: 9, color: GRISS, align: "right" } });
  pres.defineSlideMaster({ title: "CITATION", background: { color: CREME }, objects: [
    { rect: { x: 1.2, y: 1.3, w: 0.2, h: 0.2, fill: { color: OR }, line: { color: OR, width: 0 } } },
    ...barre(H - 0.1),
    ph("citation", "title", { x: 1.2, y: 1.9, w: 10.9, h: 3.3, fontFace: GEIST, fontSize: 48, color: ENC, valign: "top", lineSpacingMultiple: 1.0, charSpacing: -1.4 }),
    ph("attribution", "body", { x: 1.2, y: 5.7, w: 8, h: 0.4, fontFace: MONO, fontSize: 11, color: ORC, charSpacing: 1.5 }),
  ] });
  pres.defineSlideMaster({ title: "GRILLE", background: { color: NOIR }, objects: [
    ph("label", "body", { x: 0.7, y: 0.5, w: 8, h: 0.4, fontFace: MONO, fontSize: 11, color: ORS, charSpacing: 1.5 }),
    ph("titre", "title", { x: 0.7, y: 0.95, w: 11.9, h: 0.8, fontFace: GEIST, fontSize: 34, color: CLAIR, valign: "top", charSpacing: -1 }),
    ...barre(H - 0.1),
  ] });
  pres.defineSlideMaster({ title: "IMAGE", background: { color: NOIR }, objects: [
    ph("titre", "title", { x: 0.7, y: 0.7, w: 9, h: 1.0, fontFace: GEIST, fontSize: 44, color: CLAIR, valign: "top", charSpacing: -1.3 }),
    ph("sous", "body", { x: 0.7, y: 6.6, w: 9, h: 0.5, fontFace: INTER, fontSize: 16, color: CLAIR, valign: "top" }),
  ] });
  pres.defineSlideMaster({ title: "FIN", background: { color: NOIR }, objects: [
    { image: { path: join(A, "mosaique-fin.png"), x: W - 5.833, y: 0, w: 5.833, h: 7.5 } },
    { image: { path: LG("nexora-ai-logo-sombre-2048px.png"), x: 0.7, y: 6.3, w: 2.4, h: 2.4 * 52 / 285.55 } },
    ph("label", "body", { x: 0.7, y: 1.2, w: 5, h: 0.4, fontFace: MONO, fontSize: 11, color: ORS, charSpacing: 1.5 }),
    ph("titre", "title", { x: 0.7, y: 1.7, w: 7, h: 2.4, fontFace: GEIST, fontSize: 52, color: CLAIR, valign: "top", lineSpacingMultiple: 0.95, charSpacing: -1.5 }),
    ph("contact", "body", { x: 0.7, y: 4.3, w: 6, h: 1.6, fontFace: INTER, fontSize: 14, color: CLAIR, valign: "top" }),
  ] });

  const note = (sl) => sl.addNotes(d.notes);
  // 1 titre
  let sl = pres.addSlide({ masterName: "TITRE" }); sl.addText(s.titreLabel.toUpperCase(), { placeholder: "label" }); sl.addText(s.titre, { placeholder: "titre" }); sl.addText(s.sous, { placeholder: "sous" }); note(sl);
  // 2 citation
  sl = pres.addSlide({ masterName: "CITATION" }); sl.addText(s.citation1, { placeholder: "citation" }); sl.addText(s.attrib1.toUpperCase(), { placeholder: "attribution" }); note(sl);
  // 3 section 1
  sl = pres.addSlide({ masterName: "SECTION" }); sl.addText(s.sec1n, { placeholder: "numero" }); sl.addText(s.sec1, { placeholder: "titre" }); note(sl);
  // 4 contenu : un compte
  sl = pres.addSlide({ masterName: "CONTENU" }); sl.addText(s.compteT, { placeholder: "titre" }); sl.addText(s.compte.map((t) => ({ text: t, options: { bullet: { code: "25A0" }, breakLine: true, paraSpaceAfter: 10 } })), { placeholder: "corps" }); note(sl);
  // 5 grille des 8 outils
  sl = pres.addSlide({ masterName: "GRILLE" }); sl.addText(s.grilleL.toUpperCase(), { placeholder: "label" }); sl.addText(s.grilleT, { placeholder: "titre" });
  const cw = 2.9, ch = 2.35, gap = 0.07, x0 = 0.7, y0 = 2.0;
  M.OUTILS.forEach((o, i) => {
    const x = x0 + (i % 4) * (cw + gap), y = y0 + Math.floor(i / 4) * (ch + gap);
    sl.addShape("rect", { x, y, w: cw, h: ch, fill: { color: SURF }, line: { color: "3A3A44", width: 0.5 } });
    sl.addImage({ path: join(A, `pastille-${o.id}.png`), x: x + 0.28, y: y + 0.28, w: 0.55, h: 0.55 });
    sl.addText(l === "en" ? o.nomEn : o.nom, { x: x + 0.28, y: y + 1.0, w: cw - 0.5, h: 0.4, fontFace: GEIST, fontSize: 17, color: CLAIR, margin: 0, charSpacing: -0.5 });
    sl.addText(l === "en" ? o.tagEn : o.tag, { x: x + 0.28, y: y + 1.4, w: cw - 0.5, h: 0.35, fontFace: INTER, fontSize: 11, color: GRIS, margin: 0 });
    const col = o.etat === "disponible" ? OR : GRIS;
    sl.addShape("rect", { x: x + 0.28, y: y + 1.97, w: 0.1, h: 0.1, fill: o.etat === "plus_tard" ? { color: SURF } : { color: col }, line: { color: col, width: 0.75 } });
    sl.addText(d.t.etats[o.etat].toUpperCase(), { x: x + 0.47, y: y + 1.88, w: 1.8, h: 0.28, fontFace: MONO, fontSize: 9, color: CLAIR, margin: 0, charSpacing: 1 });
  });
  note(sl);
  // 6 image
  sl = pres.addSlide({ masterName: "IMAGE" });
  sl.background = { path: join(A, "img-quebec-16x9.jpg") };
  sl.addShape("rect", { x: 0, y: 0, w: 13.333, h: 1.9, fill: { color: NOIR, transparency: 55 }, line: { color: NOIR, width: 0, transparency: 100 } });
  sl.addShape("rect", { x: 0, y: 6.4, w: 13.333, h: 1.1, fill: { color: NOIR, transparency: 55 }, line: { color: NOIR, width: 0, transparency: 100 } });
  sl.addText(s.imgT, { placeholder: "titre" }); sl.addText(s.imgS, { placeholder: "sous" }); note(sl);
  // 7 contenu : données
  sl = pres.addSlide({ masterName: "CONTENU" }); sl.addText(s.donneesT, { placeholder: "titre" }); sl.addText(s.donnees.map((t) => ({ text: t, options: { bullet: { code: "25A0" }, breakLine: true, paraSpaceAfter: 10 } })), { placeholder: "corps" }); note(sl);
  // 8 section 2
  sl = pres.addSlide({ masterName: "SECTION" }); sl.addText(s.sec2n, { placeholder: "numero" }); sl.addText(s.sec2, { placeholder: "titre" }); note(sl);
  // 9 WorkStudio
  sl = pres.addSlide({ masterName: "CONTENU" }); sl.addText(s.wsT, { placeholder: "titre" }); sl.addText(`${d.t.etat.toUpperCase()} : ${s.wsL.toUpperCase()}`, { placeholder: "etat" });
  sl.addText(s.ws.map((t) => ({ text: t, options: { bullet: { code: "25A0" }, breakLine: true, paraSpaceAfter: 10 } })), { placeholder: "corps" });
  sl.addText(s.wsN, { x: 0.7, y: 6.35, w: 8, h: 0.4, fontFace: INTER, fontSize: 12, color: GRISS, margin: 0 }); note(sl);
  // 10 ce qui vient
  sl = pres.addSlide({ masterName: "CONTENU" }); sl.addText(s.vientT, { placeholder: "titre" }); sl.addText(s.vient.map((t) => ({ text: t, options: { bullet: { code: "25A0" }, breakLine: true, paraSpaceAfter: 10 } })), { placeholder: "corps" }); note(sl);
  // 11 citation 2
  sl = pres.addSlide({ masterName: "CITATION" }); sl.addText(s.citation2, { placeholder: "citation" }); sl.addText(s.attrib2.toUpperCase(), { placeholder: "attribution" }); note(sl);
  // 12 fin
  sl = pres.addSlide({ masterName: "FIN" }); sl.addText(s.finL.toUpperCase(), { placeholder: "label" }); sl.addText(s.finT, { placeholder: "titre" });
  sl.addText([{ text: c.courriel_general, options: { breakLine: true } }, { text: c.telephone, options: { breakLine: true } }, { text: c.site, options: { breakLine: true } }, { text: c.adresse }], { placeholder: "contact" }); note(sl);
  return pres;
}
for (const l of ["fr", "en"]) {
  const f = join(OUT, `presentation-nexora-ai-${l}.pptx`);
  await fabriquer(l).writeFile({ fileName: f });
  console.log(f);
}
