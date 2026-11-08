"""Détection S3FD expérimentale, explicite et locale pour HighSync.

Ce backend diffère de DeepFace/YOLO : les boîtes ne sont pas prétendues
équivalentes. Il fournit une boîte et une confiance par image BGR ; le cadrage
et la segmentation temporelle restent ceux de HighSync.
"""
from __future__ import annotations

import hashlib
import importlib
import math
from pathlib import Path
import sys
import types
import uuid

SOURCE_SHA = {
    'net_s3fd.py': '80960aaefd9fb97a5e9784dc0a48bc38f43bdcaacb268782ede16a959e77a5a9',
    'bbox.py': '3ed1487243bbde8ab47c567f46ee4b177a549e31440db8d71376bffc70a7bd86',
    'detect.py': '2bb9e9383e6a582d216515aab36759652cb9e7800a1910a6394ff721c4291a90',
}
WEIGHT_SHA = '619a31681264d3f7f7fc7a16a42cbbe8b23f31a256f75a366e5a1bcd59b33543'


def empreinte(path: Path) -> str:
    if not path.is_absolute() or path.is_symlink() or not path.is_file():
        raise ValueError('fichier local régulier requis')
    digest = hashlib.sha256()
    with path.open('rb') as f:
        for bloc in iter(lambda: f.read(1024 * 1024), b''):
            digest.update(bloc)
    return digest.hexdigest()


def choisir(detections, largeur: int, hauteur: int):
    """Plus grande boîte valide, score strictement supérieur à 0,5."""
    if largeur <= 0 or hauteur <= 0:
        raise ValueError('dimensions invalides')
    retenue, surface = None, 0.0
    for detection in detections:
        if len(detection) != 5:
            raise ValueError('détection invalide')
        x1, y1, x2, y2, score = map(float, detection)
        if not all(map(math.isfinite, (x1, y1, x2, y2, score))):
            raise ValueError('détection non finie')
        x1, y1 = max(0., x1), max(0., y1)
        x2, y2 = min(float(largeur), x2), min(float(hauteur), y2)
        aire = max(0., x2-x1) * max(0., y2-y1)
        if score > .5 and aire > surface:
            retenue, surface = (int(x1), int(y1), int(x2), int(y2), score), aire
    return retenue


class DetecteurS3FD:
    def __init__(self, utils_root: Path, poids: Path):
        racine = utils_root / 'face_detection' / 'detection' / 'sfd'
        for nom, attendu in SOURCE_SHA.items():
            if empreinte(racine / nom) != attendu:
                raise ValueError('source S3FD différente de la source inventoriée')
        if empreinte(poids) != WEIGHT_SHA:
            raise ValueError('poids S3FD différents des poids inventoriés')
        if not utils_root.is_absolute() or utils_root.is_symlink() or not utils_root.is_dir():
            raise ValueError('racine S3FD invalide')
        # Charger uniquement les trois modules hachés, sans exécuter les
        # initialiseurs de package MuseTalk ni utiliser leur téléchargeur.
        nom = '_nexora_s3fd_' + uuid.uuid4().hex
        package = types.ModuleType(nom)
        package.__path__ = [str(racine)]
        sys.modules[nom] = package
        net = importlib.import_module(nom + '.net_s3fd')
        self._detect = importlib.import_module(nom + '.detect').detect
        self._nms = importlib.import_module(nom + '.bbox').nms
        torch = importlib.import_module('torch')
        self.modele = net.s3fd()
        self.modele.load_state_dict(torch.load(str(poids), map_location='cpu', weights_only=True))
        self.modele.to('cpu').eval()

    def detecter(self, image_bgr):
        if len(image_bgr.shape) != 3 or image_bgr.shape[2] != 3:
            raise ValueError('image BGR invalide')
        detections = self._detect(self.modele, image_bgr, device='cpu')
        detections = detections[self._nms(detections, .3), :]
        return choisir(detections, image_bgr.shape[1], image_bgr.shape[0])
