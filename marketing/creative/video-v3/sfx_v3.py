"""Sound design de la promo V3, synthétisé en numpy (aucun échantillon externe) : impacts de bande-annonce, explosions,
tirs, rafales de canons, fouets, montées, chutes de sub, drone d'ouverture, frappe au clavier et clic d'interface.

Chaque son est déterministe (graine) et rendu en stéréo 48 kHz float. Les filtres passent par la FFT (masque spectral).
Usage : python3 sfx_v3.py type duree sortie.wav [graine]
"""
import sys
import wave

import numpy as np

SR = 48000


def _t(d):
    return np.arange(int(d * SR)) / SR


def filtre(x, bas=None, haut=None, pente=2.0):
    """Passe-haut (bas = fréquence de coupure basse) et/ou passe-bas (haut), masque doux dans le domaine fréquentiel."""
    n = len(x)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, 1 / SR)
    m = np.ones_like(f)
    if bas:
        m *= 1 / (1 + (bas / np.maximum(f, 1)) ** (2 * pente))
    if haut:
        m *= 1 / (1 + (f / haut) ** (2 * pente))
    return np.fft.irfft(X * m, n)


def env(d, attaque=0.002, decroissance=1.0, forme=1.0):
    t = _t(d)
    a = np.clip(t / max(attaque, 1e-4), 0, 1)
    return a * np.exp(-t / max(decroissance, 1e-3)) ** forme


def stereo(g, d=None, largeur=0.3, rng=None):
    """Élargit un son mono : canal droit légèrement retardé et décoloré."""
    rng = rng or np.random.default_rng(0)
    k = int(SR * 0.011 * largeur)
    r = np.concatenate([np.zeros(k), g[:-k]]) if k else g
    return np.stack([g, g * (1 - largeur * 0.3) + r * largeur * 0.3], 1) if d is None else np.stack([g * (1 - d), g * (1 + d)], 1)


def norm(x, crete=0.95):
    return x / (np.abs(x).max() + 1e-9) * crete


def bruit(rng, d):
    return rng.normal(0, 1, int(d * SR))


def generer(kind: str, d: float, rng: np.random.Generator) -> np.ndarray:
    t = _t(d)
    if kind == "impact":  # coup de bande-annonce : sub qui tombe + claquement + résonance métallique
        sub = np.sin(2 * np.pi * np.cumsum(32 + 90 * np.exp(-t * 14)) / SR) * env(d, 0.001, 0.9)
        claque = filtre(bruit(rng, d), 900, 9000) * env(d, 0.0005, 0.035)
        corps = filtre(bruit(rng, d), 60, 700) * env(d, 0.001, 0.25)
        metal = sum(np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) * np.exp(-t * (2.5 + k)) for k, f in enumerate([187, 433, 761, 1183, 1607])) * 0.18
        g = sub * 1.0 + claque * 0.8 + corps * 0.5 + metal * env(d, 0.001, 1.2)
        g = np.tanh(g * 1.6)
        return stereo(norm(g), largeur=0.6)
    if kind == "boom":  # grosse explosion lointaine : sub + grondement long
        sub = np.sin(2 * np.pi * np.cumsum(28 + 50 * np.exp(-t * 6)) / SR) * env(d, 0.003, 1.4)
        gr = filtre(bruit(rng, d), 25, 380) * env(d, 0.01, d * 0.35)
        cr = filtre(bruit(rng, d), 1500, 7000) * env(d, 0.002, 0.12) * (rng.random(len(t)) > 0.995)
        g = np.tanh((sub + gr * 1.2 + cr * 3) * 1.4)
        return stereo(norm(g), largeur=1.0)
    if kind == "explosion":  # explosion proche : souffle médium, crépitements, débris
        souffle = filtre(bruit(rng, d), 80, 2500) * env(d, 0.002, 0.45)
        sub = np.sin(2 * np.pi * np.cumsum(40 + 60 * np.exp(-t * 10)) / SR) * env(d, 0.002, 0.6)
        crepite = filtre(bruit(rng, d) * (rng.random(len(t)) > 0.985), 2000, 12000) * env(d, 0.05, d * 0.4)
        g = np.tanh((souffle * 1.2 + sub + crepite * 2.5) * 1.5)
        return stereo(norm(g), largeur=0.8)
    if kind == "tir":  # tir plasma : zap qui chute très vite
        f = 1500 * np.exp(-t * 28) + 180
        g = (np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.4 * np.sign(np.sin(2 * np.pi * np.cumsum(f * 0.5) / SR))) * env(d, 0.001, 0.09)
        g += filtre(bruit(rng, d), 2000, 9000) * env(d, 0.0005, 0.02) * 0.6
        return stereo(norm(g, 0.9), largeur=0.3)
    if kind == "canons":  # rafale de gros canons (≈ 8 coups/s)
        g = np.zeros(len(t))
        cadence = 0.12
        for k in range(int(d / cadence)):
            i0 = int((k * cadence + rng.uniform(0, 0.02)) * SR)
            n = min(len(t) - i0, int(0.35 * SR))
            tt = np.arange(n) / SR
            coup = np.sin(2 * np.pi * (55 + 40 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 12) + filtre(rng.normal(0, 1, n), 200, 4000) * np.exp(-tt * 40) * 0.7
            g[i0:i0 + n] += coup * rng.uniform(0.7, 1.0)
        return stereo(norm(np.tanh(g * 1.3)), largeur=0.7)
    if kind == "fouet":  # whoosh rapide de balayage caméra, panoramique gauche → droite
        b = bruit(rng, d)
        fc = 400 + 5000 * np.sin(np.pi * t / d) ** 2
        g = filtre(b, 300, 7000) * np.sin(np.pi * t / d) ** 3
        g = g * (0.6 + 0.4 * fc / fc.max())
        pan = np.linspace(-0.7, 0.7, len(t))
        return norm(np.stack([g * (1 - pan), g * (1 + pan)], 1), 0.9)
    if kind == "montee":  # riser : bruit + glissando, s'accélère jusqu'à la fin
        f = 120 + 1600 * (t / d) ** 2.5
        ton = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.5 * np.sin(2 * np.pi * np.cumsum(f * 1.5) / SR)
        b = filtre(bruit(rng, d), 1500, 14000)
        a = (t / d) ** 2.2
        trem = 0.75 + 0.25 * np.sin(2 * np.pi * np.cumsum(4 + 26 * (t / d) ** 2) / SR)
        return stereo(norm((ton * 0.5 + b * 0.8) * a * trem), largeur=0.9)
    if kind == "inverse":  # cymbale inversée qui aspire vers la coupe
        b = filtre(bruit(rng, d), 3000, 16000)
        return stereo(norm(b * (t / d) ** 3), largeur=1.0)
    if kind == "chute":  # sub-drop
        g = np.sin(2 * np.pi * np.cumsum(90 * np.exp(-t * 2.2) + 22) / SR) * env(d, 0.002, d * 0.5)
        return stereo(norm(np.tanh(g * 1.5)), largeur=0.0)
    if kind == "drone":  # nappe grave de l'ouverture (espace, menace)
        g = sum(np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) for f in (41.2, 41.7, 61.8, 82.6)) * 0.25
        g += filtre(bruit(rng, d), 40, 400) * 0.25
        g *= np.clip(t / 1.5, 0, 1) * np.clip((d - t) / 0.8, 0, 1)
        return stereo(norm(g, 0.8), largeur=1.0)
    if kind == "frappe":  # frappe de touche (saisie du prompt)
        g = filtre(bruit(rng, d), 1800, 9000) * env(d, 0.0003, 0.012) + np.sin(2 * np.pi * 180 * t) * env(d, 0.0005, 0.02) * 0.3
        return stereo(norm(g, 0.6), largeur=0.1)
    if kind == "clic":  # clic du bouton « Tourner »
        g = np.sin(2 * np.pi * 900 * t) * env(d, 0.0005, 0.03) + filtre(bruit(rng, d), 3000, 12000) * env(d, 0.0003, 0.008)
        return stereo(norm(g, 0.7), largeur=0.1)
    if kind == "souffle":  # souffle d'onde de choc qui traverse le cadre
        g = filtre(bruit(rng, d), 60, 1800) * np.sin(np.pi * np.clip(t / d, 0, 1)) ** 1.5
        return stereo(norm(g, 0.9), largeur=1.0)
    raise SystemExit(f"type inconnu : {kind}")


def ecrire(x: np.ndarray, chemin: str):
    x = np.clip(x, -1, 1)
    with wave.open(chemin, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype("<i2").tobytes())


if __name__ == "__main__":
    ecrire(generer(sys.argv[1], float(sys.argv[2]), np.random.default_rng(int(sys.argv[4]) if len(sys.argv) > 4 else 1)), sys.argv[3])
