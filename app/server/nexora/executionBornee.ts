import { spawn } from 'node:child_process';

/** Interrompt l'attente à l'échéance ; l'arrêt de l'enfant direct peut être refusé par l'OS. */
export function executerBorne(bin: string, args: string[], delaiMs: number): Promise<string> {
  if (!Number.isFinite(delaiMs) || delaiMs <= 0) throw new Error('Délai invalide.');
  return new Promise((resolve, reject) => {
    const enfant = spawn(bin, args, { stdio: ['ignore', 'pipe', 'ignore'] });
    let termine = false, taille = 0;
    const morceaux: Buffer[] = [];
    const finir = (err?: Error, sortie?: string) => {
      if (termine) return;
      termine = true; clearTimeout(minuterie);
      if (err) reject(err); else resolve(sortie ?? '');
    };
    const arreter = (raison: string) => {
      try { enfant.kill('SIGKILL'); } catch { /* arrêt non confirmé */ }
      enfant.stdout.destroy(); enfant.unref();
      finir(new Error(`${raison} ; arrêt de l’enfant non confirmé.`));
    };
    const minuterie = setTimeout(() => arreter('Délai dépassé'), delaiMs);
    enfant.stdout.on('data', (bloc: Buffer) => {
      if (termine) return;
      taille += bloc.length;
      if (taille > 1024 * 1024) { arreter('Sortie trop volumineuse'); return; }
      morceaux.push(bloc);
    });
    enfant.on('error', (e) => finir(e));
    enfant.on('close', (code, signal) => {
      if (code === 0) finir(undefined, Buffer.concat(morceaux).toString('utf8'));
      else finir(new Error(`Processus échoué (code ${code ?? 'absent'}, signal ${signal ?? 'absent'}).`));
    });
  });
}
