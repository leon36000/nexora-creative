// Valide un EditPlan v1 par le validateur officiel du harnais (app/server/nexora/montage/editplan.ts).
// Usage : tsx valider-editplan.ts plan.json   → une ligne JSON {ok, erreurs, avertissements, duree_s}
import { readFileSync } from 'node:fs';
import { validerEditPlan, dureeTotaleS } from '../../../../../app/server/nexora/montage/editplan.ts';
const plan = JSON.parse(readFileSync(process.argv[2], 'utf8'));
const r = validerEditPlan(plan);
console.log(JSON.stringify({ ok: r.ok, erreurs: r.erreurs, avertissements: r.avertissements.slice(0, 12), duree_s: r.plan ? dureeTotaleS(r.plan) : null }));
