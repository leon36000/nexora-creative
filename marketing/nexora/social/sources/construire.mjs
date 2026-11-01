// Point d'entrée : bun construire.mjs [famille ...] [--filtre texte]   (familles : fb ig li x yt tt chat fonds ; sans argument : tout)
import { rendre } from "./moteur/marque.mjs";
const args = process.argv.slice(2);
const fi = args.indexOf("--filtre");
const filtre = fi >= 0 ? args.splice(fi, 2)[1] : null;
const MODULES = { fb: ["./fb.mjs", "toutFacebook"], ig: ["./ig.mjs", "toutInstagram"], li: ["./li.mjs", "toutLinkedin"], x: ["./x.mjs", "toutX"], yt: ["./yt.mjs", "toutYoutube"], tt: ["./tt.mjs", "toutTiktok"], chat: ["./chat.mjs", "toutChat"], fonds: ["./fonds.mjs", "toutFonds"] };
const noms = args.length ? args : Object.keys(MODULES);
let pieces = [];
for (const n of noms) { const [f, fn] = MODULES[n]; const m = await import(f); pieces.push(...m[fn]()); }
if (filtre) pieces = pieces.filter((p) => p.id.includes(filtre) || p.htmlPath.includes(filtre));
console.log(`${pieces.length} pièces`);
const t = Date.now();
const r = await rendre(pieces, { conc: 5 });
console.log(`${r.ok} rendues en ${((Date.now() - t) / 1000).toFixed(0)} s`);
for (const e of r.errors) console.log("ERREUR", e);
if (noms.includes("li") && !filtre) { const { rendrePdf } = await import("./moteur/marque.mjs"); const { pdfsLinkedin } = await import("./li.mjs"); for (const p of pdfsLinkedin()) console.log("PDF", await rendrePdf(p)); }
