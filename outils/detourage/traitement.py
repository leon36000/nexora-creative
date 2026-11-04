"""
Chaîne de détourage vidéo « rapide » de Nexora Creative, d'une vidéo et de clics à des séquences alpha vérifiées.

  extraction -> suivi par segments (SAM 2.1, raccord par rampes) -> matting (trimap + ViTMatte) -> stabilisation
  (flux optique) -> sorties (PNG 16 bits, RGBA 16 bits, EXR, ProRes 4444, WebM alpha, aperçus, composite) -> contrôle.

Tout est repris sur disque : un dossier de tâche contient `travail/` (trames, masques, alpha brut) indexé par des clés ;
relancer la même tâche saute ce qui est fait, changer un réglage n'invalide que ce qui en dépend.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import resource
import shutil
import subprocess
import time

import cv2
import numpy as np

import ecriture as E
import noyau as N


class Annule(Exception):
    pass


def ffmpeg_bin() -> str:
    for c in (os.environ.get('FFMPEG_BIN'), shutil.which('ffmpeg'),
              os.path.expanduser('~/nexora-creative-data/engine/ffmpeg/ffmpeg-7.0.2-arm64-static/ffmpeg')):
        if c and os.path.exists(c):
            return c
    raise RuntimeError('ffmpeg introuvable (variable FFMPEG_BIN)')


def ffprobe_bin() -> str:
    f = ffmpeg_bin()
    p = os.path.join(os.path.dirname(f), 'ffprobe')
    return p if os.path.exists(p) else 'ffprobe'


def lancer(args: list[str], timeout: int = 3600) -> None:
    r = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError(f'{os.path.basename(args[0])} a échoué : {(r.stderr or "").strip().splitlines()[-1:]}')


def sonder(chemin: str) -> dict:
    r = subprocess.run([ffprobe_bin(), '-v', 'error', '-print_format', 'json', '-show_streams', '-show_format', chemin],
                       capture_output=True, text=True, timeout=60)
    j = json.loads(r.stdout or '{}')
    v = next((s for s in j.get('streams', []) if s.get('codec_type') == 'video'), None)
    if not v:
        raise RuntimeError('aucune piste vidéo')
    num, den = (v.get('avg_frame_rate') or v.get('r_frame_rate') or '24/1').split('/')
    fps = float(num) / float(den or 1) if float(den or 1) else 24.0
    return {'largeur': int(v['width']), 'hauteur': int(v['height']), 'fps': fps or 24.0,
            'duree': float(j.get('format', {}).get('duration') or v.get('duration') or 0),
            'audio': any(s.get('codec_type') == 'audio' for s in j.get('streams', [])), 'pix_fmt': v.get('pix_fmt')}


DEFAUTS = {
    'largeur_max': 1920, 'debut_s': 0.0, 'duree_s': None, 'invites': [], 'segment': {'taille': 96, 'recouvrement': 12},
    'sam': 'large', 'matting': 'vitmatte-small', 'bande': 0.015, 'lissage': 1.0, 'etapes': ['suivi', 'matting', 'sorties'],
    'sorties': {'png16': True, 'rgba16': True, 'exr': True, 'prores': True, 'webm': True, 'matte': True, 'apercu': True},
    'composite': None, 'conserver_travail': True, 'mesure_scintillement': True,
}


def regler(params: dict) -> dict:
    p = json.loads(json.dumps(DEFAUTS))
    for k, v in (params or {}).items():
        if isinstance(p.get(k), dict) and isinstance(v, dict):
            p[k].update(v)
        else:
            p[k] = v
    return p


def _cle(*parts) -> str:
    return hashlib.sha1(json.dumps(parts, sort_keys=True, default=str).encode()).hexdigest()[:16]


def _lire(c: str, flags=cv2.IMREAD_COLOR) -> np.ndarray:
    im = cv2.imread(c, flags)
    if im is None:
        raise RuntimeError(f'image illisible : {c}')
    return cv2.cvtColor(im, cv2.COLOR_BGR2RGB) if im.ndim == 3 and im.shape[2] == 3 else im


def _cle_dossier(dossier: str, cle: str) -> bool:
    """True si le dossier est valide pour `cle` ; sinon le vide et le marque."""
    fic = os.path.join(dossier, 'cle.txt')
    ok = os.path.exists(fic) and open(fic).read().strip() == cle
    if not ok:
        shutil.rmtree(dossier, ignore_errors=True)
        os.makedirs(dossier, exist_ok=True)
        open(fic, 'w').write(cle)
    return ok


class Tache:
    """Une exécution : dossier, état persistant, annulation, chronométrage par étape."""

    def __init__(self, dossier: str, modeles, params: dict, annule=lambda: False):
        self.d = dossier
        self.mod = modeles
        self.p = regler(params)
        self.annule = annule
        self.t0 = time.time()
        self.etapes: dict[str, float] = {}
        self.etat = {'etat': 'en_cours', 'etape': 'extraction', 'progression': 0.0, 'message': '', 'mesures': {}, 'sorties': {}}
        os.makedirs(os.path.join(dossier, 'travail'), exist_ok=True)

    # ---- état
    def maj(self, etape=None, fraction=None, message=None, **plus):
        e = self.etat
        if etape:
            e['etape'] = etape
        if fraction is not None:
            e['progression'] = round(min(1.0, max(0.0, fraction)), 4)
        if message is not None:
            e['message'] = message
        e.update(plus)
        e['maj'] = time.time()
        tmp = os.path.join(self.d, 'etat.json.tmp')
        json.dump(e, open(tmp, 'w'), ensure_ascii=False)
        os.replace(tmp, os.path.join(self.d, 'etat.json'))

    def verifier(self):
        if self.annule():
            raise Annule()

    def _chrono(self, nom, t):
        self.etapes[nom] = round(self.etapes.get(nom, 0) + time.time() - t, 2)

    # ---- 1. extraction
    def extraire(self):
        t = time.time()
        p, d = self.p, self.d
        src = os.path.join(d, p.get('source', 'source.mp4'))
        info = sonder(src)
        w = info['largeur']
        sc = min(1.0, p['largeur_max'] / w)
        W, H = int(round(w * sc / 2) * 2), int(round(info['hauteur'] * sc / 2) * 2)
        self.info = {**info, 'largeur_traitee': W, 'hauteur_traitee': H}
        # garde-fou disque : ≈ 0,08 Go par seconde de vidéo à 720p (images + masques + sorties), proportionnel aux pixels
        duree = min(p['duree_s'] or 1e9, max(0.0, info['duree'] - p['debut_s']))
        besoin = duree * 0.08e9 * (W * H) / (1280 * 720)
        libre = shutil.disk_usage(d).free
        if besoin > libre - 3e9:
            raise RuntimeError(f'espace disque insuffisant sur la machine GPU : {besoin / 1e9:.1f} Go nécessaires, {libre / 1e9:.1f} Go libres (réduis la durée ou la largeur)')
        dossier = os.path.join(d, 'travail', 'trames')
        cle = _cle(os.stat(src).st_size, int(os.stat(src).st_mtime), W, H, p['debut_s'], p['duree_s'])
        if not _cle_dossier(dossier, cle) or not os.listdir(dossier) or len(os.listdir(dossier)) < 2:
            cmd = [ffmpeg_bin(), '-v', 'error', '-y', '-ss', str(p['debut_s'])]
            if p['duree_s']:
                cmd += ['-t', str(p['duree_s'])]
            cmd += ['-i', src, '-vf', f'scale={W}:{H}:flags=lanczos', '-pix_fmt', 'rgb24', '-start_number', '0',
                    os.path.join(dossier, '%06d.png')]
            lancer(cmd)
        self.n = len([f for f in os.listdir(dossier) if f.endswith('.png')])
        self.cle_trames = cle
        self.coupures = self.detecter_coupures(src, p['debut_s'], p['duree_s'], info['fps'])
        self._chrono('extraction', t)

    def detecter_coupures(self, src: str, debut: float, duree, fps: float) -> list[int]:
        """Images de début de plan (changements de plan) : le suivi ne doit jamais traverser une coupure."""
        cmd = [ffmpeg_bin(), '-hide_banner', '-ss', str(debut)] + (['-t', str(duree)] if duree else []) + [
            '-i', src, '-vf', "select='gt(scene,0.38)',showinfo", '-an', '-f', 'null', '-']
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        out = sorted({int(round(float(m) * fps)) for m in re.findall(r'pts_time:([0-9.]+)', r.stderr)})
        return [c for c in out if 0 < c < self.n]

    def trame(self, i: int) -> np.ndarray:
        return _lire(os.path.join(self.d, 'travail', 'trames', f'{i:06d}.png'))

    # ---- 2. suivi par segments
    def suivre(self):
        t = time.time()
        p, d, n = self.p, self.d, self.n
        H, W = self.info['hauteur_traitee'], self.info['largeur_traitee']
        if not p['invites']:
            raise ValueError('aucun clic : choisis le sujet sur une image')
        invites = sorted(p['invites'], key=lambda g: g['image'])
        for g in invites:
            if not 0 <= g['image'] < n:
                raise ValueError(f'image {g["image"]} hors de la plage 0..{n - 1}')
        seg = p['segment']
        rec = max(2, min(int(seg['recouvrement']), int(seg['taille']) - 1))  # ≥ 2 : le raccord en a besoin pour graîner
        segs = N.plan_plans(n, self.coupures, seg['taille'], rec)
        self.segs = segs
        self.cle_suivi = _cle(self.cle_trames, invites, seg, p['sam'], self.coupures)
        dsuivi = os.path.join(d, 'travail', 'suivi')
        _cle_dossier(dsuivi, self.cle_suivi)
        dmask = os.path.join(d, 'travail', 'masques')
        valide_masques = _cle_dossier(dmask, self.cle_suivi) and len([f for f in os.listdir(dmask) if f.endswith('.png')]) == n
        visibles = np.zeros(n, bool)
        fichiers = {i: os.path.join(dsuivi, f'seg_{i}.npz') for i in range(len(segs))}
        plans_sans_clic = []
        fait = 0

        def charge(i):
            z = np.load(fichiers[i])
            return z['p'], z['vis']

        if not valide_masques:
            for plan in sorted({s['plan'] for s in segs}):
                idx = [i for i, s in enumerate(segs) if s['plan'] == plan]
                debut_plan, fin_plan = segs[idx[0]]['debut'], segs[idx[-1]]['fin']
                clics = [g for g in invites if debut_plan <= g['image'] < fin_plan]
                if not clics:  # un plan sans clic n'a pas de sujet : masque vide, signalé à l'utilisateur
                    plans_sans_clic.append([debut_plan, fin_plan - 1])
                    for i in idx:
                        s = segs[i]
                        np.savez_compressed(fichiers[i], p=np.zeros((s['fin'] - s['debut'], H, W), np.float16), vis=np.zeros(s['fin'] - s['debut'], bool))
                    fait += len(idx)
                    continue
                premier = clics[0]['image']
                maison = next(i for i in idx if segs[i]['debut'] <= premier < segs[i]['fin'])
                ordre = [maison] + [i for i in idx if i > maison] + [i for i in reversed(idx) if i < maison]
                for i in ordre:
                    self.verifier()
                    s = segs[i]
                    self.maj('suivi', 0.05 + 0.30 * fait / len(segs), f'suivi du segment {fait + 1}/{len(segs)}')
                    if os.path.exists(fichiers[i]):
                        fait += 1
                        continue
                    trames = [self.trame(f) for f in range(s['debut'], s['fin'])]
                    graines = {g['image'] - s['debut']: dict(g) for g in clics if s['debut'] <= g['image'] < s['fin']}
                    if i == maison:
                        depart, sens = min(graines), 'deux'
                    elif i > maison:  # on repart du dernier masque du segment précédent, à l'image de début de celui-ci
                        pp, _ = charge(i - 1)
                        graines.setdefault(0, {})['masque'] = pp[s['debut'] - segs[i - 1]['debut']].astype(np.float32)
                        depart, sens = 0, 'avant'
                    else:  # segments avant l'image de départ : on remonte depuis le début du segment suivant
                        pp, _ = charge(i + 1)
                        k = s['fin'] - 1
                        graines.setdefault(k - s['debut'], {})['masque'] = pp[k - segs[i + 1]['debut']].astype(np.float32)
                        depart, sens = k - s['debut'], 'arriere'
                    proba, vis = self.mod.suivre(trames, graines, depart, sens, p['sam'], self.annule)
                    np.savez_compressed(fichiers[i], p=proba, vis=vis)
                    fait += 1
            # raccord en flux : les images avant le début du segment suivant sont définitives
            cum = {}
            for i, s in enumerate(segs):
                pp, vv = charge(i)
                for k in range(pp.shape[0]):
                    f = s['debut'] + k
                    w = N.poids_segment(f, i, segs, rec)
                    if w > 0:
                        a, b = cum.get(f, (0.0, 0.0))
                        cum[f] = (a + pp[k].astype(np.float32) * w, b + w)
                        if vv[k] and w >= 0.5:
                            visibles[f] = True
                fin_def = segs[i + 1]['debut'] if i + 1 < len(segs) else n
                for f in [x for x in sorted(cum) if x < fin_def]:
                    a, b = cum.pop(f)
                    m = np.clip(a / max(b, 1e-6), 0, 1)
                    cv2.imwrite(os.path.join(dmask, f'{f:06d}.png'), np.rint(m * 255).astype(np.uint8))
            json.dump({'visibles': visibles.tolist(), 'plans_sans_clic': plans_sans_clic}, open(os.path.join(dmask, 'visibles.json'), 'w'))
        else:
            j = json.load(open(os.path.join(dmask, 'visibles.json')))
            visibles, plans_sans_clic = np.array(j['visibles'], bool), j['plans_sans_clic']
        # intervalles d'occlusion (images où l'objet n'est pas visible)
        occ, debut = [], None
        for f in range(n):
            if not visibles[f] and debut is None:
                debut = f
            if visibles[f] and debut is not None:
                occ.append([debut, f - 1])
                debut = None
        if debut is not None:
            occ.append([debut, n - 1])
        self.etat['mesures'].update({'segments': len(segs), 'images': n, 'occlusions': occ, 'visibles': int(visibles.sum()),
                                     'coupures': self.coupures, 'plans_sans_clic': plans_sans_clic})
        self._chrono('suivi', t)

    def masque(self, f: int) -> np.ndarray:
        return cv2.imread(os.path.join(self.d, 'travail', 'masques', f'{f:06d}.png'), cv2.IMREAD_GRAYSCALE).astype(np.float32) / 255.0

    # ---- 3. matting
    def apparier(self):
        t = time.time()
        p, d, n = self.p, self.d, self.n
        self.cle_mat = _cle(self.cle_suivi, p['matting'], p['bande'])
        dossier = os.path.join(d, 'travail', 'alpha_brut')
        _cle_dossier(dossier, self.cle_mat)
        H, W = self.info['hauteur_traitee'], self.info['largeur_traitee']
        bande = N.largeur_bande(H, W, p['bande'])
        for f in range(n):
            self.verifier()
            sortie = os.path.join(dossier, f'{f:06d}.png')
            if os.path.exists(sortie):
                continue
            self.maj('matting', 0.35 + 0.35 * f / n, f'matting image {f + 1}/{n}')
            m = self.masque(f)
            if p['matting'] == 'aucun' or not (m > 0.5).any():
                a = m  # sans matting : la probabilité de SAM sert d'alpha
            else:
                tri = N.trimap(m, bande, bande)
                a = np.zeros_like(m)
                b = N.boite(tri > 0, 16)
                if b:
                    x0, y0, x1, y1 = b
                    rgb = self.trame(f)[y0:y1, x0:x1]
                    a_c = self.mod.affiner(np.ascontiguousarray(rgb), np.ascontiguousarray(tri[y0:y1, x0:x1]), p['matting'])
                    a[y0:y1, x0:x1] = a_c
                a = N.fusionner(m, a, tri)
            E.ecrire_png16(sortie, E.alpha_vers_u16(a), niveau=2)
        self._chrono('matting', t)

    def alpha_brut(self, f: int) -> np.ndarray:
        r = cv2.imread(os.path.join(self.d, 'travail', 'alpha_brut', f'{f:06d}.png'), cv2.IMREAD_UNCHANGED)
        return r.astype(np.float32) / 65535.0

    # ---- 4 et 5. stabilisation + sorties
    def sortir(self):
        t = time.time()
        p, d, n = self.p, self.d, self.n
        so = p['sorties']
        cle = _cle(self.cle_mat, p['lissage'], so)
        racine = os.path.join(d, 'sorties')
        _cle_dossier(racine, cle)
        dirs = {k: os.path.join(racine, k) for k in ('alpha', 'rgba16', 'exr', 'alpha_exr')}
        for k, v in dirs.items():
            if (k == 'alpha' and so['png16']) or (k == 'rgba16' and (so['rgba16'] or so['prores'] or so['webm'] or p['composite'] or so['apercu'])) \
                    or (k in ('exr', 'alpha_exr') and so['exr']):
                os.makedirs(v, exist_ok=True)
        cache: dict[int, tuple] = {}

        def charge(i):
            if i not in cache:
                cache[i] = (self.alpha_brut(i), self.trame(i))
            for k in [k for k in cache if k < i - 2]:
                del cache[k]
            return cache[i]

        av = ap = 0.0
        nm = 0
        prec_brut = prec_lisse = None
        pas = 1 if n <= 240 else 4
        for f in range(n):
            self.verifier()
            self.maj('sorties', 0.70 + 0.28 * f / n, f'stabilisation et export image {f + 1}/{n}')
            a, rgb = charge(f)
            voisines = [charge(u) for u in (f - 1, f + 1) if 0 <= u < n]
            al = N.lisser_trame(a, rgb, voisines, force=p['lissage']) if p['lissage'] > 0 else a
            if p['mesure_scintillement'] and f > 0 and f % pas == 0 and prec_brut is not None:
                e1 = N.ecart_temporel(a, rgb, prec_brut[0], prec_brut[1])
                e2 = N.ecart_temporel(al, rgb, prec_lisse, prec_brut[1])
                if e1 is not None and e2 is not None:
                    av += e1
                    ap += e2
                    nm += 1
            prec_brut, prec_lisse = (a, rgb), al
            nom = f'{f:06d}'
            fg = N.avant_plan(rgb, al)
            if so['png16']:
                E.ecrire_png16(os.path.join(dirs['alpha'], f'alpha_{nom}.png'), E.alpha_vers_u16(al), niveau=2)
            if os.path.isdir(dirs['rgba16']):
                E.ecrire_png16(os.path.join(dirs['rgba16'], f'rgba_{nom}.png'), E.rgba_vers_u16(fg, al), niveau=2)
            if so['exr']:
                lin = N.srgb_vers_lineaire(fg)
                prem = np.concatenate([lin * al[..., None], al[..., None]], axis=2)
                E.ecrire_exr(os.path.join(dirs['exr'], f'rgba_{nom}.exr'), rgba=prem, premultiplie=True,
                             commentaire='couleur lineaire sRGB->lineaire, premultipliee par alpha')
                E.ecrire_exr(os.path.join(dirs['alpha_exr'], f'alpha_{nom}.exr'), alpha=al)
        if nm:
            self.etat['mesures']['scintillement'] = {'avant': round(av / nm, 5), 'apres': round(ap / nm, 5),
                                                     'gain': round(1 - (ap / av if av else 1), 3), 'paires': nm}
        self._chrono('stabilisation_et_images', t)
        t = time.time()
        self.videos(racine)
        self._chrono('encodage', t)
        self.controler(racine)

    # ---- vidéos
    def videos(self, racine: str):
        p, n = self.p, self.n
        so, fps = p['sorties'], self.info['fps']
        W, H = self.info['largeur_traitee'], self.info['hauteur_traitee']
        rgba = os.path.join(racine, 'rgba16', 'rgba_%06d.png')
        ff = ffmpeg_bin()
        entree = ['-framerate', f'{fps}', '-i', rgba]
        if so['prores']:
            self.maj('encodage', 0.98, 'ProRes 4444')
            lancer([ff, '-v', 'error', '-y', *entree, '-c:v', 'prores_ks', '-profile:v', '4444', '-pix_fmt', 'yuva444p10le',
                    '-alpha_bits', '16', '-vendor', 'apl0', os.path.join(racine, 'detourage-prores4444.mov')])
        if so['webm']:
            lancer([ff, '-v', 'error', '-y', *entree, '-c:v', 'libvpx-vp9', '-pix_fmt', 'yuva420p', '-b:v', '0', '-crf', '26',
                    '-auto-alt-ref', '0', '-row-mt', '1', os.path.join(racine, 'detourage-alpha.webm')])
        if so['matte']:
            lancer([ff, '-v', 'error', '-y', '-framerate', f'{fps}', '-i', os.path.join(racine, 'alpha', 'alpha_%06d.png'),
                    '-c:v', 'libx264', '-crf', '16', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', os.path.join(racine, 'matte.mp4')])
        if so['apercu']:
            cv2.imwrite(os.path.join(racine, 'echecs.png'), cv2.cvtColor((N.echecs(H, W) * 255).astype(np.uint8), cv2.COLOR_RGB2BGR))
            lancer([ff, '-v', 'error', '-y', '-loop', '1', '-framerate', f'{fps}', '-i', os.path.join(racine, 'echecs.png'), *entree,
                    '-filter_complex', '[0:v][1:v]overlay=format=auto:shortest=1,format=yuv420p[v]', '-map', '[v]',
                    '-c:v', 'libx264', '-crf', '17', '-movflags', '+faststart', os.path.join(racine, 'apercu-echecs.mp4')])
        c = p['composite']
        if c:
            self.maj('encodage', 0.99, 'composition sur le nouveau fond')
            src = os.path.join(self.d, p.get('source', 'source.mp4'))
            if c['type'] == 'couleur':
                valeur = str(c.get('valeur', '#00ff00')).lstrip('#')
                if len(valeur) != 6 or any(x not in '0123456789abcdefABCDEF' for x in valeur):
                    raise ValueError('couleur de fond invalide')
                fond = ['-f', 'lavfi', '-i', f'color=c=0x{valeur}:s={W}x{H}:r={fps}']
                traitement = '[1:v]setsar=1[bg]'
            elif c['type'] == 'image':
                fond = ['-loop', '1', '-framerate', f'{fps}', '-i', os.path.join(self.d, os.path.basename(c['fichier']))]
                traitement = f'[1:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1[bg]'
            elif c['type'] == 'video':
                fond = ['-stream_loop', '-1', '-i', os.path.join(self.d, os.path.basename(c['fichier']))]
                traitement = f'[1:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},fps={fps},setsar=1[bg]'
            elif c['type'] == 'flou':
                fond = ['-ss', str(p['debut_s']), '-i', src]
                traitement = f'[1:v]scale={W}:{H},gblur=sigma=24,setsar=1[bg]'
            else:
                raise ValueError('type de fond inconnu')
            audio = ['-ss', str(p['debut_s']), *( ['-t', str(p['duree_s'])] if p['duree_s'] else []), '-i', src]
            lancer([ff, '-v', 'error', '-y', *entree, *fond, *audio,
                    '-filter_complex', f'{traitement};[bg][0:v]overlay=format=auto:shortest=1,format=yuv420p[v]',
                    '-map', '[v]', '-map', '2:a?', '-c:v', 'libx264', '-crf', '16', '-c:a', 'aac', '-shortest',
                    '-movflags', '+faststart', os.path.join(racine, 'composite.mp4')])

    # ---- contrôle des fichiers produits
    def controler(self, racine: str):
        """Relit ce qui a été écrit et le déclare dans l'état : profondeur de bits, prémultiplication, comptes, formats."""
        n, ctl = self.n, {}
        compte = lambda sous, ext: len([f for f in os.listdir(os.path.join(racine, sous)) if f.endswith(ext)]) if os.path.isdir(os.path.join(racine, sous)) else 0
        if os.path.isdir(os.path.join(racine, 'alpha')):
            h = E.entete_png(os.path.join(racine, 'alpha', f'alpha_{0:06d}.png'))
            ctl['alpha_png'] = {'images': compte('alpha', '.png'), 'bits': h['bits'], 'type': 'gris', 'alpha': 'droit (non prémultiplié)'}
        if os.path.isdir(os.path.join(racine, 'rgba16')):
            h = E.entete_png(os.path.join(racine, 'rgba16', f'rgba_{0:06d}.png'))
            ctl['rgba_png'] = {'images': compte('rgba16', '.png'), 'bits': h['bits'], 'type': 'RGBA', 'alpha': 'droit (non prémultiplié), avant-plan estimé'}
        if os.path.isdir(os.path.join(racine, 'exr')):
            x = E.lire_exr(os.path.join(racine, 'exr', f'rgba_{n // 2:06d}.exr'))
            ctl['exr'] = {'images': compte('exr', '.exr'), 'bits': sorted(set(x['bits'].values())), 'canaux': sorted(x['canaux']),
                          'alpha': x['alpha'], 'compression': 'ZIP16', 'espace': 'linéaire',
                          'couleur_inferieure_alpha': bool((x['canaux']['R'] <= x['canaux']['A'] + 2e-3).all())}
        for nom in ('detourage-prores4444.mov', 'detourage-alpha.webm'):
            c = os.path.join(racine, nom)
            if os.path.exists(c):
                r = subprocess.run([ffprobe_bin(), '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                                    'stream=codec_name,pix_fmt,nb_frames,width,height', '-of', 'json', c], capture_output=True, text=True)
                ctl[nom] = (json.loads(r.stdout or '{}').get('streams') or [{}])[0]
        self.etat['mesures']['controle'] = ctl
        self.lister(racine)

    def lister(self, racine: str):
        """Inscrit dans l'état les fichiers de sortie (taille) et le nombre d'images de chaque séquence."""
        compte = lambda sous, ext: len([f for f in os.listdir(os.path.join(racine, sous)) if f.endswith(ext)]) if os.path.isdir(os.path.join(racine, sous)) else 0
        fichiers = {}
        for dp, _, fs in os.walk(racine):
            for f in fs:
                rel = os.path.relpath(os.path.join(dp, f), racine)
                if os.sep in rel:  # les séquences se listent par dossier, pas fichier par fichier
                    continue
                fichiers[rel] = os.path.getsize(os.path.join(dp, f))
        self.etat['sorties'] = {'fichiers': fichiers, 'sequences': {s: compte(s, '.png' if s in ('alpha', 'rgba16') else '.exr')
                                                                       for s in ('alpha', 'rgba16', 'exr', 'alpha_exr') if os.path.isdir(os.path.join(racine, s))}}

    # ---- aperçu du suivi seul
    def apercu_suivi(self):
        """Vidéo de contrôle du suivi : le masque en rouge translucide sur la vidéo (étape rapide avant le matting)."""
        t = time.time()
        d, n = self.d, self.n
        dossier = os.path.join(d, 'travail', 'apercu_suivi')
        os.makedirs(dossier, exist_ok=True)
        for f in range(n):
            self.verifier()
            m = self.masque(f)[..., None]
            im = self.trame(f).astype(np.float32) / 255.0
            rouge = np.array([1.0, 0.1, 0.2], np.float32)
            out = im * (1 - 0.55 * m) + rouge * 0.55 * m
            cv2.imwrite(os.path.join(dossier, f'{f:06d}.jpg'), cv2.cvtColor((out * 255).astype(np.uint8), cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 92])
        os.makedirs(os.path.join(d, 'sorties'), exist_ok=True)
        lancer([ffmpeg_bin(), '-v', 'error', '-y', '-framerate', f"{self.info['fps']}", '-i', os.path.join(dossier, '%06d.jpg'),
                '-c:v', 'libx264', '-crf', '20', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', os.path.join(d, 'sorties', 'suivi.mp4')])
        self._chrono('apercu_suivi', t)

    # ---- orchestration
    def executer(self) -> dict:
        try:
            self.maj('extraction', 0.01, 'extraction des images')
            self.extraire()
            self.verifier()
            etapes = self.p['etapes']
            if 'suivi' in etapes:
                self.suivre()
                if 'matting' not in etapes:
                    self.maj('suivi', 0.4, 'aperçu du suivi')
                    self.apercu_suivi()
                    self.lister(os.path.join(self.d, 'sorties'))
            if 'matting' in etapes:
                self.apparier()
            if 'sorties' in etapes:
                self.sortir()
            m = self.etat['mesures']
            m['temps_etapes_s'] = self.etapes
            m['temps_total_s'] = round(time.time() - self.t0, 1)
            m['ram_pic_go'] = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6, 2)
            m['gpu'] = self.mod.etat()
            m['disque_travail_go'] = round(taille_dossier(os.path.join(self.d, 'travail')) / 1e9, 3)
            m['disque_sorties_go'] = round(taille_dossier(os.path.join(self.d, 'sorties')) / 1e9, 3)
            if not self.p['conserver_travail']:
                shutil.rmtree(os.path.join(self.d, 'travail'), ignore_errors=True)
            self.maj('termine', 1.0, 'terminé', etat='termine')
        except (Annule, InterruptedError):
            self.maj(message='annulé', etat='annule')
        except Exception as e:  # noqa: BLE001 - l'état porte l'erreur, le serveur la renvoie telle quelle
            self.maj(message=f'{type(e).__name__}: {e}', etat='erreur')
        return self.etat


def taille_dossier(c: str) -> int:
    t = 0
    for dp, _, fs in os.walk(c):
        for f in fs:
            try:
                t += os.path.getsize(os.path.join(dp, f))
            except OSError:
                pass
    return t
