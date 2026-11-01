// Planche-contact identite/apercu.png
import { M, ID } from "./moteur.mjs";
import { join } from "node:path";
import { readdirSync } from "node:fs";
const F = join(ID, "final"), T = join(ID, "sources", "html");
const nav = await M.navigateur();
const ids = ["workstudio", "code", "rag", "bot", "creative", "webpilot", "privacy-router", "vps"];
const L = (n) => join(F, "logos", "png", n);
const images = [
  ...["sur-sombre", "sur-clair", "sur-creme"].map((k) => ({ fichier: L(`nexora-ai-logo-${k}-1024px.png`), nom: `logo ${k}` })),
  { fichier: L("nexora-ai-symbole-sur-sombre-1024px.png"), nom: "symbole sur sombre" },
  ...["noir", "orange-symbole-noir", "orange-symbole-blanc", "creme"].map((k) => ({ fichier: join(T, `_cercle-${k}.png`), nom: `profil ${k} (recadrage rond)` })),
  ...ids.map((i) => ({ fichier: join(F, "verrouillages", "png", `nexora-${i}-horizontal-sombre-2048px.png`), nom: `verrouillage ${i}` })),
  { fichier: join(F, "icones", "banniere-icone-1024.png"), nom: "bannière d’icône 1024" },
  { fichier: join(F, "icones", "icone-application-1024.png"), nom: "icône d’application 1024" },
  ...["01", "03", "05", "08", "10", "13"].map((n) => ({ fichier: join(T, "guide", `g-fr-${n}.png`), nom: `guide fr p.${n}` })),
  ...["01", "06"].map((n) => ({ fichier: join(T, "guide", `g-en-${n}.png`), nom: `guide en p.${n}` })),
];
await M.planche(nav, { images, sortie: join(ID, "apercu.png"), colonnes: 4, largeur: 2400, hauteurCase: 330, dossierTmp: T });
await nav.close();
