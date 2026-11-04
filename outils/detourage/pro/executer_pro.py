"""
Palier pro du détourage : une vidéo RGB -> son matte alpha par LTX-2.5 22B distilled + IC-LoRA Alpha-Gen (ComfyUI).

  python executer_pro.py <video.mp4> <dossier_sortie> [--largeur 1280] [--images 49] [--debut 0] [--transformeur nvfp4|int8]
                         [--comfy http://127.0.0.1:8188] [--graine 42]

Graphe écrit d'après la fiche du modèle et le flux officiel « LTX-2.5 V2V IC-LoRA Single Stage Distilled » de
ComfyUI-LTXVideo : prompt vide, LoRA à 1,0, guide vidéo de référence à la même résolution (facteur 1), une seule
passe distillée (8 pas, sigmas du flux officiel), décodage par tuiles. Préparation : la vidéo est complétée (pas
étirée) jusqu'à des dimensions multiples de 32 et 8n+1 images ; le matte est recadré à la taille d'origine.
Sortie : alpha_%06d.png (gris 8 bits, tel que décodé) et mesures.json (temps, VRAM pic vue par ComfyUI).
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import threading
import time
import urllib.request
import uuid

SIGMAS = '1.0, 0.99375, 0.9875, 0.98125, 0.975, 0.909375, 0.725, 0.421875, 0.0'
TRANSFORMEURS = {'nvfp4': 'ltx-2.5-22b-distilled-transformer-nvfp4.safetensors',
                 'int8': 'ltx-2.5-22b-distilled-transformer-comfy-int8-convrot.safetensors'}


def graphe(video: str, l: int, h: int, n: int, fps: float, transformeur: str, graine: int, prefixe: str) -> dict:
    g = {
        'unet': ('UNETLoader', {'unet_name': TRANSFORMEURS[transformeur], 'weight_dtype': 'default'}),
        'lora': ('LTXICLoRALoaderModelOnly', {'model': ['unet', 0], 'lora_name': 'ltx-2.5-22b-ic-lora-alpha-gen-0.9.safetensors', 'strength_model': 1.0}),
        'clip': ('CLIPLoader', {'clip_name': 'gemma4-12b-with-proj-ltx-2.5-comfy-int8-convrot.safetensors', 'type': 'ltxv', 'device': 'default'}),
        'pos': ('CLIPTextEncode', {'text': '', 'clip': ['clip', 0]}),
        'neg': ('CLIPTextEncode', {'text': '', 'clip': ['clip', 0]}),
        'cond': ('LTXVConditioning', {'positive': ['pos', 0], 'negative': ['neg', 0], 'frame_rate': fps}),
        'vae': ('VAELoader', {'vae_name': 'ltx-2.5-video-vae-bf16.safetensors'}),
        'vae_audio': ('VAELoader', {'vae_name': 'ltx-2.5-audio-vae-bf16.safetensors'}),
        'video': ('LoadVideo', {'file': video}),
        'images': ('GetVideoComponents', {'video': ['video', 0]}),
        'latent': ('EmptyLTXVLatentVideo', {'width': l, 'height': h, 'length': n, 'batch_size': 1}),
        'guide': ('LTXAddVideoICLoRAGuide', {'positive': ['cond', 0], 'negative': ['cond', 1], 'vae': ['vae', 0], 'latent': ['latent', 0],
                                             'image': ['images', 0], 'frame_idx': 0, 'strength': 1.0, 'latent_downscale_factor': 1.0,
                                             'crop': 'disabled', 'use_tiled_encode': False, 'tile_size': 256, 'tile_overlap': 64}),
        'audio': ('EmptyAudio', {'duration': n / fps, 'sample_rate': 44100, 'channels': 2}),
        'latent_audio': ('VAEEncodeAudio', {'audio': ['audio', 0], 'vae': ['vae_audio', 0]}),
        'av': ('LTXVConcatAVLatent', {'video_latent': ['guide', 2], 'audio_latent': ['latent_audio', 0]}),
        'bruit': ('RandomNoise', {'noise_seed': graine}),
        'guideur': ('CFGGuider', {'model': ['lora', 0], 'positive': ['guide', 0], 'negative': ['guide', 1], 'cfg': 1.0}),
        'echant': ('KSamplerSelect', {'sampler_name': 'euler_ancestral'}),
        'sigmas': ('ManualSigmas', {'sigmas': SIGMAS}),
        'debruit': ('SamplerCustomAdvanced', {'noise': ['bruit', 0], 'guider': ['guideur', 0], 'sampler': ['echant', 0], 'sigmas': ['sigmas', 0],
                                              'latent_image': ['av', 0]}),
        'separe': ('LTXVSeparateAVLatent', {'av_latent': ['debruit', 0]}),
        'recadre': ('LTXVCropGuides', {'positive': ['guide', 0], 'negative': ['guide', 1], 'latent': ['separe', 0]}),
        'decode': ('VAEDecodeTiled', {'samples': ['recadre', 2], 'vae': ['vae', 0], 'tile_size': 512, 'overlap': 64, 'temporal_size': 64, 'temporal_overlap': 8}),
        'sortie': ('SaveImage', {'images': ['decode', 0], 'filename_prefix': prefixe}),
    }
    return {k: {'class_type': c, 'inputs': i} for k, (c, i) in g.items()}


def appel(base: str, chemin: str, corps=None):
    r = urllib.request.Request(base + chemin, data=json.dumps(corps).encode() if corps is not None else None,
                               headers={'content-type': 'application/json'})
    with urllib.request.urlopen(r, timeout=60) as x:
        return json.loads(x.read() or b'{}')


def main():
    a = argparse.ArgumentParser()
    a.add_argument('video'), a.add_argument('sortie')
    a.add_argument('--largeur', type=int, default=1280), a.add_argument('--images', type=int, default=49)
    a.add_argument('--debut', type=float, default=0.0), a.add_argument('--transformeur', default='nvfp4')
    a.add_argument('--comfy', default='http://127.0.0.1:8188'), a.add_argument('--graine', type=int, default=42)
    a.add_argument('--dossier-comfy', default='/opt/ComfyUI')
    p = a.parse_args()
    n = (max(9, min(145, p.images)) - 1) // 8 * 8 + 1  # 8n+1, au plus 145 (fiche du modèle)
    info = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height,r_frame_rate',
                                      '-of', 'json', p.video], capture_output=True, text=True).stdout)['streams'][0]
    num, den = info['r_frame_rate'].split('/')
    fps = float(num) / float(den)
    l0 = min(p.largeur, info['width']) // 2 * 2
    h0 = int(round(info['height'] * l0 / info['width'] / 2)) * 2
    l, h = -(-l0 // 32) * 32, -(-h0 // 32) * 32  # complété, pas étiré
    nom = f'pro-{uuid.uuid4().hex[:10]}.mp4'
    entree = os.path.join(p.dossier_comfy, 'input', nom)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(p.debut), '-i', p.video, '-frames:v', str(n),
                    '-vf', f'scale={l0}:{h0}:flags=lanczos,pad={l}:{h}:0:0:color=black,tpad=stop_mode=clone:stop={n}',
                    '-frames:v', str(n), '-c:v', 'libx264', '-crf', '10', '-pix_fmt', 'yuv420p', entree], check=True)
    prefixe = f'detourage-pro/{nom[:-4]}'
    vram = {'total': None, 'libre_min': None}
    fin = threading.Event()

    def surveiller():
        while not fin.is_set():
            try:
                d = appel(p.comfy, '/system_stats')['devices'][0]
                vram['total'] = d['vram_total']
                vram['libre_min'] = d['vram_free'] if vram['libre_min'] is None else min(vram['libre_min'], d['vram_free'])
            except Exception:  # noqa: BLE001
                pass
            fin.wait(0.5)

    threading.Thread(target=surveiller, daemon=True).start()
    t0 = time.time()
    r = appel(p.comfy, '/prompt', {'prompt': graphe(nom, l, h, n, fps, p.transformeur, p.graine, prefixe), 'client_id': 'detourage-pro'})
    pid = r['prompt_id']
    while True:
        time.sleep(2)
        hist = appel(p.comfy, f'/history/{pid}').get(pid)
        if hist and hist.get('status', {}).get('completed') is not None:
            break
        if hist and hist.get('status', {}).get('status_str') == 'error':
            break
    fin.set()
    duree = round(time.time() - t0, 1)
    statut = hist.get('status', {})
    os.makedirs(p.sortie, exist_ok=True)
    fichiers = [img for o in hist.get('outputs', {}).values() for img in o.get('images', []) if img.get('type') == 'output' and img['filename'].endswith('.png')]
    for i, img in enumerate(sorted(fichiers, key=lambda x: x['filename'])):
        src = os.path.join(p.dossier_comfy, 'output', img.get('subfolder', ''), img['filename'])
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-vf', f'crop={l0}:{h0}:0:0,format=gray', os.path.join(p.sortie, f'alpha_{i:06d}.png')], check=True)
        os.remove(src)
    os.remove(entree)
    m = {'etat': statut.get('status_str'), 'secondes': duree, 'images': n, 'taille_traitee': [l, h], 'taille_sortie': [l0, h0], 'fps': fps,
         'transformeur': p.transformeur, 'vram_pic_go': round((vram['total'] - vram['libre_min']) / 1e9, 2) if vram['total'] else None,
         'secondes_par_image': round(duree / n, 2), 'messages': [x[0] for x in statut.get('messages', [])][-6:],
         'erreur': next((x[1].get('exception_message') for x in statut.get('messages', []) if x[0] == 'execution_error'), None)}
    json.dump(m, open(os.path.join(p.sortie, 'mesures.json'), 'w'), ensure_ascii=False, indent=1)
    print(json.dumps(m, ensure_ascii=False))
    shutil.rmtree(os.path.join(p.dossier_comfy, 'output', 'detourage-pro'), ignore_errors=True)


if __name__ == '__main__':
    main()
