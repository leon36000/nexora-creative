// bun construire.mjs [annonces banniere courriel og atterrissage] [--filtre texte]
import { rendre } from "../../social/sources/moteur/marque.mjs";
import { verifier } from "./textes.mjs";
const args = process.argv.slice(2);
const fi = args.indexOf("--filtre");
const filtre = fi >= 0 ? args.splice(fi, 2)[1] : null;
const err = verifier();
if (err.length) { console.log("LIMITES DÉPASSÉES", err); process.exit(1); }
const MODULES = { annonces: ["./annonces.mjs", "toutAnnonces"], banniere: ["./banniere.mjs", "toutBannieres"], og: ["./og.mjs", "toutOg"], courriel: ["./courriel.mjs", "toutCourriel"] };
const noms = args.length ? args : Object.keys(MODULES);
let pieces = [];
for (const n of noms) { if (!MODULES[n]) continue; const [f, fn] = MODULES[n]; const m = await import(f); pieces.push(...m[fn]()); }
if (filtre) pieces = pieces.filter((p) => p.id.includes(filtre) || p.htmlPath.includes(filtre));
console.log(`${pieces.length} pièces`);
const t = Date.now();
const r = await rendre(pieces, { conc: 5 });
console.log(`${r.ok} rendues en ${((Date.now() - t) / 1000).toFixed(0)} s`);
if (noms.includes("courriel")) { const m = await import("./courriel.mjs"); console.log(m.ecrireModeles().length, "modèles écrits"); }
for (const e of r.errors) console.log("ERREUR", e);
