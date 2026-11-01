// Planche-contact imprimes/apercu.png
import { M, IM, ID } from "../../identite/sources/moteur.mjs";
import { join } from "node:path";
import { existsSync, readdirSync, mkdirSync } from "node:fs";
const F = join(IM, "final"), T = join(IM, "sources", "html", "apercu"); mkdirSync(T, { recursive: true });
const nav = await M.navigateur();
const ras = (pdf, nom, page = 1, dpi = 30) => { const p = join(T, nom); M.pdfVersPng(pdf, p, dpi); return readdirSync(T).filter((f) => f.startsWith(nom + "-")).sort().map((f) => join(T, f)); };
const images = [];
const add = (fichier, nom) => { if (existsSync(fichier)) images.push({ fichier, nom }); };
const C = join(F, "cartes", "personne-1");
for (const k of ["recto", "verso-fr", "verso-en", "verso-braise-fr"]) add(join(C, `carte-personne-1-${k}.png`), `carte ${k}`);
const P = join(F, "papeterie");
for (const k of ["papier-en-tete-lettre-fr.png", "facture-soumission-lettre-fr.png", "enveloppe-dl-face.png", "enveloppe-dl-dos.png", "carte-remerciement-5x7-fr-recto.png", "carte-remerciement-5x7-fr-verso.png", "etiquette-expedition-4x6.png", "signature-courriel/signature-personne-1-fr.png"]) add(join(P, k), k.replace(".png", ""));
for (const id of ["heros", "famille", "quebec", "typo", "creative", "code", "workstudio"]) add(join(F, "affiches", id, `affiche-${id}-fr-24x36po.png`), `affiche ${id}`);
for (const f of ["depliant-3-volets-lettre-fr-ecran", "depliant-a5-plie-fr-ecran"]) { const pdf = join(F, "depliants", f + ".pdf"); if (existsSync(pdf)) for (const [i, p] of ras(pdf, f, 1, 40).entries()) images.push({ fichier: p, nom: `${f} p.${i + 1}` }); }
for (const id of ["workstudio", "creative", "privacy-router"]) add(join(F, "depliants", "fiches", `fiche-${id}-fr.png`), `fiche ${id}`);
const S = join(F, "salon");
for (const k of ["banniere-retractable-850x2000-fr.png", "fond-de-stand-3x2.4m-fr.png", "badge-4x3po-equipe.png", "badge-4x3po-visiteur.png", "signalisation-porte-bienvenue-lettre.png", "accroche-porte-3.5x8.5po-fr-recto.png"]) add(join(S, k), k.replace(".png", ""));
const D = join(IM, "sources", "html", "deck-controle");
if (existsSync(D)) for (const f of readdirSync(D).filter((x) => x.startsWith("deck-fr-")).sort().filter((_, i) => [0, 4, 8, 11].includes(i))) images.push({ fichier: join(D, f), nom: "présentation " + f.replace(".png", "") });
await M.planche(nav, { images, sortie: join(IM, "apercu.png"), colonnes: 6, largeur: 3000, hauteurCase: 420, dossierTmp: T });
await nav.close();
