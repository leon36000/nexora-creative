"""Adaptation pure des sources LatentSync épinglées : aucun modèle exécuté.

Ce module produit des octets adaptés; il ne prépare ni ne lance un essai GPU.
L'intégrité des modèles, les chemins, le verrou et les résultats restent à contrôler
par un lanceur séparé. Les sources non reconnues sont refusées.
"""
from __future__ import annotations

import ast
import hashlib

SOURCE_COMMIT = 'a229c3948406bc2cf6eaf4873e662e70c6a04746'
SOURCES = {
    'scripts/inference.py': '0c719555a4d2566237d7e768a5111dc0d61457a0676eb02acf16ee05bf8c91f5',
    'latentsync/pipelines/lipsync_pipeline.py': '1355313d99ef0ce3bce22deec2db82ac0910b3f887650a14611e8077a2dc800c',
    'latentsync/utils/util.py': '87a7866fa1b5dfbba3f86ff97265496f05da8f13c6c26887d5fc6a159ae023e0',
    'latentsync/models/unet.py': '9064845c34ebb9d4c854a56705b249130471822c101e84c0bf9df7ff2f604fe6',
    'latentsync/whisper/whisper/__init__.py': '5cb231ebd0daa0b0048d7166d671d69fc00a8eec85fa033d58bda68aac334d70',
    'latentsync/utils/face_detector.py': '37cfc600f8f0e409c21f8abf001ce813d08475ccaa26afde32794493d19c23e2',
}


def _une(texte: str, avant: str, apres: str) -> str:
    if texte.count(avant) != 1:
        raise ValueError('point d’adaptation ambigu ou absent')
    return texte.replace(avant, apres, 1)


def _fonction(texte: str, nom: str, remplacement: str) -> str:
    noeuds = [n for n in ast.walk(ast.parse(texte)) if isinstance(n, ast.FunctionDef) and n.name == nom]
    if len(noeuds) != 1 or noeuds[0].decorator_list:
        raise ValueError('fonction d’adaptation ambiguë')
    n = noeuds[0]
    lignes = texte.splitlines(keepends=True)
    return ''.join(lignes[:n.lineno - 1]) + remplacement + ''.join(lignes[n.end_lineno:])


def adapter(nom: str, source: bytes) -> bytes:
    if nom not in SOURCES or hashlib.sha256(source).hexdigest() != SOURCES[nom]:
        raise ValueError('source LatentSync non reconnue')
    texte = source.decode('utf-8')
    if nom == 'scripts/inference.py':
        texte = _une(texte, 'def main(config, args):\n',
                     'def main(config, args):\n'
                     '    if not os.path.isabs(args.vae_local_path) or not os.path.isdir(args.vae_local_path):\n'
                     '        raise ValueError("Dossier VAE local absolu requis")\n')
        texte = _une(texte, 'from DeepCache import DeepCacheSDHelper\n', '')
        texte = _une(texte, '    if args.enable_deepcache:\n',
                     '    if args.enable_deepcache:\n        from DeepCache import DeepCacheSDHelper\n')
        texte = _une(texte, '    scheduler = DDIMScheduler.from_pretrained("configs")',
                     '    scheduler_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "configs"))\n'
                     '    if not os.path.isdir(scheduler_dir):\n'
                     '        raise ValueError("Configuration scheduler locale requise")\n'
                     '    scheduler = DDIMScheduler.from_pretrained(scheduler_dir, local_files_only=True)')
        texte = _une(texte, 'AutoencoderKL.from_pretrained("stabilityai/sd-vae-ft-mse", torch_dtype=dtype)',
                     'AutoencoderKL.from_pretrained(args.vae_local_path, torch_dtype=dtype, local_files_only=True)')
        texte = _une(texte, '    parser.add_argument("--inference_ckpt_path", type=str, required=True)',
                     '    parser.add_argument("--vae_local_path", type=str, required=True)\n'
                     '    parser.add_argument("--inference_ckpt_path", type=str, required=True)')
    elif nom == 'latentsync/models/unet.py':
        texte = _une(texte, 'unet.load_state_dict(ckpt["state_dict"], strict=False)',
                     'unet.load_state_dict(ckpt["state_dict"], strict=True)')
    elif nom == 'latentsync/whisper/whisper/__init__.py':
        texte = _fonction(texte, '_download',
                          'def _download(*args, **kwargs):\n'
                          '    raise RuntimeError("Téléchargement Whisper interdit : poids locaux requis")\n')
    elif nom == 'latentsync/utils/face_detector.py':
        texte = 'from pathlib import Path\n' + texte
        texte = _une(texte, '    def __init__(self, device="cuda"):\n',
                     '    def __init__(self, device="cuda"):\n'
                     '        for nom in ("det_10g.onnx", "2d106det.onnx"):\n'
                     '            fichier = Path("checkpoints/auxiliary/models/buffalo_l") / nom\n'
                     '            if not fichier.is_file() or fichier.is_symlink():\n'
                     '                raise FileNotFoundError("Poids InsightFace locaux requis")\n')
    elif nom == 'latentsync/utils/util.py':
        texte = _fonction(texte, 'read_video',
                          'def read_video(video_path, change_fps=False, use_decord=True):\n'
                          '    if change_fps:\n'
                          '        raise ValueError("Réencodage implicite interdit : entrée CFR 25 requise")\n'
                          '    return read_video_decord(video_path) if use_decord else read_video_cv2(video_path)\n')
        texte = _fonction(texte, 'check_ffmpeg_installed',
                          'def check_ffmpeg_installed():\n'
                          '    subprocess.run(["ffmpeg", "-version"], check=True, timeout=10,\n'
                          '                   stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n')
        texte = _fonction(texte, 'check_model_and_download',
                          'def check_model_and_download(ckpt_path, huggingface_model_id=None):\n'
                          '    if not os.path.isfile(ckpt_path) or os.path.islink(ckpt_path):\n'
                          '        raise FileNotFoundError("Poids locaux requis, téléchargement interdit")\n')
    elif nom == 'latentsync/pipelines/lipsync_pipeline.py':
        texte = _fonction(texte, 'loop_video',
                          '    def loop_video(self, whisper_chunks, video_frames):\n'
                          '        if not len(whisper_chunks) or len(whisper_chunks) > len(video_frames):\n'
                          '            raise ValueError("Nombre d’images insuffisant : boucle vidéo interdite")\n'
                          '        video_frames = video_frames[:len(whisper_chunks)]\n'
                          '        faces, boxes, affine_matrices = self.affine_transform_video(video_frames)\n'
                          '        return video_frames, faces, boxes, affine_matrices\n')
        texte = _une(texte, 'read_video(video_path, use_decord=False)',
                     'read_video(video_path, change_fps=False, use_decord=False)')
        texte = _une(texte, '        audio_samples = read_audio(audio_path)\n',
                     '        audio_samples = read_audio(audio_path)\n'
                     '        echantillons_pcm = audio_samples.numel()\n'
                     '        if type(echantillons_pcm) is not int or echantillons_pcm <= 0:\n'
                     '            raise ValueError("PCM positif requis")\n'
                     '        if type(video_fps) is not int or video_fps != 25 or type(audio_sample_rate) is not int or audio_sample_rate != 16000:\n'
                     '            raise ValueError("Calendrier local requis : 25 i/s et PCM 16 kHz")\n'
                     '        if audio_samples.numel() * video_fps > len(whisper_chunks) * audio_sample_rate:\n'
                     '            raise ValueError("Conditionnement trop court pour conserver tout le PCM")\n'
                     '        images_pcm = (echantillons_pcm * video_fps + audio_sample_rate - 1) // audio_sample_rate\n'
                     '        print(f"NEXORA_PCM samples={echantillons_pcm} rate={audio_sample_rate} fps={video_fps} features={len(whisper_feature)} chunks={len(whisper_chunks)} frames={images_pcm}", flush=True)\n'
                     '        whisper_chunks = whisper_chunks[:images_pcm]\n')
        texte = _une(texte,
                     '        audio_samples_remain_length = int(synced_video_frames.shape[0] / video_fps * audio_sample_rate)\n'
                     '        audio_samples = audio_samples[:audio_samples_remain_length].cpu().numpy()',
                     '        if audio_samples.numel() * video_fps > synced_video_frames.shape[0] * audio_sample_rate:\n'
                     '            raise ValueError("Vidéo trop courte : troncature PCM interdite")\n'
                     '        audio_samples = audio_samples.cpu().numpy()')
        texte = _une(texte,
                     '        if os.path.exists(temp_dir):\n            shutil.rmtree(temp_dir)\n'
                     '        os.makedirs(temp_dir, exist_ok=True)',
                     '        if os.path.lexists(temp_dir) or os.path.lexists(video_out_path):\n'
                     '            raise FileExistsError("Sorties neuves requises, aucun écrasement")\n'
                     '        os.makedirs(temp_dir, mode=0o700, exist_ok=False)')
        texte = _une(texte,
                     '        command = f"ffmpeg -y -loglevel error -nostdin -i {os.path.join(temp_dir, \'video.mp4\')} -i {os.path.join(temp_dir, \'audio.wav\')} -c:v libx264 -crf 18 -c:a aac -q:v 0 -q:a 0 {video_out_path}"\n'
                     '        subprocess.run(command, shell=True)',
                     '        command = ["ffmpeg", "-n", "-loglevel", "error", "-nostdin",\n'
                     '                   "-i", os.path.join(temp_dir, "video.mp4"), "-i", audio_path,\n'
                     '                   "-map", "0:v:0", "-map", "1:a:0", "-c:v", "libx264",\n'
                     '                   "-crf", "18", "-c:a", "aac", video_out_path]\n'
                     '        subprocess.run(command, check=True, timeout=180, stdin=subprocess.DEVNULL)')
    ast.parse(texte)
    return texte.encode('utf-8')
