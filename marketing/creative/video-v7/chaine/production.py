"""Adaptateurs de production. Le mode à blanc n'ouvre aucune connexion réseau."""
import base64
import contextlib
import csv
import fcntl
import hashlib
import io
import json
import math
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

from commun import (ICI, V7, DATA, absolu, banc, budget, calage_auto, duree, ecrire_json,
                    journal, juge, lignes, lire_json, module, montage_module, moteur,
                    recette, substituer, unites, musique_legacy)

ENGINE = Path.home() / 'nexora-creative-data/engine'


def binaire(nom):
    # Le dossier demandé reste prioritaire (en particulier pour telephone).
    found = sorted((ENGINE / 'ffmpeg').glob(f'*/{nom}'))
    if found:
        return str(found[0])
    if shutil.which(nom):
        return shutil.which(nom)
    raise RuntimeError(f'{nom} introuvable')


def commande(args, **kw):
    try:
        p = subprocess.run(list(map(str, args)), check=True, capture_output=True, **kw)
    except subprocess.CalledProcessError as e:
        message = e.stderr.decode(errors='replace') if isinstance(e.stderr, bytes) else (e.stderr or '')
        raise RuntimeError(f'{Path(str(args[0])).name} a échoué (code {e.returncode}) : {message[-1800:]}') from None
    return p.stdout


def ff(*args):
    return commande([binaire('ffmpeg'), '-v', 'error', '-nostdin', '-y', *args])


def sonder(f):
    return json.loads(commande([binaire('ffprobe'), '-v', 'error', '-show_format', '-show_streams', '-of', 'json', f]))


def sha(f):
    h = hashlib.sha256()
    with Path(f).open('rb') as src:
        for bloc in iter(lambda: src.read(1024*1024), b''):
            h.update(bloc)
    return h.hexdigest()


def signature(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()[:16]


@contextlib.contextmanager
def verrou(f):
    f.parent.mkdir(parents=True, exist_ok=True)
    with f.open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError(f'Une commande travaille déjà pour cette équipe : {f.name}') from None
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


class Comfy:
    """FIFO normale ; aucun numéro ni priorité ne sont fournis au serveur."""
    def __init__(self, url):
        self.url = url

    def json(self, path, data=None):
        raw = moteur().http(self.url + path, None if data is None else json.dumps(data).encode(),
                            {'Content-Type': 'application/json'}, timeout=120)
        return json.loads(raw)

    def queue(self):
        q = self.json('/queue')
        return q.get('queue_running', []) + q.get('queue_pending', [])

    @staticmethod
    def appartient(item, prefix):
        graph = item[2]
        return any(str(n.get('inputs', {}).get('filename_prefix', '')).startswith(prefix)
                   for n in graph.values() if isinstance(n, dict))

    def compte(self, prefix):
        return sum(self.appartient(q, prefix) for q in self.queue())

    def retrouver(self, prefix):
        for item in self.queue():
            if self.appartient(item, prefix):
                return item[1]
        for pid, h in self.json('/history').items():
            prompt = h.get('prompt')
            if prompt and self.appartient(prompt, prefix):
                return pid
        return None

    def soumettre(self, graph):
        return self.json('/prompt', {'prompt': graph})['prompt_id']

    def resultat(self, pid, destination):
        h = self.json('/history/' + urllib.parse.quote(pid)).get(pid)
        if not h:
            return None
        st = h.get('status', {})
        if st.get('status_str') == 'error':
            raise RuntimeError(f'ComfyUI : échec du travail {pid}')
        if not st.get('completed'):
            return None
        fichiers = [f for out in h.get('outputs', {}).values()
                    for key in ('video', 'images', 'gifs', 'audio') for f in out.get(key, [])]
        if not fichiers:
            raise RuntimeError(f'ComfyUI : aucune sortie pour {pid}')
        f = fichiers[0]
        q = urllib.parse.urlencode({k: f.get(k, 'output' if k == 'type' else '')
                                    for k in ('filename', 'subfolder', 'type')})
        data = moteur().http(self.url + '/view?' + q, timeout=600)
        destination.parent.mkdir(parents=True, exist_ok=True)
        temp = destination.with_suffix(destination.suffix + '.part')
        temp.write_bytes(data)
        temp.replace(destination)
        ts = {m[0]: m[1].get('timestamp') for m in st.get('messages', []) if isinstance(m[1], dict)}
        secs = None
        if ts.get('execution_start') is not None and ts.get('execution_success') is not None:
            secs = (ts['execution_success']-ts['execution_start'])/1000
        return {'fichier': str(destination), 'secondesMoteur': secs}


class Atelier:
    def __init__(self, d, base, travail, blanc=False, poll=4):
        self.d, self.base, self.travail = d, base, Path(travail)
        self.blanc, self.poll = blanc, poll
        self.equipe = d['equipe']
        self.couts = self.travail / 'openrouter.jsonl'
        self._key = None
        self._secret_module = None

    def cle(self):
        if self._key is None:
            for line in (Path.home() / 'Desktop/Deepinfra.env').read_text().splitlines():
                k, sep, v = line.partition(':')
                if sep and k.strip().lower() == 'openrouter':
                    self._key = v.strip()
                    break
            if not self._key:
                raise RuntimeError('Clé OpenRouter absente de Deepinfra.env')
        return self._key

    def cout(self, obj, modele, operation):
        usage = obj.get('usage') or {}
        journal(self.couts, {'t': time.time(), 'modele': modele, 'operation': operation,
                             'reponse_id': obj.get('id'), 'cost': usage.get('cost'), 'usage': usage})

    def post(self, url, corps, timeout=300):
        if self.blanc:
            raise RuntimeError('Appel réseau interdit en mode à blanc')
        if corps.get('model') == 'google/gemini-4-argon':
            corps = {**corps, 'provider': {'order': ['google-ai-studio/flex'], 'allow_fallbacks': False}}
        req = urllib.request.Request(url, data=json.dumps(corps).encode(),
                                     headers={'Authorization': 'Bearer '+self.cle(), 'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read()
                # Les réponses speech binaires n'ont pas nécessairement de coût.
                header_cost = resp.headers.get('x-openrouter-cost')
        except urllib.error.HTTPError as e:
            # Ne jamais recopier une réponse distante contenant potentiellement des secrets.
            raise RuntimeError(f'OpenRouter HTTP {e.code}') from None
        try:
            obj = json.loads(raw)
        except (ValueError, UnicodeDecodeError):
            obj = {'usage': {'cost': float(header_cost) if header_cost else None}}
        self.cout(obj, corps.get('model'), url.rsplit('/', 1)[-1])
        return raw

    def demander(self, contenu, temperature=0.):
        obj = json.loads(self.post('https://openrouter.ai/api/v1/chat/completions', {
            'model': 'google/gemini-4-argon', 'temperature': temperature,
            'response_format': {'type': 'json_object'}, 'messages': [{'role': 'user', 'content': contenu}]}))
        txt = obj['choices'][0]['message']['content']
        return json.loads(txt[txt.find('{'):txt.rfind('}')+1])

    def noter(self, f):
        if self.blanc:
            return {'reel': 8., 'defauts': [], 'doublure': True}
        j = juge()
        from unittest.mock import patch
        with patch.object(j, 'image_de', image_juge), patch.object(j, 'demander', self.demander):
            result = j.note(f)  # Vidéo : exactement trois images, selon le contrat du juge.
        if not isinstance(result.get('reel'), (int, float)) or not 0 <= result['reel'] <= 10:
            raise ValueError('Note réel invalide renvoyée par le juge')
        return result

    def factice(self, f, secondes=6, portrait=False, image=False, audio=False):
        f.parent.mkdir(parents=True, exist_ok=True)
        if image:
            from PIL import Image, ImageDraw
            im = Image.new('RGB', (180, 320) if portrait else (320, 180), (36, 49, 62))
            ImageDraw.Draw(im).text((12, 30), 'DOUBLURE '+f.stem, fill='white')
            im.save(f)
        elif audio:
            # Un battement à 120 BPM, avec vraie dynamique et amplitude de test.
            ff('-f', 'lavfi', '-i', fr'aevalsrc=0.18*sin(2*PI*220*t)*exp(-12*mod(t\,0.5)):s=48000:d={secondes}',
               '-ac', '2', '-c:a', 'pcm_s16le', f)
        else:
            size = '180x320' if portrait else '320x180'
            ff('-f', 'lavfi', '-i', f'testsrc2=size={size}:rate=24:duration={secondes}',
               '-f', 'lavfi', '-i', f'sine=frequency=220:duration={secondes}',
               '-c:v', 'libx264', '-preset', 'ultrafast', '-pix_fmt', 'yuv420p',
               '-c:a', 'aac', '-ar', '48000', '-ac', '2', '-shortest', f)

    def cles(self):
        self._rendus('cles', self.d['cles'], Comfy(moteur().IMG_COMFY) if not self.blanc else None)

    def plans(self):
        self._rendus('plans', self.d['plans'], Comfy(moteur().H3_COMFY) if not self.blanc else None)

    def _rendus(self, groupe, specs, client):
        """Ordonnanceur asynchrone persistant, un verrou par équipe et étape.

        L'intention est fsync avant POST ; une réponse perdue est retrouvée par
        préfixe exact. Si le serveur a perdu son historique, on refuse de doubler.
        """
        root = self.travail / groupe
        root.mkdir(parents=True, exist_ok=True)
        state_file = root / 'etat.json'
        state = lire_json(state_file, {'jobs': {}, 'choix': {}})
        jobs, choix = state['jobs'], state['choix']
        video = groupe == 'plans'
        prefix_team = f'v7-{self.equipe}/'
        log = root / 'journal.jsonl'
        def sauver():
            ecrire_json(state_file, state)
        def empreinte(spec):
            extra = {'checkpoint': recette().PRISM, 'etapes': 8, 'decalage': [12, 3]} if video else {'negatif': recette().NEG}
            if video:
                key = self.travail / 'cles' / (spec['cle']+'.png')
                if not key.exists():
                    raise ValueError(f'Image clé absente : {key}')
                extra['image_sha256'] = sha(key)
            return signature({**spec, **extra})
        signatures = {s['id']: empreinte(s) for s in specs}
        def nom(spec, prise):
            return f'{spec["id"]}-{signatures[spec["id"]]}-g{spec["graine"]+prise*1000}'
        def creer(spec, prise):
            ident = nom(spec, prise)
            if ident not in jobs:
                jobs[ident] = {'id': spec['id'], 'signature': signatures[spec['id']], 'prise': prise,
                               'graine': spec['graine']+prise*1000, 'prompt': spec['prompt'], 'format': spec['format'],
                               'unites': unites(spec['images']) if video else 0, 'etat': 'neuf',
                               'revision': self.d.get('revision') is True,
                               'prefix': prefix_team+groupe+'/'+ident,
                               'fichier': str(root / 'prises' / (ident+('.mp4' if video else '.png')))}
                sauver()
            return ident, jobs[ident]
        def restants():
            return [s for s in specs if choix.get(s['id'], {}).get('signature') != signatures[s['id']]
                    or not (root / (s['id']+('.mp4' if video else '.png'))).exists()]
        def utilise(fmt):
            return sum(j['unites'] for j in jobs.values() if j['etat'] != 'neuf' and j['format'] == fmt and not j.get('revision'))
        def utilise_revision():
            return sum(j['unites'] for j in jobs.values() if j['etat'] != 'neuf' and j.get('revision'))
        def autorise(spec, reprise):
            if not video:
                # 24 créations de clés distinctes, une relance chacune ; les modifications consomment aussi.
                return sum(j['etat'] != 'neuf' and j['prise'] == 0 for j in jobs.values()) < 24 if not reprise else True
            n = unites(spec['images'])
            if self.d.get('revision') is True:
                reserves = sum(unites(s['images']) for s in restants() if s['id'] != spec['id'] and (nom(s, 0) not in jobs or jobs[nom(s, 0)]['etat'] == 'neuf'))
                return utilise_revision()+n+reserves <= 6
            fmt = spec['format']
            # Ne pas dépenser en relance les unités réservées aux plans de base.
            reserve = sum(unites(s['images']) for s in restants() if s['id'] != spec['id'] and s['format'] == fmt
                          and (nom(s, 0) not in jobs or jobs[nom(s, 0)]['etat'] == 'neuf'))
            return utilise(fmt)+n+reserve <= (20 if fmt == '16:9' else 4)
        def graphe(spec, job):
            vertical = spec['format'] == '9:16'
            if video:
                cfg = {**spec, 'nom': spec['id'], 'graine': job['graine'], 'ref': True,
                       'checkpoint': recette().PRISM, 'etapes': 8, 'decalage': [12, 3], 'echantillonneur': 'euler',
                       'largeur': 768 if vertical else 1344, 'hauteur': 1344 if vertical else 768}
                if '<Picture 1>' not in cfg['prompt']:
                    cfg['prompt'] = ('For the target video, at 0.00 seconds into the target video, <Picture 1> '
                                     '(from [Shot 1]) is fully referenced.\n\n') + cfg['prompt']
                ref = moteur().envoyer_image(client.url, str(self.travail / 'cles' / (spec['cle']+'.png')))
                g = moteur().graphe_h3(cfg, ref)
            else:
                cfg = {**spec, 'nom': spec['id'], 'graine': job['graine'], 'negatif': recette().NEG,
                       'largeur': 928 if vertical else 1664, 'hauteur': 1664 if vertical else 928}
                g = moteur().graphe_image(cfg)
            g['save']['inputs']['filename_prefix'] = job['prefix']
            return g
        while restants():
            progres = False
            for spec in restants():
                ident, job = creer(spec, 0)
                # Télécharger et juger chaque prise ; les soumissions de tous les plans
                # sont faites dans ce même tour, sans attendre le premier rendu.
                candidats = []
                for prise in (0, 1):
                    ident = nom(spec, prise)
                    job = jobs.get(ident)
                    if job is None:
                        break
                    if job['etat'] == 'intention':
                        pid = client.retrouver(job['prefix']) if client else 'doublure'
                        if not pid:
                            raise RuntimeError(f'Soumission ambiguë {ident} : absente de queue/history ; aucune resoumission automatique')
                        job.update(pid=pid, etat='soumis')
                        sauver()
                    if job['etat'] == 'soumis':
                        result = client.resultat(job['pid'], Path(job['fichier'])) if client else {'secondesMoteur': 0.}
                        if result:
                            job.update(result, etat='rendu')
                            sauver()
                            progres = True
                    if job['etat'] == 'rendu':
                        note = self.noter(Path(job['fichier']))
                        job.update(juge=note, note=note['reel'], defauts=note.get('defauts', []), etat='juge')
                        sauver()
                        if not any(r.get('tentative') == ident for r in lignes(log)):
                            journal(log, {**job, 'tentative': ident, 'doublure': self.blanc})
                        progres = True
                    if job['etat'] == 'juge':
                        if not any(r.get('tentative') == ident for r in lignes(log)):
                            journal(log, {**job, 'tentative': ident, 'doublure': self.blanc})
                        candidats.append(job)
                if candidats and candidats[0]['prise'] == 0:
                    premier = candidats[0]
                    retry_id = nom(spec, 1)
                    if premier['note'] < 6.5 and retry_id not in jobs and autorise(spec, True):
                        creer(spec, 1)
                        progres = True
                    elif premier['note'] >= 6.5 or (retry_id not in jobs) or len(candidats) == 2:
                        meilleur = max(candidats, key=lambda x: x['note'])
                        dst = root / (spec['id']+('.mp4' if video else '.png'))
                        tmp = dst.with_suffix(dst.suffix+'.part')
                        shutil.copyfile(meilleur['fichier'], tmp)
                        tmp.replace(dst)
                        choix[spec['id']] = {'signature': signatures[spec['id']], 'fichier': str(dst),
                                            'note': meilleur['note'], 'graine': meilleur['graine'],
                                            'relance_refusee_budget': premier['note'] < 6.5 and retry_id not in jobs}
                        sauver()
                        progres = True
                        continue
                for prise in (0, 1):
                    ident = nom(spec, prise)
                    job = jobs.get(ident)
                    if not job or job['etat'] != 'neuf':
                        continue
                    if not autorise(spec, prise > 0):
                        raise ValueError(f'Budget {groupe} épuisé pour {spec["id"]}')
                    # Le compte vient de /queue, inclut courant + attente, et exclut les autres équipes.
                    if client and client.compte(prefix_team) >= (6 if video else 1):
                        continue
                    if self.blanc:
                        self.factice(Path(job['fichier']), secondes=spec.get('images', 144)/24,
                                     portrait=spec['format'] == '9:16', image=not video)
                        job.update(etat='rendu', secondesMoteur=0.)
                    else:
                        g = graphe(spec, job)
                        job.update(etat='intention', debut=time.time())
                        sauver()
                        job.update(pid=client.soumettre(g), etat='soumis')
                    sauver()
                    progres = True
            if restants() and not progres:
                time.sleep(self.poll)
        return choix

    def voix(self):
        b = banc()
        root = self.travail / 'voix'
        root.mkdir(parents=True, exist_ok=True)
        for spec in self.d['voix']:
            if spec['moteur'] == 'h3-natif':
                journal(root / 'journal.jsonl', {**spec, 'natif': True})
                continue
            token = signature(spec)
            meta = root / (spec['id']+'.json')
            dst = root / (spec['id']+'.wav')
            if lire_json(meta, {}).get('signature') == token and dst.exists():
                continue
            prises = []
            for i in (0, 1):
                folder = root / 'prises' / (spec['id']+'-'+token+f'-{i+1}')
                folder.mkdir(parents=True, exist_ok=True)
                f = folder / 'prise.mp3'
                report = folder / 'mesure.json'
                if report.exists() and f.exists():
                    prises.append(lire_json(report))
                    continue
                if not f.exists():
                    if self.blanc:
                        self.factice(folder / 'source.wav', secondes=2, audio=True)
                        ff('-i', folder / 'source.wav', f)
                    else:
                        # Le banc fournit les identifiants, références de clone et options.
                        from unittest.mock import patch
                        with patch.object(b, 'D', folder), patch.object(b, 'FF', binaire('ffmpeg')), \
                             patch.object(b, 'post', self.post), patch.dict(b.TEXTES, {'replique': spec['texte']}), \
                             patch.dict(b.JEU, {'replique': spec['direction']}):
                            produit = b.generer(spec['moteur'], 'replique')
                            produit.replace(f)
                if self.blanc:
                    texte, oreille, com, genre = spec['texte'], {'langue_francaise': 8, 'energie': 8, 'caractere': 8,
                                                               'naturel': 8, 'cheap': 1, 'accent_quebecois': 8}, [], None
                else:
                    code = ('import json,sys; from faster_whisper import WhisperModel; '
                            'm=WhisperModel("small",device="cpu",compute_type="int8"); '
                            's,_=m.transcribe(sys.argv[1],language=sys.argv[2],beam_size=5); '
                            'print(json.dumps(" ".join(x.text.strip() for x in s)))')
                    texte = json.loads(commande([ENGINE / 'transcription-venv/bin/python', '-c', code, f, spec.get('langue', 'fr')]))
                    from unittest.mock import patch
                    with patch.object(b, 'post', self.post), patch.dict(b.TEXTES, {'replique': spec['texte']}):
                        oreille, com, genre = b.juger(f, 'replique')
                    if not oreille:
                        raise RuntimeError(f'Oreille de machine indisponible pour {spec["id"]}')
                taux = wer(spec['texte'], texte)
                score = sum(oreille.get(k, 0)*w for k, w in [('langue_francaise', .25), ('energie', .2),
                            ('caractere', .2), ('naturel', .25), ('cheap', -.2), ('accent_quebecois', .1)]) - 5*taux
                res = {'id': spec['id'], 'prise': i+1, 'fichier': str(f), 'transcription': texte, 'wer': taux,
                       'oreille': oreille, 'commentaires': com, 'genre': genre, 'score': score, 'doublure': self.blanc}
                ecrire_json(report, res)
                journal(root / 'journal.jsonl', res)
                prises.append(res)
            best = max(prises, key=lambda x: x['score'])
            ff('-i', best['fichier'], '-ar', '48000', '-ac', '2', dst)
            ecrire_json(meta, {'signature': token, 'choix': best, 'prises': prises})

    def musique(self):
        root = self.travail / 'musique'
        root.mkdir(parents=True, exist_ok=True)
        legacy = musique_legacy()
        for spec in self.d['musiques']:
            dst = root / (spec['id']+'.wav')
            grille_path = root / (spec['id']+'.grille.json')
            if dst.exists() and lire_json(grille_path, {}).get('signature') == signature(spec):
                continue
            cout, secs = None, None
            if self.blanc:
                self.factice(dst, secondes=max(30, duree(self.d)+4), audio=True)
                g = {'bpm': 120., 'temps_s': .5, 'phase_s': 0., 'duree_s': max(30, duree(self.d)+4),
                     'energie_db_05s': [-24., -24., -12., -18.] * math.ceil(max(30, duree(self.d)+4)/2), 'doublure': True}
            else:
                if spec['moteur'].startswith('lyria'):
                    # Même implémentation SSE que V6 ; clé issue du fichier demandé.
                    from unittest.mock import patch
                    modele = 'google/lyria-3-pro-preview' if spec['moteur'] == 'lyria-pro' else 'google/lyria-3-clip-preview'
                    src = root / 'prises' / (spec['id']+'-'+signature(spec)+'.mp3')
                    etat_src = src.with_suffix('.json')
                    ancien = lire_json(etat_src, {})
                    if not src.exists():
                        if ancien:
                            raise RuntimeError(f'Lyria {spec["id"]} : soumission ambiguë ; vérifier OpenRouter avant de reprendre')
                        ecrire_json(etat_src, {'signature': signature(spec), 'etat': 'intention', 'modele': modele})
                        with patch.object(legacy.C, 'cle', lambda nom: self.cle()):
                            data, cout = legacy.lyria(spec['prompt'], modele)
                        temp = src.with_suffix('.part')
                        temp.write_bytes(data)
                        temp.replace(src)
                        ecrire_json(etat_src, {'signature': signature(spec), 'etat': 'recu', 'cout': cout, 'modele': modele})
                        journal(self.couts, {'modele': modele, 'operation': 'musique', 'cost': cout})
                    else:
                        cout = ancien.get('cout')
                else:
                    src, secs = self.music3(spec)
                ff('-i', src, '-ar', '48000', '-ac', '2', dst)
                from unittest.mock import patch
                with patch.object(legacy.C, 'FF', binaire('ffmpeg')):
                    g = legacy.grille(dst)
            g.update(signature=signature(spec), fichier=str(dst), cout=cout, secondesMoteur=secs)
            ecrire_json(grille_path, g)
            journal(root / 'journal.jsonl', {**spec, **g})

    def music3(self, spec):
        # Tester l'API avant toute soumission ; une erreur après POST n'entraîne
        # jamais un deuxième rendu sur ComfyUI.
        api = 'http://127.0.0.1:37171'
        try:
            with urllib.request.urlopen(api + '/api/health', timeout=5):
                pass
            online = True
        except urllib.error.HTTPError as e:
            online = e.code != 503  # 404 = serveur en ligne, route health non exposée.
        except (OSError, TimeoutError):
            online = False
        src = self.travail / 'musique' / (spec['id']+'.flac')
        etat_file = src.with_suffix('.music3.json')
        old = lire_json(etat_file, {})
        if old and old.get('signature') != signature(spec):
            raise RuntimeError(f'Music3 {spec["id"]} modifié : utiliser un nouvel identifiant pour conserver la reprise')
        if old.get('done') and src.exists():
            return src, old.get('secondesMoteur')
        if old:
            online = old['backend'] == 'studio'
        if online:
            m = module('v7_studio_moteurs', V7.parents[1] / 'nexora/refonte-medias/outils/moteurs.py')
            m.BASE = api
            if not old:
                ecrire_json(etat_file, {'signature': signature(spec), 'backend': 'studio', 'intention': True})
                corps = {'kind': 'musique', 'videoModel': 'music3', 'description': spec['prompt'], 'prompt': spec['prompt'],
                         'paroles': spec.get('paroles', '[Instrumental]'), 'dureeS': spec.get('duree', max(40, duree(self.d))),
                         'seed': spec.get('graine', 42), 'app': 'nexora-musique', 'shotName': f'v7-{self.equipe}-{spec["id"]}'}
                r = m._appel('/api/generate', corps)
                old = {'signature': signature(spec), 'backend': 'studio', 'tid': r.get('takeId') or r['takeIds'][0]}
                ecrire_json(etat_file, old)
            if not old.get('tid'):
                raise RuntimeError('Music3 : soumission studio ambiguë ; vérifier la prise avant de reprendre')
            c = m._attendre(old['tid'], 3600)
            m._copier(c, src)
            # Pas de faux « temps GPU » à partir du temps d'attente du studio.
            secs = c.get('secondesMoteur')
        else:
            client = Comfy(moteur().IMG_COMFY)
            prefix = f'v7-{self.equipe}/musique/{spec["id"]}-{signature(spec)}'
            if not old:
                g = graphe_music3(spec, max(40, duree(self.d)), prefix)
                old = {'signature': signature(spec), 'backend': 'comfy', 'prefix': prefix}
                ecrire_json(etat_file, old)
                old['pid'] = client.soumettre(g)
                ecrire_json(etat_file, old)
            if not old.get('pid'):
                old['pid'] = client.retrouver(prefix)
                if not old['pid']:
                    raise RuntimeError('Music3 : soumission ComfyUI ambiguë')
                ecrire_json(etat_file, old)
            while True:
                res = client.resultat(old['pid'], src)
                if res:
                    break
                time.sleep(self.poll)
            secs = res['secondesMoteur']
        old.update(done=True, secondesMoteur=secs)
        ecrire_json(etat_file, old)
        return src, secs

    def preparer_factices(self):
        # Sources réelles des captures conservées ; seuls les assets générés sont doublés.
        for k in self.d['cles']:
            f = self.travail / 'cles' / (k['id']+'.png')
            if not f.exists():
                self.factice(f, image=True, portrait=k['format']=='9:16')
        for p in self.d['plans']:
            f = self.travail / 'plans' / (p['id']+'.mp4')
            if not f.exists():
                self.factice(f, secondes=p['images']/24, portrait=p['format']=='9:16')
        self.voix()
        self.musique()

    def monter(self, musique=None, langues=('fr',), formats=('16x9', '9x16'), brouillon=False, jobs=1):
        if self.blanc:
            self.preparer_factices()
        m = substituer(self.d, self.base, self.travail, musique)
        mid = musique or self.d['montage'].get('musique', {}).get('fichier', 'sans-musique').removeprefix('musique:')
        path = self.travail / 'montages' / (mid+'.json')
        ecrire_json(path, m)
        outputs = []
        for lang in langues:
            for fmt in formats:
                output = self.travail / 'films' / f'{self.equipe}-{mid}-{fmt}-{lang}{"-brouillon" if brouillon else ""}.mp4'
                args = [sys.executable, '-B', V7 / 'monter_v6.py', path, '--format', fmt, '--langue', lang,
                        '--master', 'web', '--sortie', output, '--jobs', jobs]
                if brouillon:
                    args.append('--brouillon')
                env = {**os.environ, 'V6_CACHE': str(self.travail / 'cache-montage'),
                       'V6_FFMPEG': binaire('ffmpeg'), 'V6_FFPROBE': binaire('ffprobe'), 'PYTHONDONTWRITEBYTECODE': '1'}
                commande(args, env=env)
                outputs.append(output)
        return outputs

    def juger_musique(self):
        resultats = {}
        for spec in self.d['musiques']:
            # Le brouillon est mixé par le moteur, avec son natif, voix, trous et ducking.
            film = self.monter(spec['id'], brouillon=True, formats=('16x9',))[0]
            m = lire_json(self.travail / 'montages' / (spec['id']+'.json'))
            g = lire_json(self.travail / 'musique' / (spec['id']+'.grille.json'))
            if self.blanc:
                avis = {k: 8. for k in ('adequation', 'energie', 'synchronisation', 'memorabilite')}
                avis.update(plat=2., commentaire='Doublure, aucune évaluation distante', doublure=True)
                modalite = 'doublure'
            else:
                prompt = ('Juge cette musique MIXÉE SUR CE FILM publicitaire. Réponds en JSON : adequation, energie, '
                          'synchronisation, memorabilite, plat (chaque note 0-10 ; plat=10 signifie très plat), commentaire. '
                          'Observe les coupes, silences, impacts et le son natif. Ne juge pas une piste isolée.')
                video = 'data:video/mp4;base64,'+base64.b64encode(film.read_bytes()).decode()
                try:
                    avis = self.demander([{'type': 'video_url', 'video_url': {'url': video}}, {'type': 'text', 'text': prompt}])
                    modalite = 'video'
                except RuntimeError as e:
                    if not any(s in str(e) for s in ('HTTP 400', 'HTTP 413', 'HTTP 415', 'HTTP 422')):
                        raise
                    frames = [image_url(film, i*duree(self.d)/16) for i in range(16)]
                    audio = self.travail / 'musique' / (spec['id']+'-mix.mp3')
                    ff('-i', film, '-vn', '-c:a', 'libmp3lame', '-b:a', '128k', audio)
                    contenu = [{'type': 'text', 'text': prompt+' Images chronologiques à intervalles réguliers.'}]
                    contenu += [{'type': 'image_url', 'image_url': {'url': im}} for im in frames]
                    contenu += [{'type': 'input_audio', 'input_audio': {'data': base64.b64encode(audio.read_bytes()).decode(), 'format': 'mp3'}}]
                    avis = self.demander(contenu)
                    modalite = '16-images-et-audio'
                for k in ('adequation', 'energie', 'synchronisation', 'memorabilite', 'plat'):
                    if not isinstance(avis.get(k), (int, float)) or not 0 <= avis[k] <= 10:
                        raise ValueError(f'Juge musique : note {k} invalide')
            piste = self.travail / 'musique' / (spec['id']+'.wav')
            onsets = onsets_forts(piste)
            mesures = mesures_synchro(m, g, onsets, duree(self.d))
            mesures['plage_sonie_lu'] = sonie(piste)
            resultats[spec['id']] = {'film': str(film), 'modalite': modalite, 'juge': avis, 'mesures': mesures,
                                     'grille': g, 'doublure': self.blanc}
            ecrire_json(self.travail / 'musique/jugement.json', resultats)
        return resultats

    def planche(self):
        from PIL import Image, ImageDraw
        out = self.travail / 'planches'
        out.mkdir(parents=True, exist_ok=True)
        def assembler(cases, fichier):
            if not cases:
                return
            cols, w, h = 4, 320, 212
            im = Image.new('RGB', (cols*w, math.ceil(len(cases)/cols)*h), '#151515')
            draw = ImageDraw.Draw(im)
            for i, (picture, label) in enumerate(cases):
                x, y = i%cols*w, i//cols*h
                picture.thumbnail((w, h-32))
                im.paste(picture, (x, y))
                draw.text((x+5, y+h-28), label, fill='white')
            im.save(fichier, quality=88)
        for film in sorted((self.travail / 'films').glob('*.mp4')):
            seconds = float(sonder(film)['format']['duration'])
            assembler([(image_frame(film, t), f'{t:05.1f} s') for t in range(math.ceil(seconds))], out / (film.stem+'.jpg'))
        choix = lire_json(self.travail / 'plans/etat.json', {}).get('choix', {})
        cases = []
        for p in self.d['plans']:
            f = self.travail / 'plans' / (p['id']+'.mp4')
            seconds = float(sonder(f)['format']['duration'])
            note = choix.get(p['id'], {}).get('note', 'doublure' if self.blanc else '?')
            for frac in (.15, .5, .85):
                cases.append((image_frame(f, seconds*frac), f'{p["id"]} - {seconds*frac:.2f} s - note {note}'))
        assembler(cases, out / 'plans.jpg')

    def telephone(self):
        outputs = []
        for f in sorted((self.travail / 'films').glob('*.mp4')):
            dst = self.travail / 'telephone' / f.name
            dst.parent.mkdir(parents=True, exist_ok=True)
            seconds = float(sonder(f)['format']['duration'])
            # Mo décimaux, marge pour conteneur/AAC. Sous 28 Mo même à 70 s.
            debit = min(3_800_000, int(27_300_000*8/seconds)-128_000)
            if debit < 50_000:
                raise ValueError(f'Film trop long pour 28 Mo : {f.name}')
            for essai in range(3):
                # Deux passes pour une taille contrôlée ; journaux sur le disque de données.
                passe = dst.with_suffix('.pass')
                common = ['-i', f, '-map', '0:v:0', '-c:v', 'libx264', '-preset', 'medium', '-b:v', str(debit),
                          '-pix_fmt', 'yuv420p', '-passlogfile', passe]
                ff(*common, '-pass', '1', '-an', '-f', 'null', os.devnull)
                ff(*common, '-map', '0:a:0?', '-pass', '2', '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', dst)
                for log in dst.parent.glob(passe.name+'*'):
                    log.unlink()
                if dst.stat().st_size <= 28_000_000:
                    break
                debit = int(debit*.92)
            else:
                raise RuntimeError(f'Téléphone : taille > 28 Mo : {dst.name}')
            outputs.append(dst)
        return outputs

    def archiver(self):
        files = sorted(self.travail.rglob('*.mp4'))
        if self.blanc:
            plan = [{'source': str(f), 'destination': f'creative-v7/{self.equipe}/{f.relative_to(self.travail)}', 'sha256': sha(f)} for f in files]
            ecrire_json(self.travail / 'archive-a-blanc.json', plan)
            return plan
        # SHA de déduplication *après* copie, inventaire sous flock distant pour les 4 équipes.
        rows = []
        for f in files:
            rel = f'creative-v7/{self.equipe}/{f.relative_to(self.travail)}'
            dest = 'Bureau/Nexora-Livrables/TOUS-LES-FILMS/'+rel
            commande(['ssh', 'pc1', 'mkdir -p '+shlex.quote(str(Path(dest).parent))])
            commande(['rsync', '-a', '--protect-args', f, 'pc1:'+dest])
            j = sonder(f)
            st = next((s for s in j['streams'] if s.get('width')), {})
            role = 'master' if 'films' in f.relative_to(self.travail).parts else 'rush' if 'plans' in f.relative_to(self.travail).parts else 'travail'
            rows.append([rel, f.stat().st_size, round(float(j['format']['duration']), 2),
                         f'{st.get("width", "")}x{st.get("height", "")}', time.strftime('%Y-%m-%d %H:%M', time.localtime(f.stat().st_mtime)),
                         sha(f), f'Film V7 {self.d["titre"]}', 'V7', 'H3 / monter_v6.py', role, '', '', f'pc6:{f}', 1, ''])
        code = '''import csv,fcntl,json,sys
from pathlib import Path
p=Path.home()/"Bureau/Nexora-Livrables/TOUS-LES-FILMS/INVENTAIRE.csv"
p.parent.mkdir(parents=True,exist_ok=True)
with p.open("a+",newline="") as f:
 fcntl.flock(f,fcntl.LOCK_EX)
 f.seek(0)
 connus={r[5] for r in csv.reader(f) if len(r)>5}
 f.seek(0,2)
 w=csv.writer(f)
 n=0
 for row in json.load(sys.stdin):
  if row[5] not in connus:
   w.writerow(row); connus.add(row[5]); n+=1
 f.flush()
 print(n)
'''
        n = commande(['ssh', 'pc1', 'python3 -c '+shlex.quote(code)], input=json.dumps(rows).encode())
        return {'nouvelles_lignes': int(n), 'copies': len(files)}

    def bilan(self):
        jobs = []
        notes = {}
        for group in ('cles', 'plans'):
            state = lire_json(self.travail / group / 'etat.json', {})
            jobs += list(state.get('jobs', {}).values())
            notes[group] = state.get('choix', {})
        music = lignes(self.travail / 'musique/journal.jsonl')
        costs = lignes(self.couts)
        # Les réponse_id évitent de compter une réponse journalisée deux fois.
        connus, uniques = set(), []
        for c in costs:
            rid = c.get('reponse_id')
            if rid and rid in connus:
                continue
            if rid:
                connus.add(rid)
            uniques.append(c)
        rendu = [j for j in jobs if j['etat'] != 'neuf']
        result = {'equipe': self.equipe, 'doublure': self.blanc,
                  'secondes_gpu_connues': sum(j.get('secondesMoteur') or 0 for j in jobs+music),
                  'temps_moteur_inconnus': sum(j.get('secondesMoteur') is None for j in rendu+music),
                  'unites_h3': {fmt: sum(j.get('unites', 0) for j in rendu if j.get('format') == fmt) for fmt in ('16:9', '9:16')},
                  'unites_revision': sum(j.get('unites', 0) for j in rendu if j.get('revision')),
                  'images_cles_tentatives': sum(j.get('unites', 0) == 0 for j in rendu),
                  'budget_dossier': budget(self.d), 'notes': notes,
                  'cout_openrouter_usd_connu': sum(c['cost'] for c in uniques if isinstance(c.get('cost'), (int, float))),
                  'reponses_sans_cout': sum(c.get('cost') is None for c in uniques)}
        ecrire_json(self.travail / 'bilan.json', result)
        return result


def wer(reference, texte):
    import re
    a, b = [re.findall(r'\w+', s.lower()) for s in (reference, texte)]
    row = list(range(len(b)+1))
    for i, x in enumerate(a, 1):
        nxt = [i]
        for j, y in enumerate(b, 1):
            nxt.append(min(nxt[-1]+1, row[j]+1, row[j-1]+(x != y)))
        row = nxt
    return row[-1]/max(1, len(a))


def graphe_music3(s, secondes, prefix):
    # Transcription fidèle de app/server/graphs/music3.ts.
    seed = s.get('graine', 42)
    return {
        'u': {'class_type': 'UNETLoader', 'inputs': {'unet_name': 'minimax_music3_dit_int8_convrot.safetensors', 'weight_dtype': 'default'}},
        'c': {'class_type': 'CLIPLoader', 'inputs': {'clip_name': 'minimax_music3_text_encoder_pruned_int8_convrot.safetensors', 'type': 'minimax', 'device': 'default'}},
        'v': {'class_type': 'VAELoader', 'inputs': {'vae_name': 'minimax_music3_dav.safetensors'}},
        'enc': {'class_type': 'MiniMaxMusic3TextEncode', 'inputs': {'clip': ['c', 0], 'caption': s['prompt'],
                'lyrics': s.get('paroles', '[Instrumental]'), 'seed': seed, 'max_duration': max(5, min(300, s.get('duree', secondes))), 'cfg_scale': 1.7, 'top_k': 50}},
        'neg': {'class_type': 'ConditioningZeroOut', 'inputs': {'conditioning': ['enc', 0]}},
        'lat': {'class_type': 'EmptyMiniMaxMusic3LatentAudio', 'inputs': {'seconds': ['enc', 1], 'batch_size': 1}},
        'ks': {'class_type': 'KSampler', 'inputs': {'model': ['u', 0], 'seed': seed, 'steps': 30, 'cfg': 1.7, 'sampler_name': 'euler',
                'scheduler': 'simple', 'positive': ['enc', 0], 'negative': ['neg', 0], 'latent_image': ['lat', 0], 'denoise': 1.}},
        'dec': {'class_type': 'VAEDecodeAudio', 'inputs': {'samples': ['ks', 0], 'vae': ['v', 0]}},
        'save': {'class_type': 'SaveAudio', 'inputs': {'audio': ['dec', 0], 'filename_prefix': prefix}}}



def image_juge(media, largeur=1024):
    """Triptyque du juge, avec ffprobe résolu indépendamment de ffmpeg.

    Le juge historique remplace toutes les occurrences de ffmpeg dans le chemin,
    ce qui casse aussi le nom du dossier parent engine/ffmpeg/.
    """
    from PIL import Image
    f = Path(media)
    if f.suffix.lower() in ('.mp4', '.mov', '.webm'):
        sec = float(sonder(f)['format']['duration'])
        images = [image_frame(f, sec*t) for t in (.15, .5, .85)]
        w = largeur//3
        h = round(images[0].height*w/images[0].width)
        im = Image.new('RGB', (3*w, h))
        for i, frame in enumerate(images):
            im.paste(frame.resize((w, h)), (i*w, 0))
    else:
        im = Image.open(f).convert('RGB')
        im.thumbnail((largeur, largeur))
    out = io.BytesIO()
    im.save(out, 'JPEG', quality=88)
    return 'data:image/jpeg;base64,'+base64.b64encode(out.getvalue()).decode()

def image_frame(film, t):
    from PIL import Image
    raw = ff('-ss', f'{t:.4f}', '-i', film, '-frames:v', '1', '-f', 'image2pipe', '-vcodec', 'png', '-')
    return Image.open(io.BytesIO(raw)).convert('RGB')


def image_url(film, t):
    im = image_frame(film, t)
    im.thumbnail((1024, 1024))
    b = io.BytesIO()
    im.save(b, 'JPEG', quality=85)
    return 'data:image/jpeg;base64,'+base64.b64encode(b.getvalue()).decode()


def sonie(f):
    p = subprocess.run([binaire('ffmpeg'), '-hide_banner', '-i', str(f), '-vn', '-af',
                        'loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json', '-f', 'null', '-'], capture_output=True, text=True, check=True)
    raw = p.stderr[p.stderr.rfind('{'):p.stderr.rfind('}')+1]
    return float(json.loads(raw)['input_lra'])


def onsets_forts(f):
    """Flux spectral à 100 Hz, maxima espacés de 120 ms, quartile fort."""
    import numpy as np
    raw = ff('-i', f, '-f', 'f32le', '-ac', '1', '-ar', '22050', '-')
    x = np.frombuffer(raw, np.float32)
    frames = np.lib.stride_tricks.sliding_window_view(x, 1024)[::220]
    spectrum = np.abs(np.fft.rfft(frames*np.hanning(1024), axis=1))
    flux = np.maximum(0, np.diff(np.log1p(10*spectrum), axis=0)).sum(1)
    if not len(flux) or flux.max() == 0:
        return []
    threshold = max(float(np.quantile(flux, .75)), float(flux.max())*.15)
    peaks = [i for i in range(1, len(flux)-1) if flux[i] > threshold and flux[i] >= flux[i-1] and flux[i] > flux[i+1]]
    selected = []
    for i in sorted(peaks, key=lambda i: -flux[i]):
        if all(abs(i-j) >= 12 for j in selected):
            selected.append(i)
    return sorted((i+1)*220/22050 for i in selected)


def mesures_synchro(m, g, onsets, duration):
    import numpy as np
    cuts = sorted(set(s['debut'] for s in m['segments'] if 0 < s['debut'] < duration))
    mu = m.get('musique', {})
    anchors = sorted([(0., mu.get('entree', 0.))]+[tuple(x) for x in mu.get('coupes', [])])
    holes = mu.get('trous', [])
    def audible(t):
        return not any(a <= t <= b for a, b in holes)
    def source(t):
        a, b = max((p for p in anchors if p[0] <= t), key=lambda p: p[0])
        return b+t-a
    def distance_temps(t):
        src = source(t)
        phase, dt = g['phase_s'], g['temps_s']
        return abs((src-phase+dt/2) % dt-dt/2)
    impacts = []
    for i, (tf, ts) in enumerate(anchors):
        end = anchors[i+1][0] if i+1 < len(anchors) else duration
        impacts += [tf+o-ts for o in onsets if tf <= tf+o-ts < end and audible(tf+o-ts)]
    audible_cuts = [t for t in cuts if audible(t)]
    return {'tempo_bpm': g['bpm'], 'coupes': len(cuts), 'coupes_audibles': len(audible_cuts),
            'part_coupes_a_2_images_temps': sum(distance_temps(t) <= 2/24+1e-9 for t in audible_cuts)/len(audible_cuts) if audible_cuts else None,
            'ecart_moyen_impacts_coupes_s': float(np.mean([min(abs(t-c) for c in cuts) for t in impacts])) if impacts and cuts else None,
            'onsets_forts_film_s': impacts, 'definition': 'Coupes internes, temps mesurés ; impacts = maxima de flux spectral forts ; trous exclus'}
