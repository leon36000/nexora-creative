"""Exécution bornée : conserver les flux et signaler tout arrêt non confirmé."""
import shlex
import subprocess
import time
import uuid


def executer(cmd, timeout, journal):
    cmd = list(map(str, cmd))
    debut = time.monotonic()
    flux = journal.parent / 'flux-commandes'
    flux.mkdir(exist_ok=True)
    identifiant = uuid.uuid4().hex
    stdout = flux / (identifiant + '.stdout')
    stderr = flux / (identifiant + '.stderr')
    with stdout.open('xb') as sortie, stderr.open('xb') as erreurs:
        enfant = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=sortie, stderr=erreurs)
        try:
            code = enfant.wait(timeout=timeout)
            statut = 'status=' + str(code)
        except subprocess.TimeoutExpired:
            try:
                enfant.kill()
                enfant.wait(timeout=5)
                statut = 'status=timeout arret=confirme'
            except (OSError, subprocess.TimeoutExpired) as exc:
                statut = 'status=timeout arret=non_confirme raison=' + type(exc).__name__
            code = None
    duree = time.monotonic() - debut
    def instantane(path):
        with path.open('rb') as fichier:
            return fichier.read(path.stat().st_size).decode('utf-8', 'replace')
    out = instantane(stdout)
    err = instantane(stderr)
    with journal.open('a') as fichier:
        fichier.write('\n$ ' + shlex.join(cmd) + '\npid=' + str(enfant.pid)
                      + ' timeout_s=' + str(timeout) + ' stdout=' + str(stdout)
                      + ' stderr=' + str(stderr) + '\n' + out + '\n' + err + '\n'
                      + statut + ' sec=' + str(round(duree, 3)) + '\n')
    if code is None:
        raise RuntimeError(statut + ' ; enfant potentiellement vivant si arrêt non confirmé : pid=' + str(enfant.pid))
    if code:
        raise RuntimeError('Commande en échec : ' + shlex.join(cmd))
    return out, err, duree
