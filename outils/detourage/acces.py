"""
Contrôle d'accès du serveur de détourage (stdlib seule, testable sans GPU).

Deux verrous, vérifiés avant de lire le corps d'une requête :
  1. l'adresse du client est dans la liste autorisée (adresses ou réseaux, IPv4/IPv6) ;
  2. l'en-tête « Authorization: Bearer <jeton> » correspond au jeton partagé (comparaison en temps constant).

Le jeton vit dans un fichier lisible par son seul propriétaire (mode 600 ou plus strict) ; il n'est jamais journalisé.
Un serveur qui écoute ailleurs qu'en boucle locale refuse de démarrer sans jeton ni liste d'adresses.
"""
from __future__ import annotations

import hmac
import ipaddress
import os
import stat

LONGUEUR_MIN = 32


class ConfigAcces(Exception):
    pass


def est_local(hote: str) -> bool:
    try:
        return ipaddress.ip_address(hote).is_loopback
    except ValueError:
        return hote == 'localhost'


def lire_jeton(chemin: str) -> str:
    """Lit le jeton ; refuse un fichier accessible aux autres, modifiable par le groupe, ou un jeton trop court.

    La lecture par le groupe n'est admise que si ce groupe est celui du processus : c'est le cas d'un Secret Kubernetes
    monté avec fsGroup (le kubelet ajoute g+r), où seul notre conteneur appartient à ce groupe.
    """
    st = os.stat(chemin)
    mode = stat.S_IMODE(st.st_mode)
    groupe_a_nous = st.st_gid == os.getgid() or st.st_gid in os.getgroups()
    if mode & stat.S_IRWXO or mode & (stat.S_IWGRP | stat.S_IXGRP) or (mode & stat.S_IRGRP and not groupe_a_nous):
        raise ConfigAcces(f'le fichier du jeton doit être en mode 600 (actuel {mode:o})')
    with open(chemin, encoding='utf-8') as fh:
        jeton = fh.read().strip()
    if len(jeton) < LONGUEUR_MIN:
        raise ConfigAcces(f'jeton trop court (au moins {LONGUEUR_MIN} caractères)')
    return jeton


def lire_reseaux(texte: str | None) -> list:
    reseaux = []
    for x in (texte or '').split(','):
        x = x.strip()
        if x:
            reseaux.append(ipaddress.ip_network(x, strict=False))
    return reseaux


class Acces:
    def __init__(self, jeton: str | None, reseaux: list):
        self._jeton = jeton.encode() if jeton else None
        self.reseaux = reseaux

    @classmethod
    def depuis_env(cls, hotes: list[str], env=os.environ) -> 'Acces':
        fichier = (env.get('NEXORA_DETOURAGE_JETON_FICHIER') or '').strip()
        jeton = lire_jeton(fichier) if fichier else None
        reseaux = lire_reseaux(env.get('NEXORA_DETOURAGE_AUTORISES'))
        if any(not est_local(h) for h in hotes):
            if not jeton:
                raise ConfigAcces('écoute réseau sans jeton : définis NEXORA_DETOURAGE_JETON_FICHIER')
            if not reseaux:
                raise ConfigAcces('écoute réseau sans liste d’adresses : définis NEXORA_DETOURAGE_AUTORISES')
        return cls(jeton, reseaux)

    def adresse_autorisee(self, ip: str) -> bool:
        if not self.reseaux:
            return True  # boucle locale seulement (vérifié au démarrage)
        try:
            a = ipaddress.ip_address(ip.split('%')[0])
        except ValueError:
            return False
        if a.version == 6 and a.ipv4_mapped:
            a = a.ipv4_mapped
        return any(a in r for r in self.reseaux)

    def jeton_valide(self, entete: str | None) -> bool:
        if self._jeton is None:
            return True
        if not entete or not entete.startswith('Bearer '):
            return False
        return hmac.compare_digest(entete[7:].strip().encode(), self._jeton)

    def verifier(self, ip: str, entete: str | None) -> int:
        """0 si la requête passe, sinon le code HTTP à renvoyer (403 adresse, 401 jeton)."""
        if not self.adresse_autorisee(ip):
            return 403
        if not self.jeton_valide(entete):
            return 401
        return 0

    def resume(self) -> str:
        return f"jeton {'exigé' if self._jeton else 'absent'}, adresses {','.join(map(str, self.reseaux)) or 'toutes (boucle locale)'}"
