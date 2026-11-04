/** Produit les PDF d'échantillon de la vague 2 (entreprise fictive) : npx tsx scripts/marketing-echantillons.ts [sortie] [--cmjn] */
import { mkdirSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { KIT_EXEMPLE, TEXTE_EXEMPLE } from '../server/nexora/marketing/exemple.js';
import { construireSpec } from '../server/nexora/marketing/modeles.js';
import { fermerNavigateur, rendre } from '../server/nexora/marketing/rendu.js';

const sortie = process.argv[2] && !process.argv[2].startsWith('--') ? process.argv[2] : '../marketing/creative/echantillons-vague2';
const cmjn = process.argv.includes('--cmjn');
mkdirSync(sortie, { recursive: true });
const lot: [string, string, object][] = [
  ['carte-aplat', 'carte-affaires', TEXTE_EXEMPLE.carte], ['carte-filet', 'carte-affaires', TEXTE_EXEMPLE.carte], ['carte-bloc', 'carte-affaires', TEXTE_EXEMPLE.carte],
  ['flyer-bandeau', 'flyer-lettre', TEXTE_EXEMPLE.flyer], ['flyer-editorial', 'flyer-lettre', TEXTE_EXEMPLE.flyer], ['flyer-sombre', 'flyer-lettre', TEXTE_EXEMPLE.flyer],
  ['accroche-bande', 'accroche-porte', TEXTE_EXEMPLE.accroche], ['accroche-sobre', 'accroche-porte', TEXTE_EXEMPLE.accroche], ['accroche-arche', 'accroche-porte', TEXTE_EXEMPLE.accroche],
];
const only = process.argv.find((a) => a.startsWith('--seulement='))?.split('=')[1];
for (const [g, f, t] of lot) {
  if (only && g !== only) continue;
  const spec = construireSpec(g, f, KIT_EXEMPLE, t);
  const r = await rendre(spec, KIT_EXEMPLE, { cmjn });
  for (const p of r.pdfs) writeFileSync(join(sortie, `${g}-${p.variante}.pdf`), p.pdf);
  r.pngs.forEach((p) => writeFileSync(join(sortie, `${g}-${p.face}.png`), p.png));
  console.log(g, `${r.ms} ms`, `erreurs ${r.controle.erreurs}`, `avert. ${r.controle.avertissements}`, r.controle.constats.filter((c) => c.gravite !== 'info').map((c) => c.message).join(' | '));
}
await fermerNavigateur();
