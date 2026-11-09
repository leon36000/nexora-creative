"""Essai LatentSync local et isolé ; aucun service produit n'est modifié.

Le préparateur reçoit des fichiers déjà présents, jamais des identifiants réseau.
Le plan est épinglé par SHA avant exécution. Les sorties restent des essais R&D,
même si leur validation audiovisuelle réussit.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import time
import urllib.request

from outils.sync import valider_duree_av as av
from outils.sync.labo import capsule_sync, highsync_preflight


def empreinte(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for bloc in iter(lambda: f.read(1048576), b''):
            h.update(bloc)
    return h.hexdigest()


def _objet(paires):
    if len({k for k, _ in paires}) != len(paires):
        raise ValueError('clé JSON dupliquée')
    return dict(paires)


def _lire(path: Path):
    capsule_sync._sans_echappement(path, 'JSON')
    return json.loads(path.read_text(), object_pairs_hook=_objet)


def _ecrire(path: Path, data):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write('\n')


def _arguments(c, run: Path):
    runtime = Path(c['runtime'])
    return ['--unet_config_path', str(runtime/'configs/unet/stage2_512.yaml'),
            '--inference_ckpt_path', c['unet'], '--vae_local_path', c['vae'],
            '--video_path', str(run/'video-entree.mp4'),
            '--audio_path', str(run/'audio-entree.wav'),
            '--video_out_path', str(run/'sortie.mp4'),
            '--inference_steps', '20', '--guidance_scale', '1',
            '--temp_dir', str(run/'intermediaires'), '--seed', '1247']


def _commande(c, run: Path, lock_fd: int, status_fd: int):
    return capsule_sync.construire(Path(c['runtime']), run, Path(c['python']),
        Path(c['runtime'])/'scripts/capsule_inference.py', _arguments(c, run),
        Path(c['ffmpeg']), c['gpu_uuid'], lock_fd, status_fd,
        Path(c.get('bwrap', '/usr/bin/bwrap')))


def _verifier(c, run: Path):
    _commande(c, run, 3, 4)  # Validation pure des chemins ; ces FDs ne sont pas ouverts.
    manifest_path = Path(c['runtime_manifest'])
    highsync_preflight._verifier_fichier(manifest_path, c['runtime_manifest_sha256'])
    manifest = _lire(manifest_path)
    runtime = Path(c['runtime'])
    if manifest['runtime'] != str(runtime):
        raise ValueError('racine runtime différente')
    files = manifest['runtime_sha256']
    if not isinstance(files, dict) or not files:
        raise ValueError('manifeste runtime vide')
    for nom, sha in files.items():
        rel = Path(nom)
        if rel.is_absolute() or '..' in rel.parts or not rel.parts:
            raise ValueError('chemin runtime invalide')
        highsync_preflight._verifier_fichier(runtime/rel, sha)
    if any(p.is_symlink() for p in runtime.rglob('*')) or {
        str(p.relative_to(runtime)) for p in runtime.rglob('*') if p.is_file()
    } != set(files):
        raise ValueError('contenu runtime différent')
    for nom in ('python', 'ffmpeg', 'ffprobe', 'bwrap', 'nvidia_smi'):
        path = Path(c[nom])
        capsule_sync._exe(path, nom, suivre_lien=True)
        highsync_preflight._verifier_fichier(path.resolve(), c['executables_sha256'][nom])
    if Path(c['ffmpeg']).parent != Path(c['ffprobe']).parent:
        raise ValueError('paire FFmpeg/FFprobe requise')
    for nom, sha in c['poids_sha256'].items():
        highsync_preflight._verifier_fichier(Path(nom), sha)
    for nom in ('unet',):
        if c[nom] not in c['poids_sha256']:
            raise ValueError('poids non épinglés')
    for nom in ('config.json', 'diffusion_pytorch_model.bin'):
        if str(Path(c['vae'])/nom) not in c['poids_sha256']:
            raise ValueError('VAE non épinglé')
    provenance = run/'provenance-entrees.json'
    highsync_preflight._verifier_fichier(provenance, c['provenance_sha256'])
    p = _lire(provenance)
    if p['modele_demande'] != 'elevenlabs/eleven-v4':
        raise ValueError('provenance Eleven4 requise')
    for nom in ('audio-original.mp3', 'audio-entree.wav', 'video-entree.mp4'):
        highsync_preflight._verifier_fichier(run/nom, p['fichiers'][nom])
    return highsync_preflight.preflight(run/'video-entree.mp4', run/'audio-entree.wav',
        p['fichiers']['video-entree.mp4'], p['fichiers']['audio-entree.wav'],
        Path(c['ffmpeg']), Path(c['ffprobe']))


def gpu(c):
    def requete(champ, option):
        p = subprocess.run([c['nvidia_smi'], f'--query-{option}={champ}',
            '--format=csv,noheader,nounits'], env={'PATH':'/usr/bin:/bin'},
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, check=True, text=True, timeout=10)
        if len(p.stdout) > 65536:
            raise ValueError('réponse GPU excessive')
        return [[x.strip() for x in ligne.split(',')] for ligne in p.stdout.splitlines()]
    rows = requete('uuid,memory.total,memory.free,utilization.gpu,power.limit', 'gpu')
    selected = [r for r in rows if len(r) == 5 and r[0] == c['gpu_uuid']]
    if len(selected) != 1:
        raise ValueError('GPU absent ou ambigu')
    r = selected[0]
    apps = requete('gpu_uuid,pid,used_memory', 'compute-apps')
    if any(len(a) != 3 for a in apps):
        raise ValueError('liste processus GPU illisible')
    return {'uuid': r[0], 'total_mib': int(r[1]), 'free_mib': int(r[2]),
            'utilisation': int(r[3]), 'power_limit_w': float(r[4]),
            'processus': [{'pid':int(a[1]), 'mib':int(a[2])}
                         for a in apps if a[0] == c['gpu_uuid']]}


def _gpu_initial(c):
    info = gpu(c)
    if info['processus'] or info['utilisation'] != 0 or info['free_mib'] < 24576:
        raise ValueError('GPU occupé ou moins de 24 Gio disponibles')
    return info


def _prevol(c):
    ram = next(int(l.split()[1])//1024 for l in Path('/proc/meminfo').read_text().splitlines()
               if l.startswith('MemAvailable:'))
    if ram < 12288:
        raise ValueError('moins de 12 Gio de RAM disponibles')
    queue = {'statut':'inconnue', 'endpoint':'http://127.0.0.1:18388/prompt'}
    try:
        # Aucun proxy ni identifiant du compte hôte transmis.
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(queue['endpoint'], timeout=2) as response:
            data = response.read(4097)
        if len(data) > 4096:
            raise ValueError('réponse de file excessive')
        n = json.loads(data)['exec_info']['queue_remaining']
        if isinstance(n,bool) or not isinstance(n,int) or n < 0:
            raise ValueError('nombre en file invalide')
        queue.update(statut='connue', taches=n)
    except (OSError,ValueError,KeyError,TypeError) as exc:
        queue['erreur'] = type(exc).__name__
    if queue.get('taches',0) != 0:
        raise ValueError('file ComfyUI locale occupée')
    return {'gpu':_gpu_initial(c), 'ram_disponible_mib':ram, 'file_locale':queue,
            'portee':'essai autonome ; autres files non attestées, verrou coopératif Nexora seulement'}


def planifier(c, run: Path):
    av_entree = _verifier(c, run)
    plan = {'statut':'planifie_sans_inference', 'configuration':c,
            'entrees_av': av_entree, 'prevol':_prevol(c),
            'voix_validee_humain':False, 'produit_livre':False}
    _ecrire(run/'plan-execution.json', plan)
    return empreinte(run/'plan-execution.json')


def executer(run: Path, plan_sha256: str):
    from outils.sync.labo.supervision_capsule import superviser
    plan_path = run/'plan-execution.json'
    highsync_preflight._verifier_fichier(plan_path, plan_sha256)
    plan = _lire(plan_path)
    if plan['statut'] != 'planifie_sans_inference':
        raise ValueError('plan non exécutable')
    c = plan['configuration']
    _verifier(c, run)
    if any(os.path.lexists(run/p) for p in ('sortie.mp4', 'intermediaires',
                   'execution.log', 'resultat-execution.json', 'validation-av.json')):
        raise ValueError('essai déjà exécuté ; créer un autre dossier')
    lock = Path(c['gpu_lock'])
    capsule_sync._sans_echappement(lock, 'verrou')
    capsule_sync._dossier(lock.parent, 'dossier du verrou', 0o700)
    fd = os.open(lock, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        m = os.fstat(fd)
        if not stat.S_ISREG(m.st_mode) or m.st_uid != os.getuid() or m.st_mode & 0o077:
            raise ValueError('verrou non privé')
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        for rel in ('cache/hf','cache/torch','cache/xdg','cache/mpl','tmp'):
            (run/rel).mkdir(parents=True, mode=0o700, exist_ok=True)
        prevol = _prevol(c)
        _ecrire(run/'prevol-lancement.json',prevol)
        initial = prevol['gpu']
        samples = []
        derniere_mesure = [-float('inf')]
        def controle(identite, pids):
            if time.monotonic()-derniere_mesure[0] < 1:
                return
            derniere_mesure[0] = time.monotonic()
            s = gpu(c)
            samples.append(s)
            if any(p['pid'] not in pids for p in s['processus']):
                raise RuntimeError('autre processus GPU apparu : arrêter notre essai')
            if sum(p['mib'] for p in s['processus']) > initial['total_mib']*.70:
                raise RuntimeError('mémoire de notre essai dépasse le seuil de surveillance')
        read_fd, write_fd = os.pipe()
        bilan = superviser(_commande(c, run, fd, write_fd), run,
            fd, read_fd, write_fd, 1200, controle)
        _ecrire(run/'surveillance-gpu.json', samples)
    finally:
        os.close(fd)
    resultat = {'plan_sha256':plan_sha256, 'supervision':bilan,
                'qualite_humaine':'non évaluée', 'statut':'echec_ou_non_verifie'}
    if bilan['statut'] == 'succès' and bilan['arret_confirmé'] is True:
        resultat['av'] = av.valider(run/'audio-entree.wav',run/'sortie.mp4',
            Path(c['ffmpeg']),Path(c['ffprobe']),.08,cadence_cible='25')
        resultat['sortie_sha256'] = empreinte(run/'sortie.mp4')
        resultat['statut'] = 'av_valide_non_juge' if resultat['av']['valide'] else 'av_refuse'
    _ecrire(run/'validation-av.json', resultat)
    return resultat


def main():
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('phase', choices=['plan','executer'])
    p.add_argument('--run', type=Path, required=True)
    p.add_argument('--configuration', type=Path)
    p.add_argument('--plan-sha256')
    a = p.parse_args()
    if a.phase == 'plan':
        print(json.dumps({'plan_sha256':planifier(_lire(a.configuration), a.run)}))
    else:
        r = executer(a.run, a.plan_sha256)
        print(json.dumps({'statut':r['statut']}))
        return 0 if r['statut'] == 'av_valide_non_juge' else 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
