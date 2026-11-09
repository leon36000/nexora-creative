"""Construction vérifiable du moteur HighSync adapté, sans chargement de modèle.

La sortie est un fichier neuf dans un répertoire de travail privé. Son exécution
nécessite un superviseur distinct : ce module ne lance aucune inférence.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

SOURCE_COMMIT = '19a8efb11b52bc1b218f8dbda191e10627c6b29a'
SOURCE_SHA256 = '863285bcf8e7cc283ee04a8c698984880c844ec969c15478fc4d879d71e7f358'
WHISPER_SOURCE_SHA256 = '206da24046aea7ed799a11e210ecb9a0a7cdbf6f1dd5a4c4b98319d2aedcc586'
IMAGE_PROCESSOR_SHA256 = '5472ac9abc92737c609b026a9b9fe408c215f33885eac118af5c47508ff9cc41'


def adapter(source: bytes) -> bytes:
    if hashlib.sha256(source).hexdigest() != SOURCE_SHA256:
        raise ValueError('source HighSync différente du commit épinglé')
    texte = source.decode('utf-8')

    def remplacer(ancien: str, nouveau: str) -> None:
        nonlocal texte
        if texte.count(ancien) != 1:
            raise ValueError('ancre HighSync absente ou ambiguë')
        texte = texte.replace(ancien, nouveau, 1)

    remplacer('from denoiser import pretrained\nfrom denoiser.dsp import convert_audio\n', '')
    remplacer('from image_processor import ImageProcessor\nfrom src.utils.util import save_video, filter_non_none',
              'from highsync_image_processor import ImageProcessor\nfrom highsync_s3fd import DetecteurS3FD\nfrom pathlib import Path\n\ndef filter_non_none(obj):\n    result = {k: v for k, v in obj.items() if v is not None}\n    obj.clear()\n    obj.update(result)\n    return obj')
    remplacer('    vae = AutoencoderKL.from_pretrained(config.vae.model_path)',
              '    vae, vae_info = AutoencoderKL.from_pretrained(config.vae.model_path, local_files_only=True, use_safetensors=False, output_loading_info=True)\n    if any(vae_info.get(k) for k in ("missing_keys", "unexpected_keys", "mismatched_keys", "error_msgs")):\n        raise RuntimeError("chargement VAE incomplet")\n    print("vae: aucune clé manquante/inattendue/incompatible")')
    ancien_chargement = """    reference_unet = UNet2DConditionModel.from_pretrained(
        config.base_model_path, subfolder="unet")
    denoising_unet = EchoUNet3DConditionModel.from_pretrained_2d(
        config.base_model_path,
        "",
        subfolder="unet",
        unet_additional_kwargs=OmegaConf.to_container(
            config.unet_additional_kwargs)
    )

    reference_unet.load_state_dict(
        torch.load(config.reference_unet_path, map_location="cpu"),
    )

    denoising_unet.load_state_dict(
        torch.load(config.denoising_unet_path, map_location="cpu"),
    )"""
    nouveau_chargement = """    import json
    with open(Path(config.base_model_path) / "unet" / "config.json", encoding="utf-8") as fichier:
        base = json.load(fichier)
    reference_unet = UNet2DConditionModel.from_config(base)
    config_3d = dict(base)
    config_3d["_class_name"] = EchoUNet3DConditionModel.__name__
    config_3d["down_block_types"] = ["CrossAttnDownBlock3D"] * 3 + ["DownBlock3D"]
    config_3d["up_block_types"] = ["UpBlock3D"] + ["CrossAttnUpBlock3D"] * 3
    config_3d["mid_block_type"] = "UNetMidBlock3DCrossAttn"
    denoising_unet = EchoUNet3DConditionModel.from_config(
        config_3d, **OmegaConf.to_container(config.unet_additional_kwargs))
    for nom, modele, chemin in (("reference", reference_unet, config.reference_unet_path),
                                 ("denoising", denoising_unet, config.denoising_unet_path)):
        etat = torch.load(chemin, map_location="cpu", weights_only=True, mmap=True)
        resultat = modele.load_state_dict(etat, strict=True)
        print(f"checkpoint={nom} clés={len(etat)} manquantes={len(resultat.missing_keys)} inattendues={len(resultat.unexpected_keys)}")
        del etat"""
    remplacer(ancien_chargement, nouveau_chargement)
    remplacer('    # 2. runtime variables',
              '    if not 0 < args.cuda_fraction <= 0.60:\n        raise ValueError("fraction CUDA invalide")\n    if not torch.cuda.is_available():\n        raise RuntimeError("CUDA indisponible")\n    torch.cuda.set_per_process_memory_fraction(args.cuda_fraction, 0)\n\n    # 2. runtime variables')
    remplacer('    image_processor = ImageProcessor(img_size)',
              '    image_processor = ImageProcessor(img_size, DetecteurS3FD(Path(args.s3fd_utils_root), Path(args.s3fd_poids)))')
    remplacer('    parser.add_argument("--source_video",',
              '    parser.add_argument("--ffmpeg", required=True)\n    parser.add_argument("--cuda-fraction", type=float, required=True)\n    parser.add_argument("--s3fd-utils-root", required=True)\n    parser.add_argument("--s3fd-poids", required=True)\n    parser.add_argument("--source_video",')
    debut = texte.index('def process_audio(')
    fin = texte.index('\nimg_size = ', debut)
    texte = texte[:debut] + texte[fin:]
    remplacer('    os.makedirs(temp_dir, exist_ok=True)\n    os.system(f"rm -r {temp_dir}/*")',
              '    os.makedirs(temp_dir, exist_ok=False)')
    remplacer('    fps = config.data.export_video.fps',
              '    fps = config.data.export_video.fps\n    if fps != 25:\n        raise ValueError("cadence de configuration différente de 25 fps")')
    remplacer('    audio_temp_path = os.path.join(save_path, "audio.wav")\n    process_audio(config.driving_audio, audio_temp_path)',
              '    audio_temp_path = config.driving_audio')
    remplacer('    temp_video_path = config.output[:4] + "_no_audio.mp4"',
              '    temp_video_path = os.path.join(save_path, "video_sans_audio.mp4")\n    if os.path.lexists(temp_video_path) or os.path.lexists(config.output):\n        raise FileExistsError("sortie déjà présente")')
    remplacer('    video_length = min(int(video_stream.get(cv2.CAP_PROP_FRAME_COUNT)), audio_frame_num)\n    if video_length < audio_frame_num:\n        audio_fea_final = audio_fea_final[:, :video_length, :, :]',
              '    source_frames = int(video_stream.get(cv2.CAP_PROP_FRAME_COUNT))\n    if audio_frame_num <= 0 or source_frames < audio_frame_num:\n        raise ValueError("vidéo source trop courte pour les fenêtres audio")\n    video_length = audio_frame_num')
    remplacer('    command = f"ffmpeg -i {temp_video_path} -i {config.driving_audio} -map 0:v -map 1:a -c:v h264 -shortest -y {config.output} -loglevel quiet"\n    subprocess.run(command, shell=True, check=True, text=True)',
              '    if count_img != video_length:\n        raise RuntimeError("nombre d’images générées incomplet")\n    subprocess.run([args.ffmpeg, "-nostdin", "-n", "-i", temp_video_path, "-i", config.driving_audio, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", config.output], check=True)')
    return texte.encode('utf-8')



def adapter_image_processor(source: bytes) -> bytes:
    """Conserve le découpage et l'agrandissement auteurs, seul détecteur changé."""
    if hashlib.sha256(source).hexdigest() != IMAGE_PROCESSOR_SHA256:
        raise ValueError('image_processor auteur différent de la source épinglée')
    texte = source.decode('utf-8')
    debut = texte.index('    def preprocess_frames_jump(self, frames):')
    fin = texte.index('    def preprocess_frames_deepface_no_detect', debut)
    methode = texte[debut:fin]
    debut_detection = methode.index('            # 2.1 detect face')
    fin_detection = methode.index('        pixel_values_ref_img_all,', debut_detection)
    methode = (methode[:debut_detection] +
               '            detection = self.detecteur.detecter(frame)\n'
               '            bbox_list.append(tuple(detection[:4]) if detection else (0, 0, 0, 0))\n\n' +
               methode[fin_detection:])
    debut_aug = texte.index('    def _augmentation(self, images, transform, state=None):')
    fin_aug = texte.index('    def __enter__(self):', debut_aug)
    augmentation = texte[debut_aug:fin_aug]
    entete = ('from typing import List\nimport cv2\nimport numpy as np\nimport torch\n'
              'from PIL import Image\nfrom torchvision import transforms\n'
              'MEAN = 0.5\nSTD = 0.5\n\nclass ImageProcessor:\n'
              '    def __init__(self, img_size, detecteur):\n'
              '        self.detecteur = detecteur\n'
              '        self.pixel_transform = transforms.Compose([transforms.Resize(img_size), '
              'transforms.ToTensor(), transforms.Normalize([MEAN], [STD])])\n\n')
    return (entete + methode + augmentation).encode('utf-8')



def adapter_whisper(source: bytes) -> bytes:
    """Force weights_only pour le checkpoint local sans modifier la source amont."""
    if hashlib.sha256(source).hexdigest() != WHISPER_SOURCE_SHA256:
        raise ValueError('source Whisper auteur différente de la version épinglée')
    avant = b'torch.load(fp, map_location=device)'
    apres = b'torch.load(fp, map_location=device, weights_only=True)'
    if source.count(avant) != 1:
        raise ValueError('ancre Whisper absente ou ambiguë')
    return source.replace(avant, apres, 1)


def ecrire_source(source: Path, cible: Path) -> str:
    if source.is_symlink() or not source.is_file() or cible.is_symlink():
        raise ValueError('source ou destination invalide')
    contenu = adapter(source.read_bytes())
    with cible.open('xb') as sortie:
        sortie.write(contenu)
    return hashlib.sha256(contenu).hexdigest()
