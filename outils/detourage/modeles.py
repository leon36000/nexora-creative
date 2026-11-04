"""
Modèles du détourage (paliers « rapide » : SAM 2.1 pour la sélection et le suivi, ViTMatte pour les bords).
Poids ouverts, hors ligne : HF_HOME pointe sur le dossier de poids (variable NEXORA_DETOURAGE_POIDS), aucun jeton.
SAM 2.1 : Apache-2.0 (facebook/sam2.1-hiera-*). ViTMatte : Apache-2.0 (hustvl/vitmatte-*-composition-1k).
Remarque licence consignée dans recherche/22 : ViTMatte est entraîné sur Composition-1k (jeu Adobe).
"""
from __future__ import annotations

import os
import threading

import numpy as np

VARIANTES_SAM = {'large': 'facebook/sam2.1-hiera-large', 'small': 'facebook/sam2.1-hiera-small'}
SAM3 = 'sam3.1'  # SAM 3.1 (sam31.py) : défaut ; SAM 2.1 large en repli s'il ne se charge pas
REPLI_SAM = 'large'
VARIANTES_MATTING = {'vitmatte-small': 'hustvl/vitmatte-small-composition-1k', 'vitmatte-base': 'hustvl/vitmatte-base-composition-1k'}


def _configurer_env():
    racine = os.environ.get('NEXORA_DETOURAGE_POIDS') or os.path.expanduser('~/nexora-creative-data/models/detourage')
    os.environ.setdefault('HF_HOME', os.path.join(racine, 'hf'))
    os.environ.setdefault('HF_HUB_OFFLINE', '1')
    return racine


class Modeles:
    """Charge à la demande et garde en mémoire. Le verrou ne protège que le chargement : l'inférence est réentrante, ce qui
    laisse l'aperçu interactif d'une image passer pendant qu'un long travail tourne (les sessions SAM sont indépendantes)."""

    def __init__(self):
        _configurer_env()
        import torch
        self.torch = torch
        self.appareil = 'cuda' if torch.cuda.is_available() else 'cpu'
        # bf16 sur Ampere et plus (GB10, 5080, 5090) ; fp16 sur Volta et Turing (V100 de pc3, pc5) ; fp32 sur CPU.
        # La capacité est lue directement : is_bf16_supported() répond oui par émulation sur Volta (lent).
        if self.appareil == 'cuda':
            self.dtype = torch.bfloat16 if torch.cuda.get_device_capability(0) >= (8, 0) else torch.float16
        else:
            self.dtype = torch.float32
        self.verrou = threading.RLock()
        self._sam: dict = {}
        self._mat: dict = {}
        self._sam3 = None
        self.repli: str | None = None  # raison du repli sur SAM 2.1, s'il a eu lieu

    # ----- SAM 3.1, avec repli
    def sam3(self):
        """L'adaptateur SAM 3.1 chargé, ou None (repli SAM 2.1, raison dans self.repli)."""
        with self.verrou:
            if self._sam3 is None and self.repli is None:
                try:
                    from sam31 import Sam31
                    s = Sam31(self.torch, self.appareil)
                    s.charger()
                    self._sam3 = s
                except Exception as e:  # noqa: BLE001 - tout échec de chargement mène au repli, consigné
                    self.repli = f'{type(e).__name__}: {e}'[:300]
                    import sys
                    print(f'[detourage] SAM 3.1 indisponible, repli sur SAM 2.1 : {self.repli}', file=sys.stderr, flush=True)
            return self._sam3

    def _resoudre(self, variante: str):
        """(adaptateur SAM 3.1 ou None, variante SAM 2.1 effective)."""
        if variante == SAM3:
            s = self.sam3()
            return (s, None) if s else (None, REPLI_SAM)
        return None, variante

    def sam_effectif(self, variante: str) -> str:
        s3, v = self._resoudre(variante)
        return SAM3 if s3 else v

    def detecter_texte(self, rgb: np.ndarray, texte: str, seuil: float = 0.4) -> list[dict]:
        s = self.sam3()
        if not s:
            raise RuntimeError(f'sélection par texte indisponible (SAM 3.1 non chargé : {self.repli})')
        return s.detecter_texte(rgb, texte, seuil)

    # ----- SAM 2.1
    def sam(self, variante: str = 'large'):
        with self.verrou:
            if variante not in self._sam:
                from transformers import Sam2VideoModel, Sam2VideoProcessor
                depot = VARIANTES_SAM[variante]
                m = Sam2VideoModel.from_pretrained(depot, torch_dtype=self.dtype).to(self.appareil).eval()
                self._sam[variante] = (m, Sam2VideoProcessor.from_pretrained(depot))
            return self._sam[variante]

    def session(self, trames: list[np.ndarray], variante: str = 'large'):
        m, p = self.sam(variante)
        s = p.init_video_session(video=trames, inference_device=self.appareil, video_storage_device='cpu', dtype=self.dtype)
        return m, p, s

    def _graine(self, p, s, k: int, g: dict, h: int, w: int):
        """Pose une graine (points/boîte normalisés 0..1, ou masque) sur la trame locale k."""
        kw = {}
        pts = g.get('points') or []
        if pts:
            kw['input_points'] = [[[[x * w, y * h] for x, y, _ in pts]]]
            kw['input_labels'] = [[[int(l) for _, _, l in pts]]]
        if g.get('boite'):
            x0, y0, x1, y1 = g['boite']
            kw['input_boxes'] = [[[x0 * w, y0 * h, x1 * w, y1 * h]]]
        if g.get('masque') is not None:
            kw['input_masks'] = (g['masque'] > 0.5).astype(np.uint8)
        p.add_inputs_to_inference_session(inference_session=s, frame_idx=k, obj_ids=1, original_size=(h, w), **kw)

    def _proba(self, p, sortie, h: int, w: int) -> np.ndarray:
        m = p.post_process_masks([sortie.pred_masks], original_sizes=[[h, w]], binarize=False)[0]
        return self.torch.sigmoid(m[0, 0].float()).cpu().numpy().astype(np.float16)

    def masque_image(self, rgb: np.ndarray, graine: dict, variante: str = SAM3) -> tuple[np.ndarray, float]:
        """Aperçu interactif : une image, des points/boîte -> (probabilité H×W float16, score d'objet)."""
        s3, variante = self._resoudre(variante)
        if s3:
            return s3.masque_image(rgb, graine)
        h, w = rgb.shape[:2]
        with self.torch.inference_mode():
            m, p, s = self.session([rgb], variante)
            self._graine(p, s, 0, graine, h, w)
            o = m(inference_session=s, frame_idx=0)
            return self._proba(p, o, h, w), float(o.object_score_logits.flatten()[0])

    def suivre(self, trames: list[np.ndarray], graines: dict[int, dict], depart: int, sens: str, variante: str,
               annule=None, progres=None) -> tuple[np.ndarray, np.ndarray]:
        """Suit l'objet dans un segment.

        `graines` : trame locale -> graine ; `depart` : trame locale d'où l'on se propage ; `sens` : 'avant', 'arriere'
        ou 'deux'. Retourne (probabilités T×H×W float16, visible T bool). Une trame dont le score d'objet est ≤ 0
        est déclarée non visible (occlusion ou sortie de champ) et son masque est mis à zéro.
        """
        s3, variante = self._resoudre(variante)
        if s3:
            return s3.suivre(trames, graines, depart, sens, annule, progres)
        h, w = trames[0].shape[:2]
        n = len(trames)
        proba = np.zeros((n, h, w), np.float16)
        vis = np.zeros(n, bool)
        fait = 0
        with self.torch.inference_mode():
            m, p, s = self.session(trames, variante)
            for k, g in sorted(graines.items()):
                self._graine(p, s, k, g, h, w)
            passes = []
            if sens in ('avant', 'deux'):
                passes.append(False)
            if sens in ('arriere', 'deux'):
                passes.append(True)
            for inverse in passes:
                for o in m.propagate_in_video_iterator(s, start_frame_idx=depart, reverse=inverse):
                    if annule and annule():
                        raise InterruptedError('annulé')
                    k = o.frame_idx
                    pr = self._proba(p, o, h, w)
                    ok = float(o.object_score_logits.flatten()[0]) > 0.0
                    vis[k] = ok
                    proba[k] = pr if ok else 0
                    fait += 1
                    if progres:
                        progres(fait / (n * len(passes)))
            del s
            self.torch.cuda.empty_cache() if self.appareil == 'cuda' else None
        return proba, vis

    # ----- ViTMatte
    def matting(self, variante: str):
        with self.verrou:
            if variante not in self._mat:
                from transformers import VitMatteForImageMatting, VitMatteImageProcessor
                depot = VARIANTES_MATTING[variante]
                self._mat[variante] = (VitMatteForImageMatting.from_pretrained(depot).to(self.appareil, self.dtype).eval(),
                                       VitMatteImageProcessor.from_pretrained(depot))
            return self._mat[variante]

    def affiner(self, rgb: np.ndarray, tri: np.ndarray, variante: str) -> np.ndarray:
        """ViTMatte sur une vignette : rgb uint8 H×W×3, trimap uint8 -> alpha float32 H×W (0..1)."""
        from PIL import Image
        m, p = self.matting(variante)
        with self.torch.inference_mode():
            x = p(images=Image.fromarray(rgb), trimaps=Image.fromarray(tri), return_tensors='pt')
            x = {k: v.to(self.appareil, self.dtype if v.is_floating_point() else v.dtype) for k, v in x.items()}
            a = m(**x).alphas[0, 0].float().cpu().numpy()
        return np.clip(a[:rgb.shape[0], :rgb.shape[1]], 0, 1).astype(np.float32)

    def etat(self) -> dict:
        t = self.torch
        d = {'appareil': self.appareil, 'dtype': str(self.dtype).replace('torch.', ''), 'sam': sorted(self._sam) + ([SAM3] if self._sam3 else []),
             'matting': sorted(self._mat), 'sam3_repli': self.repli}
        if self.appareil == 'cuda':
            d['gpu'] = t.cuda.get_device_name(0)
            d['vram_pic_go'] = round(t.cuda.max_memory_allocated() / 1e9, 2)
            libre, total = t.cuda.mem_get_info()
            d['memoire_gpu_libre_go'] = round(libre / 1e9, 1)
            d['memoire_gpu_totale_go'] = round(total / 1e9, 1)
        return d
