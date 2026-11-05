/** Banc sans GPU : uniquement l'alias de production gemini de la passerelle locale déjà démarrée.
 * Usage depuis app : node_modules/.bin/tsx server/nexora/bench/liveAction.ts <résultat.json>
 * Seule la clé maître locale est lue, jamais journalisée. Aucun fichier de clés fournisseur n'est ouvert. */
import { readFileSync, writeFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';
import { realiser, verifierFiche, type EntreeRealisateur } from '../realisateur.js';
import { motsRenduInterdits, NEGATIF_LIVE_ACTION, verifierRecetteLiveAction } from '../liveAction.js';
import { validerPromptH3 } from '../promptH3.js';
import type { ClientLlm } from '../llm.js';

const demandes: (EntreeRealisateur & { id: string })[] = [
  { id: 'fr-dragon', intention: 'un gros dragon noir y passe au dessus du chateau pis y se pose su la tour, faut ca bouge', mode: 't2va', dureeS: 124 / 24, langueClient: 'fr' },
  { id: 'fr-espace', intention: '2 vaisseau y se chase en orbit dla terre pis un vire sec pour eviter lautre, pas des avions', mode: 't2va', dureeS: 124 / 24, langueClient: 'fr' },
  { id: 'fr-marques', intention: 'un jedi avec son lightsaber en duel sous pluie genre star wars mais pour vrai la', mode: 't2va', dureeS: 124 / 24, langueClient: 'fr' },
  { id: 'fr-poutine', intention: 'pub dla ptite cantine une poutine ben chaude le client tire le fromage pis y souri, ca donne faim', mode: 'i2va', dureeS: 243 / 24, langueClient: 'fr' },
  { id: 'fr-auto', intention: 'mon char rouge part du garage premiere photo pis y arrive su bord du fleuve derniere photo, roues qui tourne', mode: 'fl2va', dureeS: 243 / 24, langueClient: 'fr' },
  { id: 'fr-ref', intention: 'Mara en manteau vert y traverse une ruelle mouille pis y se retourne pour sourire', mode: 'ref2va', references: { sujets: [{ nom: 'Mara', apparence: 'a woman with short red hair and a green coat', images: 2 }] }, dureeS: 124 / 24, langueClient: 'fr' },
  { id: 'en-dragon', intention: 'huge dragon over castle swoops right past us then lands, epic cinematic glowing ultra-detailed 8K Unreal render pls', mode: 't2va', dureeS: 124 / 24, langueClient: 'en' },
  { id: 'en-space', intention: 'two original spaceships race above Earth then the nearer one banks hard, wanna see the scale', mode: 't2va', dureeS: 124 / 24, langueClient: 'en' },
  { id: 'en-brand', intention: 'coffee ad like Starbucks woman picks up hot cup then takes a sip and smiles no logo', mode: 't2va', dureeS: 124 / 24, langueClient: 'en' },
  { id: 'en-product', intention: 'animate this perfume pic, bottle stays same, camera moves closer while a drop slides down the glass', mode: 'i2va', dureeS: 124 / 24, langueClient: 'en' },
  { id: 'en-last', intention: 'runner sprints through puddles then stops exactly at the finish pose in the final photo', mode: 'l2va', dureeS: 243 / 24, langueClient: 'en' },
  { id: 'en-ref', intention: 'Mara opens the heavy wooden door then steps into sunlight, keep her face and green coat', mode: 'ref2va', references: { sujets: [{ nom: 'Mara', apparence: 'a woman with short red hair and a green coat', images: 2 }], composition: 1 }, dureeS: 124 / 24, langueClient: 'en' },
];

async function main() {
  const sortie = process.argv[2];
  if (!sortie) throw new Error('Indiquer un fichier résultat JSON.');
  const cle = readFileSync(join(homedir(), '.config/nexora-sous-agents/master.key'), 'utf8').trim();
  const resultats: Record<string, unknown>[] = [];
  let position = 0;
  async function travailleur() {
    while (position < demandes.length) {
      const d = demandes[position++];
      const debut = Date.now();
      const usage = { appels: 0, entree: 0, sortie: 0, modeles: [] as string[] };
      const llm: ClientLlm = { async completer(_role, messages, options) {
        usage.appels++;
        const reponse = await fetch('http://127.0.0.1:4410/v1/chat/completions', {
          method: 'POST', signal: AbortSignal.timeout(180_000),
          headers: { 'content-type': 'application/json', authorization: `Bearer ${cle}`, 'x-sa-run': 'nexora-live-action-12' },
          body: JSON.stringify({ model: 'eco-gemini', messages, temperature: options?.temperature, max_tokens: options?.maxTokens ?? 3000, response_format: { type: 'json_object' } }),
        });
        // Ne pas propager les corps d'erreur du fournisseur (ils pourraient contenir des informations de compte).
        if (!reponse.ok) throw new Error(`passerelle locale HTTP ${reponse.status}`);
        const j = await reponse.json() as any;
        usage.entree += j.usage?.prompt_tokens ?? 0;
        usage.sortie += j.usage?.completion_tokens ?? 0;
        if (j.model && !usage.modeles.includes(j.model)) usage.modeles.push(j.model);
        return j.choices?.[0]?.message?.content ?? '';
      } };
      let ligne: Record<string, unknown>;
      try {
        const r = await realiser({ ...d, moteur: 'h3-fast', format: '16:9' }, llm);
        const erreurs = [...verifierFiche(r.fiche, d), ...verifierRecetteLiveAction(r.prompt, d.intention),
          ...validerPromptH3(r.prompt, { ...d, dialogues: d.dialogues?.map((x) => x.texte) }), ...(!r.prompt.includes(NEGATIF_LIVE_ACTION) ? ['negative missing'] : [])];
        ligne = { id: d.id, entree: d, ok: erreurs.length === 0, erreurs, interdits: motsRenduInterdits(r.prompt), tentatives: r.tentatives, historique: r.historique, fiche: r.fiche, prompt: r.prompt, usage, ms: Date.now() - debut };
      } catch (e) {
        ligne = { id: d.id, entree: d, ok: false, erreurs: [e instanceof Error ? e.message : 'échec'], usage, ms: Date.now() - debut };
      }
      resultats.push(ligne);
      writeFileSync(sortie, JSON.stringify({ date: new Date().toISOString(), alias: 'gemini', route: 'eco-gemini', gpu: false, resultats }, null, 2) + '\n');
      console.log(`${d.id}: ${ligne.ok ? 'OK' : 'ÉCHEC'} (${usage.appels} appel(s), ${((Date.now() - debut) / 1000).toFixed(1)} s)`);
    }
  }
  await Promise.all([travailleur(), travailleur()]);
  console.log(`${resultats.filter((r) => r.ok).length}/${resultats.length} conformes`);
  if (resultats.some((r) => !r.ok)) process.exitCode = 1;
}

main().catch(() => { console.error('Banc indisponible : vérifier la passerelle et le fichier maître local.'); process.exitCode = 1; });
