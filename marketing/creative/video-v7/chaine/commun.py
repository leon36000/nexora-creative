"""Contrats V7, validation et substitution ; aucune connexion à l'import."""
import contextlib
import copy
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import sys
import tempfile
from unittest.mock import patch

sys.dont_write_bytecode = True
ICI = Path(__file__).resolve().parent
V7 = ICI.parent
DEPOT = V7.parents[2]
DATA = Path.home() / 'nexora-creative-data/promo/v7-creative'
INTERDITS = ('cinematic', 'epic', 'glowing', 'incandescent', 'majestic', 'dramatic lighting',
             'hyper-detailed', '8k', 'render', 'cgi', 'unreal', 'concept art', 'teal and orange', 'vibrant', 'stunning')
IDENTIFIANT = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_-]*$')


def module(nom, fichier):
    if nom not in sys.modules:
        spec = importlib.util.spec_from_file_location(nom, fichier)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[nom] = mod
        anciens_chemins = sys.path[:]
        sys.path.insert(0, str(Path(fichier).parent))
        try:
            spec.loader.exec_module(mod)
        except BaseException:
            sys.modules.pop(nom, None)
            raise
        finally:
            sys.path[:] = anciens_chemins
    return sys.modules[nom]


def moteur():
    return module('v7_moteur', V7.parent / 'video-v3/moteur.py')


def montage_module():
    return module('v7_montage', V7 / 'monter_v6.py')


def banc():
    return module('v7_banc', V7 / 'voix/banc_voix_v7.py')


def recette():
    return module('v7_recette', V7 / 'recette/recette_live.py')


def juge():
    return module('v7_juge', V7 / 'recette/juge_reel.py')


def ecrire_json(f, objet):
    f = Path(f)
    f.parent.mkdir(parents=True, exist_ok=True)
    tmp = f.with_name(f.name + '.tmp')
    with tmp.open('w') as out:
        json.dump(objet, out, ensure_ascii=False, indent=2, allow_nan=False)
        out.flush()
        os.fsync(out.fileno())
    tmp.replace(f)


def lire_json(f, defaut=None):
    return json.loads(Path(f).read_text()) if Path(f).exists() else defaut


def journal(f, objet):
    f = Path(f)
    f.parent.mkdir(parents=True, exist_ok=True)
    with f.open('a') as out:
        out.write(json.dumps(objet, ensure_ascii=False, allow_nan=False) + '\n')
        out.flush()
        os.fsync(out.fileno())


def lignes(f):
    if not Path(f).exists():
        return []
    # Une dernière ligne interrompue n'est pas une tentative supplémentaire.
    rows = []
    raw = Path(f).read_text().splitlines()
    for i, line in enumerate(raw):
        try:
            rows.append(json.loads(line))
        except ValueError:
            if i != len(raw)-1:
                raise
    return rows


def absolu(valeur, base):
    p = Path(os.path.expandvars(valeur)).expanduser()
    return p.resolve() if p.is_absolute() else (base / p).resolve()


def chemin_source(valeur, base):
    """Les chemins du contrat montage sont relatifs au dossier.json.

    captures/ et marque-v7.json sont les ressources communes de video-v7.
    """
    p = absolu(valeur, base)
    if not p.exists() and (valeur.startswith('captures/') or valeur == 'marque-v7.json'):
        return absolu(valeur, V7)
    return p


def unites(images):
    if type(images) is not int or images < 124 or images > 243 or (images-5) % 17:
        raise ValueError('images : grille 17k+5 de 124 à 243 requise')
    return 1 if images == 124 else 2


def budget(d):
    return {fmt: sum(unites(p['images']) for p in d['plans'] if p['format'] == fmt)
            for fmt in ('16:9', '9:16')}


def duree(d):
    m = d['montage']
    return m.get('duree', max((s['debut'] + s['duree'] for s in m['segments']), default=0))


def premier_impact(d):
    return min((x['t'] for x in d['temps_forts']), default=0.)


def calage_auto(g, impact, film_duree=0):
    """Le plus fort saut positif d'énergie *atteignable* arrive au premier impact.

    Ne boucle pas la piste : l'entrée doit laisser toute la durée du film.
    """
    e = g['energie_db_05s']
    maximum = max(0., g['duree_s'] - film_duree)
    candidats = [(e[i]-e[i-1], i*.5-impact) for i in range(1, len(e))
                 if 0 <= i*.5-impact <= maximum]
    if not candidats:
        return 0.
    return round(max(candidats, key=lambda x: (x[0], -x[1]))[1], 6)


def parcourir(obj):
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from parcourir(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from parcourir(v)


def substituer(d, base, travail, musique=None, factices=None):
    m = copy.deepcopy(d['montage'])
    refs = {}
    for p in d['plans']:
        prefix = 'plan_v' if p['format'] == '9:16' else 'plan'
        refs[f'{prefix}:{p["id"]}'] = str(travail / 'plans' / f'{p["id"]}.mp4')
    refs.update({f'musique:{x["id"]}': str(travail / 'musique' / f'{x["id"]}.wav') for x in d['musiques']})
    if factices:
        refs.update(factices)
    def rec(obj, key=''):
        if isinstance(obj, list):
            return [rec(v, key) for v in obj]
        if isinstance(obj, dict):
            return {k: rec(v, k) for k, v in obj.items()}
        if isinstance(obj, str):
            if obj.startswith(('plan:', 'plan_v:', 'musique:')):
                if obj not in refs:
                    raise ValueError(f'Référence inconnue : {obj}')
                return refs[obj]
            if key in montage_module().PATH_KEYS | montage_module().LOCAL_KEYS or key == 'marque':
                return str(chemin_source(obj, base))
            if key in ('media', 'couches', 'rushes'):
                return str(chemin_source(obj, base))
        return obj
    m = rec(m)
    m.setdefault('marque', str(V7 / 'marque-v7.json'))
    mu = m.get('musique')
    if musique:
        if musique not in {x['id'] for x in d['musiques']}:
            raise ValueError(f'Musique inconnue : {musique}')
        mu = m.setdefault('musique', {})
        mu['fichier'] = refs[f'musique:{musique}']
    if mu:
        original = d['montage'].get('musique', {}).get('fichier', '')
        mid = musique or original.removeprefix('musique:')
        g = lire_json(travail / 'musique' / f'{mid}.grille.json')
        if mu.pop('calage', None) == 'auto':
            if g:
                mu['entree'] = calage_auto(g, premier_impact(d), duree(d))
            elif factices is not None:
                mu['entree'] = 0.
            else:
                raise ValueError(f'Grille absente : {mid} ; lancer musique')
        if g:
            m['bpm'] = g['bpm']
            m['phase'] = (g['phase_s'] - mu.get('entree', 0)) % g['temps_s']
    voix = {v['id']: v for v in d['voix']}
    for parent in ([m['voix']] if isinstance(m.get('voix'), list) else (m.get('voix') or {}).values()):
        parent[:] = [v for v in parent if voix.get(v.get('id'), {}).get('moteur') != 'h3-natif']
        for v in parent:
            v.setdefault('fichier', str(travail / 'voix' / f'{v["id"]}.wav'))
            if factices and f'voix:{v["id"]}' in factices:
                v['fichier'] = factices[f'voix:{v["id"]}']
    # Les polices et le logo restent relatifs au JSON de marque, chargé par V6.
    return m


def valider(d, base):
    erreurs, avertissements = [], []
    if not isinstance(d, dict):
        return ['dossier : objet requis'], []
    for k in ('equipe', 'titre'):
        if not isinstance(d.get(k), str) or not d[k].strip():
            erreurs.append(f'{k} : chaîne non vide requise')
    if isinstance(d.get('equipe'), str) and not IDENTIFIANT.fullmatch(d['equipe']):
        erreurs.append('equipe : identifiant simple requis')
    champs = {'cles': ('id', 'format', 'graine', 'prompt'),
              'plans': ('id', 'cle', 'format', 'images', 'graine', 'prompt'),
              'voix': ('id', 'moteur', 'texte', 'direction'),
              'musiques': ('id', 'moteur', 'prompt'), 'temps_forts': ('t', 'evenement')}
    for group, keys in champs.items():
        rows = d.get(group)
        if not isinstance(rows, list):
            erreurs.append(f'{group} : liste requise')
            continue
        ids = set()
        for i, row in enumerate(rows):
            loc = f'{group}[{i}]'
            if not isinstance(row, dict):
                erreurs.append(f'{loc} : objet requis')
                continue
            for k in keys:
                v = row.get(k)
                if k in ('graine', 'images'):
                    ok = type(v) is int and v >= 0
                elif k == 't':
                    ok = type(v) in (int, float) and math.isfinite(v) and v >= 0
                else:
                    ok = isinstance(v, str) and bool(v.strip())
                if not ok:
                    erreurs.append(f'{loc}.{k} : valeur requise invalide')
            if 'id' in row:
                ident = row['id']
                if not isinstance(ident, str) or not IDENTIFIANT.fullmatch(ident):
                    erreurs.append(f'{loc}.id : identifiant simple requis')
                elif ident in ids:
                    erreurs.append(f'{loc}.id : doublon {ident}')
                else:
                    ids.add(ident)
            if group in ('cles', 'plans'):
                if row.get('format') not in ('16:9', '9:16'):
                    erreurs.append(f'{loc}.format : 16:9 ou 9:16 requis')
                prompt = row.get('prompt', '')
                if isinstance(prompt, str):
                    normal = re.sub(r'[-–—\s]+', ' ', prompt.lower())
                    for mot in INTERDITS:
                        motif = re.escape(mot.replace('-', ' ')).replace(r'\ ', r'\s+')
                        if re.search(r'\b' + motif + r'\b', normal):
                            erreurs.append(f'{loc}.prompt : mot interdit « {mot} »')
                    if group == 'plans' and not re.search(r'\bno\s+text\b', prompt, re.I):
                        erreurs.append(f'{loc}.prompt : « No text » requis')
                if group == 'plans':
                    try:
                        unites(row.get('images'))
                    except ValueError as e:
                        erreurs.append(f'{loc}.{e}')
            if group == 'voix' and row.get('moteur') not in {*banc().CANDIDATS, 'h3-natif'}:
                erreurs.append(f'{loc}.moteur : inconnu')
            if group == 'musiques' and row.get('moteur') not in ('lyria-pro', 'lyria-clip', 'music3'):
                erreurs.append(f'{loc}.moteur : inconnu')
    if not isinstance(d.get('montage'), dict) or not isinstance(d['montage'].get('segments'), list) or not d['montage']['segments']:
        erreurs.append('montage.segments : liste non vide requise')
    m = d.get('montage')
    if isinstance(m, dict):
        if m.get('musique') is not None and not isinstance(m['musique'], dict):
            erreurs.append('montage.musique : objet requis')
        voix = m.get('voix', [])
        groupes = voix.values() if isinstance(voix, dict) else [voix]
        if any(not isinstance(g, list) or any(not isinstance(x, dict) or not isinstance(x.get('id'), str) for x in g) for g in groupes):
            erreurs.append('montage.voix : liste de répliques {id, t} ou listes par langue requises')
    if erreurs:
        return erreurs, avertissements
    for nom, maximum in (('cles', 24), ('voix', 8), ('musiques', 4 if d.get('revision') is True else 3)):
        if len(d[nom]) > maximum:
            erreurs.append(f'Budget {nom} dépassé : {len(d[nom])}/{maximum}')
    if len(d['musiques']) < 3:
        avertissements.append('Moins de 3 pistes : dossier incomplet pour la livraison (essai permis)')
    b = budget(d)
    for fmt, maximum in (('16:9', 20), ('9:16', 4)):
        if b[fmt] > maximum:
            erreurs.append(f'Budget H3 {fmt} dépassé : {b[fmt]}/{maximum}')
    cles = {k['id']: k for k in d['cles']}
    for p in d['plans']:
        if p['cle'] not in cles:
            erreurs.append(f'{p["id"]} : clé inconnue {p["cle"]}')
        elif cles[p['cle']]['format'] != p['format']:
            erreurs.append(f'{p["id"]} : format différent de sa clé')
        if p['images']/24 > 6:
            avertissements.append(f'{p["id"]} : rush de plus de 6 s')
    refs = {f'{"plan_v" if p["format"] == "9:16" else "plan"}:{p["id"]}' for p in d['plans']}
    refs |= {f'musique:{m["id"]}' for m in d['musiques']}
    def refs_rec(obj):
        if isinstance(obj, str) and obj.startswith(('plan:', 'plan_v:', 'musique:')) and obj not in refs:
            erreurs.append(f'Référence inconnue : {obj}')
        elif isinstance(obj, list):
            for x in obj:
                refs_rec(x)
        elif isinstance(obj, dict):
            for x in obj.values():
                refs_rec(x)
    refs_rec(d['montage'])
    vs = {v['id'] for v in d['voix']}
    for v in parcourir(d['montage'].get('voix', [])):
        if 'id' in v and v['id'] not in vs:
            erreurs.append(f'Voix inconnue : {v["id"]}')
    try:
        sec = duree(d)
        if not 40 <= sec <= 70:
            avertissements.append(f'Durée hors 40–70 s : {sec:g} s')
        for s in d['montage']['segments']:
            if s['duree'] > 6 and s['type'] == 'plan':
                avertissements.append('Montage : plan de plus de 6 s')
        marque = lire_json(chemin_source(d['montage'].get('marque', 'marque-v7.json'), base))
        for obj in parcourir(d['montage']):
            tid = obj.get('texte_id')
            if tid:
                for lang, textes in marque['textes'].items():
                    if len(textes.get(tid, '').split()) > 4:
                        avertissements.append(f'Texte de carton/titre de plus de 4 mots ({lang}) : {tid}')
        if any(s['type'] == 'carton' for s in d['montage']['segments']):
            for lang, textes in marque['textes'].items():
                for tid in (marque.get('carton', {}).get('slogan_id'), marque.get('carton', {}).get('mentions_id')):
                    if len(textes.get(tid, '').split()) > 4:
                        avertissements.append(f'Texte de carton de plus de 4 mots ({lang}) : {tid}')
    except (KeyError, TypeError, ValueError, OSError, AttributeError) as e:
        erreurs.append(f'Montage : {e}')
    if not erreurs:
        try:
            validation_montage(d, base)
        except (ValueError, OSError, KeyError, TypeError, IndexError, AttributeError) as e:
            erreurs.append(f'monter_v6.charger : {e}')
    return erreurs, avertissements


def validation_montage(d, base):
    """Appelle le vrai validateur ; seuls les médias générés sont des doublures.

    Les fichiers existent et leurs durées sont celles des specs. Les captures,
    polices, marque, boost et autres ressources restent strictement contrôlés.
    """
    v6 = montage_module()
    with tempfile.TemporaryDirectory(prefix='validation-', dir=ICI) as tmp:
        root = Path(tmp)
        refs, durations = {}, {}
        for p in d['plans']:
            ref = f'{"plan_v" if p["format"] == "9:16" else "plan"}:{p["id"]}'
            f = root / (p['id']+'.mp4')
            f.touch()
            refs[ref] = str(f)
            durations[str(f)] = p['images']/24
        for group, prefix in (('musiques', 'musique'), ('voix', 'voix')):
            for x in d[group]:
                f = root / f'{prefix}-{x["id"]}.wav'
                f.touch()
                refs[f'{prefix}:{x["id"]}'] = str(f)
        m = substituer(d, base, root, factices=refs)
        f = root / 'montage.json'
        ecrire_json(f, m)
        original = v6.duree_media
        def duree_double(path):
            return durations[str(path)] if str(path) in durations else original(path)
        with patch.object(v6, 'duree_media', side_effect=duree_double):
            for lang in ('fr', 'en'):
                v6.charger(f, lang)


def musique_legacy():
    """Isole les noms génériques commun/musique utilisés par les outils V5/V6."""
    dossier = V7.parents[1] / 'nexora/campagne-films/films-v3/outils'
    c = module('v7_audio_commun', dossier / 'commun.py')
    precedent = sys.modules.get('commun')
    sys.modules['commun'] = c
    try:
        return module('v7_audio_musique', dossier / 'musique.py')
    finally:
        if precedent is None:
            sys.modules.pop('commun', None)
        else:
            sys.modules['commun'] = precedent
