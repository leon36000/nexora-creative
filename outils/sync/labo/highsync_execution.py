"""Supervision locale d'un essai HighSync préparé ; usage R&D uniquement.

Aucun modèle téléchargé : toutes les entrées, sources et poids sont hachés.
La préparation et la revue de cet essai restent des étapes distinctes.
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

from outils.sync import valider_duree_av as av
from outils.sync.labo import highsync_patch, highsync_preflight, highsync_s3fd

GPU_LOCK_PC3 = Path('/opt/nexora-sync-rd-20261105/runs/active-gpu.lock')

SOURCE_MANIFEST_SHA256 = '2eb551aecf72851265ea19d30fc999249523e6eef53a9867488a85aa3dd1dbbc'

POIDS = {
    'reference': '66d63c15e6a0d431d6cb4489aa89957ff6e0af091dc25095525ddeeb5d1e10a5',
    'denoising': 'e557cfc841872f674abee31881db6052c7dd86a7fa197afc56bbdf29168efdc5',
    'whisper': '65147644a518d12f04e32d6f3b26facc3f8dd46e5390956a9424a650c0ce22b9',
    'vae': '1b4889b6b1d4ce7ae320a02dedaeff1780ad77d415ea0d744b476155c6377ddc',
    'vae_config': '92d3dfb746fca211a2c9e019e285f8597412211728dce3c5bcf4eda0f2d62e7e',
    'base_config': '2a50fbaa1c20bec4f6c4474e5594237640ad26ee7b10b5da1e921f303ba706a1',
}


def _ecrire(path: Path, data: bytes):
    with path.open('xb') as fichier:
        os.fchmod(fichier.fileno(), 0o600)
        fichier.write(data)


def _json_sans_doublon(paires):
    obj = {}
    for cle, valeur in paires:
        if cle in obj:
            raise ValueError('clé JSON dupliquée')
        obj[cle] = valeur
    return obj


def lire_json(path: Path):
    if path.is_symlink() or not path.is_file():
        raise ValueError('fichier JSON invalide')
    with path.open(encoding='utf-8') as f:
        return json.load(f, object_pairs_hook=_json_sans_doublon)


def verifier_gpu(info, processus, autorises, minimum_mib):
    """Vérifie snapshot fourni par nvidia-smi et identités déjà contrôlées."""
    if not isinstance(minimum_mib, int) or minimum_mib < 12288:
        raise ValueError('seuil mémoire insuffisant')
    if info['free_mib'] < minimum_mib or info['utilisation'] != 0:
        raise ValueError('GPU occupé ou mémoire insuffisante')
    if len({x['pid'] for x in processus}) != len(processus):
        raise ValueError('PID GPU dupliqué')
    if {str(x['pid']) for x in processus} != set(autorises):
        raise ValueError('processus GPU attendus absents ou supplémentaires')
    for process in processus:
        attendue = autorises.get(str(process['pid']))
        if attendue is None or any(process[k] != attendue[k] for k in ('uid', 'start', 'exe')):
            raise ValueError('processus GPU non autorisé ou identité modifiée')
        if not isinstance(attendue.get('max_mib'), int) or not 0 <= attendue['max_mib'] <= 512 or process['vram_mib'] > attendue['max_mib']:
            raise ValueError('processus GPU autorisé dépasse son plafond')


def identite(pid: int):
    base = Path('/proc') / str(pid)
    # Seules des métadonnées d'identité sont lues ; jamais /proc/PID/environ.
    text = (base / 'stat').read_text()
    fin = text.rfind(')')
    if fin < 0:
        raise ValueError('stat processus invalide')
    champs = text[fin+2:].split()
    uid = next(line for line in (base/'status').read_text().splitlines() if line.startswith('Uid:'))
    return {'pid': pid, 'start': int(champs[19]), 'uid': int(uid.split()[1]),
            'exe': os.readlink(base/'exe')}


def snapshot_gpu(nvidia_smi: Path, gpu_uuid: str):
    def query(args):
        result = subprocess.run([str(nvidia_smi), *args], stdin=subprocess.DEVNULL,
                                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                text=True, timeout=10, check=True)
        if len(result.stdout) > 65536:
            raise ValueError('réponse GPU excessive')
        return result.stdout.splitlines()
    rows = query(['--query-gpu=uuid,memory.total,memory.free,utilization.gpu', '--format=csv,noheader,nounits'])
    entries = [line.split(',') for line in rows]
    selected = [row for row in entries if len(row) == 4 and row[0].strip() == gpu_uuid]
    # Ce protocole vise pc3 à GPU unique ; ne pas extrapoler à une autre topologie.
    if len(entries) != 1 or len(selected) != 1:
        raise ValueError('GPU absent ou ambigu')
    row = selected[0]
    info = {'uuid': gpu_uuid, 'total_mib': int(row[1]), 'free_mib': int(row[2]), 'utilisation': int(row[3])}
    apps = query(['--query-compute-apps=gpu_uuid,pid,used_memory', '--format=csv,noheader,nounits'])
    processes = []
    for line in apps:
        cols = line.split(',')
        if len(cols) != 3:
            raise ValueError('réponse processus GPU invalide')
        if cols[0].strip() == gpu_uuid:
            item = identite(int(cols[1]))
            item['vram_mib'] = int(cols[2])
            processes.append(item)
    return info, processes


def verifier_sources(source: Path, manifest: Path):
    highsync_preflight._verifier_fichier(manifest, SOURCE_MANIFEST_SHA256)
    liste = lire_json(manifest)
    if liste.get('source_commit') != highsync_patch.SOURCE_COMMIT:
        raise ValueError('révision source inattendue')
    fichiers = liste.get('files')
    if not isinstance(fichiers, dict) or not fichiers:
        raise ValueError('manifeste source invalide')
    for nom, sha in fichiers.items():
        relatif = Path(nom)
        if relatif.is_absolute() or '..' in relatif.parts:
            raise ValueError('chemin source invalide')
        highsync_preflight._verifier_fichier(source / relatif, sha)
    return fichiers


def construire_runtime(run: Path, source: Path, source_manifest: Path, poids: dict):
    """Copie les sources épinglées et écrit une configuration locale neuve."""
    if run.is_symlink() or run.resolve() != run or not run.is_dir():
        raise ValueError('répertoire essai invalide')
    manifest = lire_json(run/'manifest.json')
    if manifest.get('statut') != 'prepare_sans_inference' or manifest.get('detector_backend') != 's3fd':
        raise ValueError('essai non préparé')
    for cle, attendu in POIDS.items():
        highsync_preflight._verifier_fichier(Path(poids[cle]), attendu)
    vae = Path(poids['vae'])
    vae_config = Path(poids['vae_config'])
    if vae.name != 'diffusion_pytorch_model.bin' or vae_config != vae.parent / 'config.json':
        raise ValueError('ensemble VAE incohérent')
    fichiers = verifier_sources(source, source_manifest)
    attendu = manifest['entrees']
    highsync_preflight._verifier_fichier(run/'video-entree.mp4', attendu['video_sha256'])
    highsync_preflight._verifier_fichier(run/'audio-entree.wav', attendu['audio_sha256'])
    for nom, champ in (('inference_adaptee.py','runner_sha256'), ('highsync_image_processor.py','image_processor_sha256'), ('highsync_s3fd.py','s3fd_adapter_sha256'), ('whisper_init_adapte.py','whisper_adapte_sha256')):
        highsync_preflight._verifier_fichier(run/nom, manifest[champ])
    runtime = run/'runtime'
    runtime.mkdir(mode=0o700)
    for nom, sha in fichiers.items():
        cible = runtime / nom
        cible.parent.mkdir(parents=True, exist_ok=True)
        if nom == 'src/models/whisper/whisper/__init__.py':
            data = (run/'whisper_init_adapte.py').read_bytes()
        else:
            data = (source/nom).read_bytes()
            if hashlib.sha256(data).hexdigest() != sha:
                raise ValueError('source modifiée pendant la copie')
        _ecrire(cible, data)
    for nom in ('inference_adaptee.py','highsync_image_processor.py','highsync_s3fd.py'):
        _ecrire(runtime/nom, (run/nom).read_bytes())
    dossier_base = runtime/'base'/'unet'
    dossier_base.mkdir(parents=True)
    _ecrire(dossier_base/'config.json', Path(poids['base_config']).read_bytes())
    # JSON est un sous-ensemble de YAML, lu par OmegaConf du runner.
    from omegaconf import OmegaConf
    cfg = OmegaConf.to_container(OmegaConf.load(str(runtime/'configs/inference/default.yaml')), resolve=True)
    cfg['base_model_path'] = str(runtime/'base')
    cfg['reference_unet_path'] = poids['reference']
    cfg['denoising_unet_path'] = poids['denoising']
    cfg['audio_model_path'] = poids['whisper']
    cfg['vae']['model_path'] = str(Path(poids['vae']).parent)
    cfg['save_path'] = str(run/'intermediaires')
    cfg['mask_path'] = str(runtime/'masks/mask_64.png')
    cfg['mask_512_path'] = str(runtime/'masks/mask_512.png')
    cfg['output'] = str(run/'sortie.mp4')
    cfg['source_video'] = str(run/'video-entree.mp4')
    cfg['driving_audio'] = str(run/'audio-entree.wav')
    _ecrire(run/'runtime-config.json', json.dumps(cfg, sort_keys=True, indent=2).encode())
    return runtime


def _memoire_disponible_mib():
    with open('/proc/meminfo', encoding='ascii') as fichier:
        for line in fichier:
            if line.startswith('MemAvailable:'):
                return int(line.split()[1]) // 1024
    raise ValueError('mémoire disponible inconnue')


def _hash(path: Path):
    return highsync_s3fd.empreinte(path)


def planifier(run: Path, source: Path, source_manifest: Path, poids: dict, options: dict):
    """Fige code, commandes et prévol ; n'exécute aucun modèle."""
    if options.get('cuda_fraction') != 0.60:
        raise ValueError('fraction CUDA non conforme au protocole')
    if options.get('min_ram_mib', 0) < 12288:
        raise ValueError('réserve RAM insuffisante')
    for cle in ('python', 'ffmpeg', 'ffprobe', 'nvidia_smi'):
        chemin = Path(options[cle])
        if not chemin.is_absolute() or not chemin.is_file() or not os.access(chemin, os.X_OK):
            raise ValueError('exécutable absent ou invalide : ' + cle)
    deps = Path(options['deps'])
    if not deps.is_absolute() or deps.is_symlink() or not deps.is_dir():
        raise ValueError('dépendances isolées absentes')
    modele_s3fd = Path(options['s3fd_poids'])
    if _hash(modele_s3fd) != highsync_s3fd.WEIGHT_SHA:
        raise ValueError('poids détecteur divergents')
    racine_s3fd = Path(options['s3fd_utils_root']) / 'face_detection/detection/sfd'
    for nom, attendu in highsync_s3fd.SOURCE_SHA.items():
        highsync_preflight._verifier_fichier(racine_s3fd/nom, attendu)
    origine = lire_json(run.parent/'provenance-audio.json')
    prep = lire_json(run/'manifest.json')
    if origine.get('essai') != run.name or origine.get('audio_pcm_sha256') != prep['entrees']['audio_sha256']:
        raise ValueError('filiation audio incohérente')
    highsync_preflight._verifier_fichier(run.parent/'audio-original.mp3', origine['audio_original_sha256'])
    evidence_path = Path(options['audio_provenance_path'])
    highsync_preflight._verifier_fichier(evidence_path, options['audio_provenance_sha256'])
    evidence = lire_json(evidence_path)
    correspondances = [a for a in evidence.get('assets', []) if a.get('sha256') == origine['audio_original_sha256'] and a.get('voice_id') == options['voice_id'] and a.get('model') == 'elevenlabs/eleven-v4']
    if evidence.get('requested_model') != 'elevenlabs/eleven-v4' or len(correspondances) != 1:
        raise ValueError('provenance audio demandée non établie')
    if _hash(Path(options['ffmpeg'])) != origine['ffmpeg_sha256']:
        raise ValueError('FFmpeg différent de la conversion audio')
    highsync_preflight.preflight(run/'video-entree.mp4', run/'audio-entree.wav',
        prep['entrees']['video_sha256'], prep['entrees']['audio_sha256'],
        Path(options['ffmpeg']), Path(options['ffprobe']))
    gpu, processus = snapshot_gpu(Path(options['nvidia_smi']), options['gpu_uuid'])
    verifier_gpu(gpu, processus, options['processus_autorises'], options['min_vram_mib'])
    ram = _memoire_disponible_mib()
    if ram < options['min_ram_mib']:
        raise ValueError('RAM disponible insuffisante')
    runtime = construire_runtime(run, source, source_manifest, poids)
    commande = [options['python'], str(runtime/'inference_adaptee.py'),
        '--config', str(run/'runtime-config.json'), '--source_video', str(run/'video-entree.mp4'),
        '--driving_audio', str(run/'audio-entree.wav'), '--output', str(run/'sortie.mp4'),
        '--ffmpeg', options['ffmpeg'], '--cuda-fraction', str(options['cuda_fraction']),
        '--s3fd-utils-root', options['s3fd_utils_root'], '--s3fd-poids', options['s3fd_poids']]
    runtime_hash = {}
    for chemin in sorted(runtime.rglob('*')):
        if chemin.is_symlink():
            raise ValueError('lien interdit dans le runtime')
        if chemin.is_file():
            runtime_hash[str(chemin.relative_to(runtime))] = _hash(chemin)
    plan = {'statut': 'planifie_sans_inference', 'commande': commande, 'options': options,
            'poids': poids, 'source': str(source), 'source_manifest': str(source_manifest),
            'runtime_sha256': runtime_hash, 'configuration_sha256': _hash(run/'runtime-config.json'),
            'preparation_sha256': _hash(run/'manifest.json'), 'provenance_sha256': _hash(run.parent/'provenance-audio.json'),
            'executables_sha256': {k: _hash(Path(options[k]).resolve()) for k in ('python','ffmpeg','ffprobe','nvidia_smi')},
            'prevol_gpu': gpu, 'prevol_processus': processus, 'prevol_ram_mib': ram,
            'allocateur_limite_estimee_mib': gpu['total_mib'] * options['cuda_fraction'],
            'memoire_auteur_gb': 10, 'avertissement': 'limite par processus conservatrice ; un OOM ne prouve pas une incompatibilité du modèle',
            'audio_modele_demande': 'elevenlabs/eleven-v4', 'audio_modele_effectivement_servi': 'non atteste'}
    _ecrire(run/'plan-execution.json', (json.dumps(plan, ensure_ascii=False, sort_keys=True, indent=2)+'\n').encode())
    return plan


def _arreter_enfant(process):
    if process.poll() is not None:
        return True
    try:
        process.terminate()
        process.wait(timeout=2)
        return True
    except (OSError, subprocess.TimeoutExpired):
        try:
            process.kill()
            process.wait(timeout=2)
            return True
        except (OSError, subprocess.TimeoutExpired):
            return False


def _vram_enfant(nvidia_smi: Path, pid: int, gpu_uuid: str):
    try:
        resultat = subprocess.run([str(nvidia_smi), '--query-compute-apps=gpu_uuid,pid,used_memory',
                                   '--format=csv,noheader,nounits'], stdin=subprocess.DEVNULL,
                                  stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                  text=True, timeout=5, check=True)
        for ligne in resultat.stdout.splitlines():
            cols = [x.strip() for x in ligne.split(',')]
            if len(cols) == 3 and cols[0] == gpu_uuid and int(cols[1]) == pid:
                return int(cols[2])
    except (OSError, ValueError, subprocess.SubprocessError):
        pass
    return None


def executer(run: Path, plan_sha256: str):
    """Exécute uniquement le plan relu identifié par SHA ; pas de reprise implicite."""
    if run.is_symlink() or not run.is_absolute() or run.resolve() != run or not run.is_dir():
        raise ValueError('répertoire essai invalide')
    plan_path = run/'plan-execution.json'
    highsync_preflight._verifier_fichier(plan_path, plan_sha256)
    plan = lire_json(plan_path)
    if plan.get('statut') != 'planifie_sans_inference':
        raise ValueError('plan invalide')
    opts, poids = plan['options'], plan['poids']
    runtime = run/'runtime'
    commande = [opts['python'], str(runtime/'inference_adaptee.py'),
        '--config', str(run/'runtime-config.json'), '--source_video', str(run/'video-entree.mp4'),
        '--driving_audio', str(run/'audio-entree.wav'), '--output', str(run/'sortie.mp4'),
        '--ffmpeg', opts['ffmpeg'], '--cuda-fraction', str(opts['cuda_fraction']),
        '--s3fd-utils-root', opts['s3fd_utils_root'], '--s3fd-poids', opts['s3fd_poids']]
    if plan['commande'] != commande or opts['cuda_fraction'] != 0.60:
        raise ValueError('commande ou fraction modifiée')
    if not isinstance(opts.get('delai_secondes'), int) or not 1 <= opts['delai_secondes'] <= 3600:
        raise ValueError('délai invalide')
    highsync_preflight._verifier_fichier(run/'manifest.json', plan['preparation_sha256'])
    highsync_preflight._verifier_fichier(run.parent/'provenance-audio.json', plan['provenance_sha256'])
    highsync_preflight._verifier_fichier(run/'runtime-config.json', plan['configuration_sha256'])
    prep = lire_json(run/'manifest.json')
    origine = lire_json(run.parent/'provenance-audio.json')
    highsync_preflight._verifier_fichier(run.parent/'audio-original.mp3', origine['audio_original_sha256'])
    highsync_preflight._verifier_fichier(Path(opts['audio_provenance_path']), opts['audio_provenance_sha256'])
    highsync_preflight.preflight(run/'video-entree.mp4', run/'audio-entree.wav',
        prep['entrees']['video_sha256'], prep['entrees']['audio_sha256'],
        Path(opts['ffmpeg']), Path(opts['ffprobe']))
    verifier_sources(Path(plan['source']), Path(plan['source_manifest']))
    for cle, attendu in POIDS.items():
        highsync_preflight._verifier_fichier(Path(poids[cle]), attendu)
    highsync_preflight._verifier_fichier(Path(opts['s3fd_poids']), highsync_s3fd.WEIGHT_SHA)
    for nom, attendu in highsync_s3fd.SOURCE_SHA.items():
        highsync_preflight._verifier_fichier(Path(opts['s3fd_utils_root'])/'face_detection/detection/sfd'/nom, attendu)
    for cle, attendu in plan['executables_sha256'].items():
        highsync_preflight._verifier_fichier(Path(opts[cle]).resolve(), attendu)
    fichiers = {str(x.relative_to(runtime)) for x in runtime.rglob('*') if x.is_file()}
    if fichiers != set(plan['runtime_sha256']) or any(x.is_symlink() for x in runtime.rglob('*')):
        raise ValueError('contenu runtime différent du plan')
    for nom, sha in plan['runtime_sha256'].items():
        highsync_preflight._verifier_fichier(runtime/nom, sha)
    if any(os.path.lexists(run/x) for x in ('sortie.mp4','intermediaires','execution.log','resultat-execution.json')):
        raise ValueError('traces d’exécution déjà présentes')
    gpu, processus = snapshot_gpu(Path(opts['nvidia_smi']), opts['gpu_uuid'])
    verifier_gpu(gpu, processus, opts['processus_autorises'], opts['min_vram_mib'])
    if _memoire_disponible_mib() < opts['min_ram_mib']:
        raise ValueError('RAM disponible insuffisante')
    verrou = run/'execution.lock'
    fd = os.open(verrou, os.O_CREAT|os.O_EXCL|os.O_WRONLY|os.O_NOFOLLOW, 0o600)
    active_fd = None
    process = None
    bilan = {'statut': 'echec', 'phase': 'avant_demarrage', 'plan_sha256': plan_sha256,
             'child_pid': None, 'arret_confirme': None, 'vram_echantillons_mib': []}
    try:
        fcntl.flock(fd, fcntl.LOCK_EX|fcntl.LOCK_NB)
        gpu_lock = Path(opts['gpu_lock'])
        if gpu_lock != GPU_LOCK_PC3:
            raise ValueError('verrou GPU commun invalide')
        active_fd = os.open(gpu_lock, os.O_RDWR|os.O_NOFOLLOW)
        lock_meta = os.fstat(active_fd)
        if not stat.S_ISREG(lock_meta.st_mode) or lock_meta.st_uid != os.getuid():
            raise ValueError('propriétaire ou type de verrou GPU invalide')
        fcntl.flock(active_fd, fcntl.LOCK_EX|fcntl.LOCK_NB)
        cache = run/'cache'; cache.mkdir(mode=0o700)
        env = {'PATH': str(Path(opts['ffmpeg']).parent)+':/usr/bin:/bin',
               'PYTHONPATH': str(runtime)+':'+opts['deps'], 'PYTHONDONTWRITEBYTECODE': '1',
               'CUDA_VISIBLE_DEVICES': opts['gpu_uuid'], 'HF_HUB_OFFLINE':'1',
               'TRANSFORMERS_OFFLINE':'1', 'TORCH_FORCE_WEIGHTS_ONLY_LOAD':'1',
               'HF_HOME':str(cache/'hf'), 'TRANSFORMERS_CACHE':str(cache/'transformers'),
               'TORCH_HOME':str(cache/'torch'), 'XDG_CACHE_HOME':str(cache/'xdg'),
               'IMAGEIO_FFMPEG_EXE':opts['ffmpeg'], 'TOKENIZERS_PARALLELISM':'false'}
        gpu, processus = snapshot_gpu(Path(opts['nvidia_smi']), opts['gpu_uuid'])
        verifier_gpu(gpu, processus, opts['processus_autorises'], opts['min_vram_mib'])
        with (run/'execution.log').open('xb') as log:
            os.fchmod(log.fileno(), 0o600)
            process = subprocess.Popen(commande, cwd=runtime, env=env, stdin=subprocess.DEVNULL,
                                       stdout=log, stderr=subprocess.STDOUT, pass_fds=(active_fd,))
            bilan.update(phase='inference_demarrée', child_pid=process.pid)
            _ecrire(run/'execution-pid.json', json.dumps({'pid':process.pid}).encode())
            debut = time.monotonic()
            while process.poll() is None:
                elapsed = time.monotonic()-debut
                if elapsed >= opts['delai_secondes']:
                    bilan['arret_confirme'] = _arreter_enfant(process)
                    bilan['phase'] = 'delai_depasse'
                    bilan['descendants_non_verifies'] = True
                    if not bilan['arret_confirme']:
                        _ecrire(run/'arret-non-confirme.json', json.dumps({'pid': process.pid}).encode())
                        # Conserver le verrou commun jusqu'à constater la fin de notre enfant.
                        while process.poll() is None:
                            time.sleep(2)
                        bilan['arret_confirme'] = True
                    break
                value = _vram_enfant(Path(opts['nvidia_smi']), process.pid, opts['gpu_uuid'])
                if value is not None:
                    bilan['vram_echantillons_mib'].append(value)
                time.sleep(min(2, max(.01, opts['delai_secondes']-elapsed)))
            bilan['duree_secondes'] = time.monotonic()-debut
            bilan['code_enfant'] = process.poll()
        if bilan['phase'] == 'delai_depasse':
            return bilan
        bilan['arret_confirme'] = process.poll() is not None
        if process.returncode != 0:
            bilan['phase'] = 'inference_echouee'
            return bilan
        bilan['phase'] = 'validation_av'
        resultat = av.valider(run/'audio-entree.wav', run/'sortie.mp4',
                             Path(opts['ffmpeg']), Path(opts['ffprobe']), .08, cadence_cible='25')
        bilan['validation_av'] = resultat
        if resultat['valide']:
            bilan.update(statut='av_valide_non_jugé', phase='termine', sortie_sha256=_hash(run/'sortie.mp4'))
        return bilan
    except Exception:
        if process is not None and process.poll() is None:
            bilan['arret_confirme'] = _arreter_enfant(process)
            bilan['descendants_non_verifies'] = True
            if not bilan['arret_confirme']:
                _ecrire(run/'arret-non-confirme.json', json.dumps({'pid': process.pid}).encode())
                while process.poll() is None:
                    time.sleep(2)
                bilan['arret_confirme'] = True
        raise
    finally:
        if bilan['vram_echantillons_mib']:
            bilan['vram_max_observe_mib'] = max(bilan['vram_echantillons_mib'])
        _ecrire(run/'resultat-execution.json', (json.dumps(bilan, ensure_ascii=False, indent=2)+'\n').encode())
        if active_fd is not None:
            os.close(active_fd)
        os.close(fd)


def main():
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    sous = p.add_subparsers(dest='phase', required=True)
    plan = sous.add_parser('plan')
    plan.add_argument('--run', type=Path, required=True)
    plan.add_argument('--source', type=Path, required=True)
    plan.add_argument('--source-manifest', type=Path, required=True)
    plan.add_argument('--poids-json', type=Path, required=True)
    plan.add_argument('--options-json', type=Path, required=True)
    lancement = sous.add_parser('executer')
    lancement.add_argument('--run', type=Path, required=True)
    lancement.add_argument('--plan-sha256', required=True)
    args = p.parse_args()
    try:
        if args.phase == 'plan':
            result = planifier(args.run, args.source, args.source_manifest,
                               lire_json(args.poids_json), lire_json(args.options_json))
            print(json.dumps({'statut':result['statut'], 'plan_sha256':_hash(args.run/'plan-execution.json')}, ensure_ascii=False))
            return 0
        result = executer(args.run, args.plan_sha256)
        print(json.dumps({'statut': result['statut'], 'phase': result['phase']}, ensure_ascii=False))
        return 0 if result['statut'] == 'av_valide_non_jugé' else 1
    except (ValueError, OSError, KeyError, subprocess.SubprocessError, av.ValidationErreur) as exc:
        print(json.dumps({'statut':'refuse_ou_echec', 'type':type(exc).__name__, 'erreur':str(exc)}, ensure_ascii=False))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
