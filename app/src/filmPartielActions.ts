/** Ouvre seulement une prise ou un film retrouvé après actualisation, sans relancer de travail. */
export async function ouvrirCiblePartielle(id: number, rafraichir: () => Promise<void>, existe: (id: number) => boolean, ouvrir: (id: number) => void): Promise<boolean> {
  if (!Number.isSafeInteger(id) || id <= 0) return false;
  await rafraichir();
  if (!existe(id)) return false;
  ouvrir(id);
  return true;
}

export const filmPartielAConsulter = (e: { filmId: number; conflit?: { filmId: number } }): number => e.conflit?.filmId ?? e.filmId;
