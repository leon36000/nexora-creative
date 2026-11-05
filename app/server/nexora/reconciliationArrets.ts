/** Un job « expired » ou inconnu peut encore tourner : il ne prouve pas la fin du calcul. */
export const statutTerminalConfirme = (statut: string): boolean => ['succeeded', 'failed', 'canceled', 'cancelled'].includes(statut);

/** Balayage borné et cyclique ; une requête réseau bloquée ne se multiplie pas à chaque cycle. */
export function creerVerificationArrets(
  lire: (apres: number, limite: number) => { id: number; prompt_id: string | null }[],
  etatTerminal: (promptId: string) => Promise<boolean>,
  confirmer: (id: number, promptId: string) => void,
  delaiMs = 5000,
): () => Promise<void> {
  let curseur = 0;
  const enCours = new Set<string>();
  return async () => {
    let lot = lire(curseur, 10);
    if (!lot.length && curseur) { curseur = 0; lot = lire(0, 10); }
    if (!lot.length) return;
    const recherches: Promise<void>[] = [];
    for (const prise of lot) {
      const prompt = prise.prompt_id;
      if (!prompt || enCours.has(prompt)) { curseur = prise.id; continue; }
      if (enCours.size >= 4) break;
      curseur = prise.id;
      enCours.add(prompt);
      const recherche = Promise.resolve().then(() => etatTerminal(prompt)).finally(() => enCours.delete(prompt));
      recherches.push((async () => {
        let timer: ReturnType<typeof setTimeout> | undefined;
        try {
          const termine = await Promise.race([recherche, new Promise<false>((resolve) => { timer = setTimeout(() => resolve(false), delaiMs); })]);
          if (termine) confirmer(prise.id, prompt);
        } catch { /* Pas de preuve : conserver l'état et la réservation. */ }
        finally { if (timer) clearTimeout(timer); }
      })());
    }
    await Promise.all(recherches);
  };
}
