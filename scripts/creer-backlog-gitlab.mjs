#!/usr/bin/env node
/**
 * Crée le backlog de la feuille de route maître dans GitLab (root/nexora-creative) depuis
 * docs/backlog/feuille-de-route-maitre.json : une issue par élément, puis les dépendances réécrites en #numéros, puis
 * l'issue de suivi « Feuille de route maître ». Idempotent : un titre déjà présent n'est pas recréé.
 * Jeton lu dans GITLAB_JETON (jamais affiché). Usage : GITLAB_JETON=… node scripts/creer-backlog-gitlab.mjs
 */
import { readFileSync, writeFileSync } from 'node:fs';

const BASE = process.env.GITLAB_URL ?? 'https://pc4.tail0c55ff.ts.net';
const PROJET = encodeURIComponent('root/nexora-creative');
const JETON = process.env.GITLAB_JETON;
if (!JETON) throw new Error('GITLAB_JETON manquant');
const items = JSON.parse(readFileSync(new URL('../docs/backlog/feuille-de-route-maitre.json', import.meta.url), 'utf8'));

async function api(methode, chemin, corps) {
  const r = await fetch(`${BASE}/api/v4/projects/${PROJET}${chemin}`, {
    method: methode,
    headers: { 'PRIVATE-TOKEN': JETON, 'content-type': 'application/json' },
    body: corps ? JSON.stringify(corps) : undefined,
  });
  if (!r.ok) throw new Error(`${methode} ${chemin} → HTTP ${r.status} ${(await r.text()).slice(0, 200)}`);
  return r.json();
}

const COULEURS = { vague: '#1f75cb', zone: '#6699cc', priorite: '#dc143c', agent: '#8e44ad' };
const etiquettes = (i) => [`vague::${i.vague}`, `zone::${i.zone}`, `priorite::${i.priorite}`, `agent::${i.agent}`];

async function main() {
  const existants = new Set((await api('GET', '/labels?per_page=100')).map((l) => l.name));
  for (const nom of new Set(items.flatMap(etiquettes).concat(['suivi']))) {
    if (existants.has(nom)) continue;
    await api('POST', '/labels', { name: nom, color: COULEURS[nom.split('::')[0]] ?? '#428bca' });
  }
  const deja = new Map();
  for (let page = 1; ; page++) {
    const l = await api('GET', `/issues?state=all&per_page=100&page=${page}`);
    l.forEach((x) => deja.set(x.title, x.iid));
    if (l.length < 100) break;
  }
  const corps = (i, numero) => [
    `**${i.cle}** · vague ${i.vague} · ${i.zone} · ${i.priorite} · estimation ${i.estimation} · agent ${i.agent}`,
    '', `**Contexte.** ${i.contexte}`, '', '**Critères d’acceptation**', ...i.criteres.map((c) => `- [ ] ${c}`), '',
    `**Dépendances** : ${i.dependances.length ? i.dependances.map((d) => (numero[d] ? `#${numero[d]} (${d})` : d)).join(', ') : 'aucune'}`,
    '', 'Source : `docs/FEUILLE-DE-ROUTE-MAITRE.md`.',
  ].join('\n');
  const numero = {};
  for (const i of items) {
    const titre = `[${i.cle}] ${i.titre}`;
    numero[i.cle] = deja.get(titre) ?? (await api('POST', '/issues', { title: titre, description: corps(i, {}), labels: etiquettes(i).join(',') })).iid;
  }
  for (const i of items) if (i.dependances.length) await api('PUT', `/issues/${numero[i.cle]}`, { description: corps(i, numero) });
  const titreSuivi = 'Feuille de route maître — Nexora Creative';
  const lignes = [1, 2, 3, 4, 5, 6, 7].flatMap((v) => [
    '', `### Vague ${v}`, ...items.filter((i) => i.vague === v).map((i) => `- [ ] #${numero[i.cle]} ${i.cle} ${i.titre} (${i.priorite}, ${i.agent}, ${i.estimation})`),
  ]);
  const suivi = [
    'Plan : `docs/FEUILLE-DE-ROUTE-MAITRE.md` (audit, vagues, spécifications de la bulle d’effet et du mode Marketing, définition de fini).',
    '', '**Livré en vague 1** : bulle « Effet IA ici… » v0 (clic droit clip et vide de piste, 26 recettes maison à 0 jeton, rôle LLM `effets`, Plus fort / Plus doux, Avant/Après, un seul Ctrl+Z).',
    ...lignes,
  ].join('\n');
  const iidSuivi = deja.get(titreSuivi)
    ? (await api('PUT', `/issues/${deja.get(titreSuivi)}`, { description: suivi })).iid
    : (await api('POST', '/issues', { title: titreSuivi, description: suivi, labels: 'suivi' })).iid;
  writeFileSync(new URL('../docs/backlog/numeros-gitlab.json', import.meta.url), JSON.stringify({ suivi: iidSuivi, ...numero }, null, 1) + '\n');
  console.log(`issues : ${Object.keys(numero).length} + suivi #${iidSuivi}`);
}
main().catch((e) => { console.error(e.message); process.exit(1); });
