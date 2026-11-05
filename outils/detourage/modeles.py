"""
Modèles du détourage (palier « rapide ») : SAM 3.1 pour la sélection (clic, boîte, texte) et le suivi, ViTMatte pour
les bords. Poids ouverts, hors ligne, sous NEXORA_DETOURAGE_POIDS : SAM 3.1 dans pro/Comfy-Org/sam3.1/ (sam31.py ;
licence SAM de Meta, jointe au dépôt), ViTMatte dans hf/ (HF_HOME ; Apache-2.0, hustvl/vitmatte-*-composition-1k ;
entraîné sur Composition-1k, jeu Adobe : remarque consignée dans recherche/22). SAM 2.1 a été retiré le 04/11/2026.
"""
from __future__ import annotations

import os
import threading

import numpy as np

SAM3 = 'sam3.1'
VARIANTES_MATTING = {'vitmatte-small': 'hustvl/vitmatte-small-composition-1k', 'vitmatte-base': 'hustvl/vitmatte-base-composition-1k'}


def _configurer_env():
    racine = os.environ.get('NEXORA_DETOURAGE_POIDS') or os.path.expanduser('~/nexora-creative-data/models/detourage')
    os.environ.setdefault('HF_HOME', os.path.join(racine, 'hf'))
    os.environ.setdefault('HF_HUB_OFFLINE', '1')
    return racine


class Modeles:
    """Charge à la demande et garde en mémoire. Le verrou ne protège que le chargement : l'inférence est réentrante, ce qui
    laisse l'aperçu interactif d'une image passer pendant qu'un long travail tourne."""

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
        self._mat: dict = {}
        self._sam3 = None

    # ----- SAM 3.1
    def sam3(self):
        with self.verrou:
            if self._sam3 is None:
                from sam31 import Sam31
                s = Sam31(self.torch, self.appareil)
                s.charger()
                self._sam3 = s
            return self._sam3

    @staticmethod
    def _variante(variante: str):
        # « large » et « small » (anciens noms SAM 2.1, encore envoyés par d'anciens clients) désignent désormais SAM 3.1
        if variante not in (SAM3, None, '', 'large', 'small'):
            raise ValueError(f'modèle de sélection inconnu : {variante} (seul {SAM3} est installé)')

    def sam_effectif(self, variante: str) -> str:
        self._variante(variante)
        return SAM3

    def detecter_texte(self, rgb: np.ndarray, texte: str, seuil: float = 0.4) -> list[dict]:
        return self.sam3().detecter_texte(rgb, texte, seuil)

    def masque_image(self, rgb: np.ndarray, graine: dict, variante: str = SAM3) -> tuple[np.ndarray, float]:
        """Aperçu interactif : une image, des points/boîte -> (probabilité H×W float16, score)."""
        self._variante(variante)
        return self.sam3().masque_image(rgb, graine)

    def suivre(self, trames: list[np.ndarray], graines: dict[int, dict], depart: int, sens: str, variante: str = SAM3,
               annule=None, progres=None) -> tuple[np.ndarray, np.ndarray]:
        """Suit l'objet dans un segment : (probabilités T×H×W float16, visible T bool). Voir sam31.Sam31.suivre."""
        self._variante(variante)
        return self.sam3().suivre(trames, graines, depart, sens, annule, progres)

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
        d = {'appareil': self.appareil, 'dtype': str(self.dtype).replace('torch.', ''), 'sam': [SAM3] if self._sam3 else [],
             'matting': sorted(self._mat)}
        if self.appareil == 'cuda':
            d['gpu'] = t.cuda.get_device_name(0)
            d['vram_pic_go'] = round(t.cuda.max_memory_allocated() / 1e9, 2)
            libre, total = t.cuda.mem_get_info()
            d['memoire_gpu_libre_go'] = round(libre / 1e9, 1)
            d['memoire_gpu_totale_go'] = round(total / 1e9, 1)
        return d
