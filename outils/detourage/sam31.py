"""
SAM 3.1 (Object Multiplex) pour le détourage : sélection au clic, à la boîte ou par texte, et suivi vidéo.

Poids : Comfy-Org/sam3.1, `checkpoints/sam3.1_multiplex_fp16.safetensors` (fp16, 1,75 Go ; licence SAM de Meta jointe au
dépôt), sous <NEXORA_DETOURAGE_POIDS>/pro/Comfy-Org/sam3.1/ (manifeste : pro/modeles-pro.json). Implémentation : le
code SAM 3 de ComfyUI (comfy/ldm/sam3, v0.44.0) appelé comme bibliothèque (NEXORA_COMFYUI = dossier de ComfyUI) : pas
de second serveur, un seul processus tient le GPU.

Mêmes formats que modeles.Modeles (SAM 2.1) : points normalisés [x, y, étiquette], boîte [x0, y0, x1, y1] normalisée,
masque graine, probabilités float16, visibilité par image. Différences : le suivi part d'un masque initial unique par
segment (les autres clics du segment servent seulement à l'image où ils sont posés) ; les masques suivis sont binaires.
"""
from __future__ import annotations

import os
import sys
import threading

import numpy as np

TAILLE = 1008  # résolution d'entrée du modèle SAM 3


def chemin_poids() -> str:
    racine = os.environ.get('NEXORA_DETOURAGE_POIDS') or os.path.expanduser('~/nexora-creative-data/models/detourage')
    return os.path.join(racine, 'pro', 'Comfy-Org', 'sam3.1', 'checkpoints', 'sam3.1_multiplex_fp16.safetensors')


class Annulation:
    """Barre de progression de ComfyUI détournée : appelle `progres` et lève InterruptedError si `annule()`."""

    def __init__(self, n, annule=None, progres=None, base=0.0, part=1.0):
        self.n, self.fait, self.annule, self.progres, self.base, self.part = max(1, n), 0, annule, progres, base, part

    def update(self, k=1):
        self.fait += k
        if self.annule and self.annule():
            raise InterruptedError('annulé')
        if self.progres:
            self.progres(self.base + self.part * min(1.0, self.fait / self.n))

    def update_absolute(self, v, total=None, preview=None):
        self.update(max(0, v - self.fait))


class Sam31:
    def __init__(self, torch_mod, appareil: str):
        self.torch = torch_mod
        self.appareil = appareil
        self.verrou = threading.RLock()
        self._m = None  # (patcher, clip)

    def charger(self):
        with self.verrou:
            if self._m is None:
                comfy_dir = os.environ.get('NEXORA_COMFYUI') or '/opt/ComfyUI'
                if comfy_dir not in sys.path:
                    sys.path.insert(0, comfy_dir)
                import comfy.sd  # noqa: E402
                p = chemin_poids()
                if not os.path.exists(p):
                    raise FileNotFoundError(f'poids SAM 3.1 absents : {p}')
                patcher, clip, _vae, _ = comfy.sd.load_checkpoint_guess_config(p, output_vae=False, output_clip=True)
                self._m = (patcher, clip)
            return self._m

    def _modele(self):
        import comfy.model_management as mm
        patcher, clip = self.charger()
        mm.load_model_gpu(patcher)
        return patcher.model.diffusion_model, patcher.model.get_dtype(), mm.get_torch_device(), clip

    def _image(self, rgb: np.ndarray, dev, dtype):
        import comfy.utils
        t = self.torch.from_numpy(np.ascontiguousarray(rgb)).float().div(255.0)[None]  # [1, H, W, 3]
        return comfy.utils.common_upscale(t.movedim(-1, 1), TAILLE, TAILLE, 'bilinear', crop='disabled').to(dev, dtype)

    def _segmenter(self, m, frame, g: dict, h: int, w: int, dev, dtype, affinages: int = 2):
        """Logits haute résolution H×W (float32) d'une graine points/boîte/masque sur une image prétraitée."""
        F = self.torch.nn.functional
        kw = {}
        pts = g.get('points') or []
        if pts:
            kw['point_inputs'] = {
                'point_coords': self.torch.tensor([[[x * TAILLE, y * TAILLE] for x, y, _ in pts]], dtype=dtype, device=dev),
                'point_labels': self.torch.tensor([[int(l) for _, _, l in pts]], dtype=self.torch.int32, device=dev)}
        if g.get('boite'):
            x0, y0, x1, y1 = g['boite']
            kw['box_inputs'] = self.torch.tensor([[[x0 * TAILLE, y0 * TAILLE], [x1 * TAILLE, y1 * TAILLE]]], dtype=dtype, device=dev)
        if g.get('masque') is not None and not kw:
            mk = self.torch.from_numpy((np.asarray(g['masque']) > 0.5).astype(np.float32))[None, None].to(dev, dtype)
            kw['mask_inputs'] = F.interpolate(mk * 20 - 10, size=(TAILLE // 4, TAILLE // 4), mode='bilinear', align_corners=False)
        logit = m.forward_segment(frame, **kw)
        for _ in range(max(0, affinages - 1)):
            logit = m.forward_segment(frame, mask_inputs=logit)
        return F.interpolate(logit.float(), size=(h, w), mode='bilinear', align_corners=False)[0, 0]

    def masque_image(self, rgb: np.ndarray, graine: dict) -> tuple[np.ndarray, float]:
        h, w = rgb.shape[:2]
        with self.torch.inference_mode():
            m, dtype, dev, _ = self._modele()
            logit = self._segmenter(m, self._image(rgb, dev, dtype), graine, h, w, dev, dtype)
            proba = self.torch.sigmoid(logit).cpu().numpy().astype(np.float16)
            score = float(logit.max())
        return proba, score

    def detecter_texte(self, rgb: np.ndarray, texte: str, seuil: float = 0.4, maximum: int = 8) -> list[dict]:
        """Objets désignés par un texte (anglais : « person », « dog ») : masque, score, boîte normalisée, par score décroissant."""
        h, w = rgb.shape[:2]
        with self.torch.inference_mode():
            m, dtype, dev, clip = self._modele()
            cond = clip.encode_from_tokens_scheduled(clip.tokenize(texte))
            emb = cond[0][0].to(dev, dtype)
            masque_txt = cond[0][1].get('attention_mask')
            masque_txt = masque_txt.to(dev) if masque_txt is not None else self.torch.ones(emb.shape[0], emb.shape[1], dtype=self.torch.int64, device=dev)
            frame = self._image(rgb, dev, dtype)
            r = m(frame, text_embeddings=emb, text_mask=masque_txt, threshold=seuil, orig_size=(h, w))
            probs = r['scores'][0].sigmoid()
            garde = (probs > seuil).nonzero().flatten().tolist()
            garde = sorted(garde, key=lambda i: -float(probs[i]))[:maximum]
            objets = []
            for i in garde:
                x0, y0, x1, y1 = [float(v) for v in r['boxes'][0][i]]
                boite = [max(0.0, x0 / w), max(0.0, y0 / h), min(1.0, x1 / w), min(1.0, y1 / h)]
                logit = self._segmenter(m, frame, {'boite': boite}, h, w, dev, dtype)  # affinage par le décodeur SAM
                objets.append({'masque': self.torch.sigmoid(logit).cpu().numpy().astype(np.float16), 'score': round(float(probs[i]), 3),
                               'boite': [round(v, 4) for v in boite]})
        return objets

    def suivre(self, trames: list[np.ndarray], graines: dict[int, dict], depart: int, sens: str,
               annule=None, progres=None) -> tuple[np.ndarray, np.ndarray]:
        from comfy.ldm.sam3.tracker import unpack_masks
        h, w = trames[0].shape[:2]
        n = len(trames)
        proba = np.zeros((n, h, w), np.float16)
        vis = np.zeros(n, bool)
        with self.torch.inference_mode():
            m, dtype, dev, _ = self._modele()
            g = graines.get(depart) or {}
            if g.get('masque') is not None and not (g.get('points') or g.get('boite')):
                init = (np.asarray(g['masque']) > 0.5).astype(np.float32)
            else:
                init = (self._segmenter(m, self._image(trames[depart], dev, dtype), g, h, w, dev, dtype) > 0).float().cpu().numpy()
            if not init.any():
                return proba, vis
            passes = []
            if sens in ('avant', 'deux'):
                passes.append(list(range(depart, n)))
            if sens in ('arriere', 'deux'):
                passes.append(list(range(depart, -1, -1)))
            total = sum(len(p) for p in passes)
            fait = 0
            for idx in passes:
                images = self.torch.from_numpy(np.stack([trames[i] for i in idx])).float().div(255.0).movedim(-1, 1)  # [N, 3, H, W]
                barre = Annulation(len(idx), annule, progres, fait / total, len(idx) / total)
                res = m.forward_video(images=images, initial_masks=self.torch.from_numpy(init)[None, None].to(dev, dtype), pbar=barre,
                                      text_prompts=None, max_objects=1, detect_interval=1, target_device=dev, target_dtype=dtype)
                fait += len(idx)
                if res.get('packed_masks') is None:
                    continue
                mk = unpack_masks(res['packed_masks'])  # [N, objets, h', w'] booléens
                mk = mk[:, 0].float()[:, None]
                if mk.shape[-2:] != (h, w):
                    mk = self.torch.nn.functional.interpolate(mk, size=(h, w), mode='nearest')
                mk = mk[:, 0].cpu().numpy()
                for j, i in enumerate(idx):
                    if j < mk.shape[0]:
                        vis[i] = bool(mk[j].any())
                        proba[i] = mk[j].astype(np.float16)
            if self.appareil == 'cuda':
                self.torch.cuda.empty_cache()
        return proba, vis

    def etat(self) -> dict:
        return {'charge': self._m is not None, 'poids': os.path.basename(chemin_poids())}
