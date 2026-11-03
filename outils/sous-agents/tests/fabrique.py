#!/usr/bin/env python3
"""Fabrique les 3 tâches d'essai de capacité. Usage : fabrique.py <racine>  -> <racine>/{prompts/t1.txt..., work/t1..t3}"""
import os, sys, textwrap
root = sys.argv[1]
def w(path, s):
    p = os.path.join(root, path); os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w").write(textwrap.dedent(s).lstrip("\n"))

# ---- Tâche 1 : renommage multi-fichiers + correction de tests (Python) ----
w("work/t1/boutique/prix.py", '''
    TVA = 0.15

    def calcul_prix_ttc(ht, taux=TVA):
        """Prix toutes taxes comprises, arrondi au cent."""
        return round(ht * (1 + taux), 1)
''')
w("work/t1/boutique/facture.py", '''
    from boutique.prix import calcul_prix_ttc

    def total_facture(lignes):
        return round(sum(calcul_prix_ttc(p) * q for p, q in lignes), 2)
''')
w("work/t1/boutique/__init__.py", "")
w("work/t1/tests/__init__.py", "")
w("work/t1/cli.py", '''
    from boutique.prix import calcul_prix_ttc
    import sys
    if __name__ == "__main__":
        print(calcul_prix_ttc(float(sys.argv[1])))
''')
w("work/t1/README.md", "Utiliser `calcul_prix_ttc(ht)` pour obtenir le prix TTC (TVA 14,975 % arrondie : voir prix.py).\n")
w("work/t1/tests/test_prix.py", '''
    import unittest
    from boutique.prix import calcul_prix_ttc
    from boutique.facture import total_facture
    class T(unittest.TestCase):
        def test_ttc(self): self.assertEqual(calcul_prix_ttc(100), 114.98)
        def test_ttc_petit(self): self.assertEqual(calcul_prix_ttc(9.99), 11.49)
        def test_facture(self): self.assertEqual(total_facture([(100, 2), (10, 1)]), 241.46)
    if __name__ == "__main__": unittest.main()
''')
w("prompts/t1.txt", '''
    Dépôt Python dans le dossier courant. Fais ceci :
    1) Renomme la fonction `calcul_prix_ttc` en `prix_ttc` partout (module, imports, cli.py, README.md, tests).
    2) Les tests (python3 -m unittest discover -s tests -t .) échouent : corrige le code de prix.py pour qu'ils passent. La TVA du Québec combinée est de 14,975 % ; le prix est arrondi au cent. Ne modifie pas les valeurs attendues des tests, seulement leur nom de fonction.
    3) Lance les tests pour le confirmer. Plus aucune occurrence de `calcul_prix_ttc` ne doit rester.
''')

# ---- Tâche 2 : fonctionnalité + tests (TypeScript, node:test) ----
w("work/t2/src/panier.ts", '''
    export type Ligne = { sku: string; prix: number; qte: number };

    export class Panier {
      private lignes: Ligne[] = [];
      ajouter(sku: string, prix: number, qte = 1): void {
        if (prix < 0 || qte <= 0) throw new Error("ligne invalide");
        const l = this.lignes.find((x) => x.sku === sku);
        if (l) l.qte += qte; else this.lignes.push({ sku, prix, qte });
      }
      sousTotal(): number {
        return Math.round(this.lignes.reduce((s, l) => s + l.prix * l.qte, 0) * 100) / 100;
      }
      total(): number { return this.sousTotal(); }
    }
''')
w("work/t2/test/panier.test.ts", '''
    import { test } from "node:test";
    import assert from "node:assert/strict";
    import { Panier } from "../src/panier.ts";
    test("sous-total", () => {
      const p = new Panier(); p.ajouter("a", 10, 2); p.ajouter("b", 5.5);
      assert.equal(p.sousTotal(), 25.5);
    });
''')
w("work/t2/package.json", '{"name":"panier","type":"module","scripts":{"test":"node --test"}}\n')
w("prompts/t2.txt", '''
    Petit projet TypeScript (exécuté par Node avec le retrait de types natif ; pas de dépendances, pas de npm install). Tests : `node --test` (sans argument).
    Ajoute à la classe Panier (src/panier.ts) la méthode `appliquerCoupon(code: string): void` et fais que `total()` en tienne compte :
    - "PROMO10" : -10 % sur le sous-total ; "FIXE5" : -5 $ fixes mais seulement si le sous-total est >= 20 (sinon lever une Error de message "minimum non atteint") ; tout autre code : lever Error("coupon invalide").
    - Un seul coupon à la fois : appliquer un second coupon lève Error("coupon déjà appliqué").
    - Le total ne descend jamais sous 0, est arrondi au cent, et se recalcule si on ajoute des articles après le coupon (FIXE5 est revérifié au calcul : si le sous-total repasse sous 20 le coupon ne s'applique plus mais reste enregistré).
    Écris les tests correspondants dans test/panier.test.ts (ajoute-les à côté de l'existant) et lance-les jusqu'à ce qu'ils passent.
''')
w("verif/t2.test.ts", '''
    import { test } from "node:test";
    import assert from "node:assert/strict";
    import { Panier } from "../work/t2/src/panier.ts";
    const mk = (prix: number) => { const p = new Panier(); p.ajouter("a", prix); return p; };
    test("PROMO10", () => { const p = mk(50); p.appliquerCoupon("PROMO10"); assert.equal(p.total(), 45); });
    test("FIXE5 ok", () => { const p = mk(20); p.appliquerCoupon("FIXE5"); assert.equal(p.total(), 15); });
    test("FIXE5 minimum", () => { assert.throws(() => mk(19.99).appliquerCoupon("FIXE5"), /minimum non atteint/); });
    test("invalide", () => { assert.throws(() => mk(10).appliquerCoupon("XX"), /coupon invalide/); });
    test("un seul", () => { const p = mk(50); p.appliquerCoupon("PROMO10"); assert.throws(() => p.appliquerCoupon("FIXE5"), /coupon déjà appliqué/); });
    test("recalcul", () => { const p = mk(20); p.appliquerCoupon("FIXE5"); p.ajouter("b", 10); assert.equal(p.total(), 25); });
    test("revérifié", () => { const p = mk(25); p.appliquerCoupon("FIXE5"); assert.equal(p.total(), 20); });
    test("arrondi", () => { const p = mk(33.33); p.appliquerCoupon("PROMO10"); assert.equal(p.total(), 30); });
    test("jamais négatif", () => { const p = mk(21); p.appliquerCoupon("FIXE5"); p.ajouter("c", 0, 1); assert.ok(p.total() >= 0); });
''')

# ---- Tâche 3 : lire un module, le résumer avec exactitude, corriger un bogue ----
w("work/t3/ttlcache.py", '''
    """Cache en mémoire avec expiration (TTL) et éviction du moins récemment utilisé (LRU)."""
    import threading
    import time
    from collections import OrderedDict

    _ABSENT = object()


    class TTLCache:
        """Cache LRU borné, avec durée de vie par entrée.

        - `maxsize` : nombre maximal d'entrées ; au-delà, l'entrée la MOINS récemment utilisée est évincée.
        - `ttl` : durée de vie par défaut, en SECONDES ; None = n'expire jamais.
        - `clock` : fonction d'horloge injectable (par défaut time.monotonic), utile pour les tests.
        Toutes les opérations publiques sont protégées par un verrou réentrant.
        """

        def __init__(self, maxsize=128, ttl=60.0, clock=time.monotonic):
            if maxsize <= 0:
                raise ValueError("maxsize doit être > 0")
            self.maxsize = maxsize
            self.ttl = ttl
            self._clock = clock
            self._data = OrderedDict()  # clé -> (valeur, instant d'expiration ou None)
            self._lock = threading.RLock()
            self._hits = 0
            self._misses = 0
            self._evictions = 0

        def _expiry(self, ttl):
            ttl = self.ttl if ttl is None else ttl
            return None if ttl is None else self._clock() + ttl

        def _is_expired(self, expires):
            return expires is not None and self._clock() >= expires

        def set(self, key, value, ttl=None):
            """Insère ou remplace une entrée ; `ttl` surcharge la durée par défaut. L'entrée devient la plus récente."""
            with self._lock:
                self._data[key] = (value, self._expiry(ttl))
                while len(self._data) > self.maxsize:
                    self._data.popitem(last=False)
                    self._evictions += 1

        def get(self, key, default=None):
            """Retourne la valeur si présente et non expirée (et la marque comme récemment utilisée), sinon `default`."""
            with self._lock:
                item = self._data.get(key, _ABSENT)
                if item is _ABSENT:
                    self._misses += 1
                    return default
                value, expires = item
                if self._is_expired(expires):
                    self._misses += 1
                    return default
                self._hits += 1
                self._data.move_to_end(key)
                return value

        def get_or_set(self, key, factory, ttl=None):
            """Retourne la valeur en cache ou la calcule avec `factory()` puis la stocke."""
            with self._lock:
                value = self.get(key, _ABSENT)
                if value is _ABSENT:
                    value = factory()
                    self.set(key, value, ttl)
                return value

        def delete(self, key):
            """Supprime une entrée ; retourne True si elle existait."""
            with self._lock:
                return self._data.pop(key, None) is not None

        def purge(self):
            """Retire toutes les entrées expirées et retourne leur nombre."""
            with self._lock:
                dead = [k for k, (_, e) in self._data.items() if self._is_expired(e)]
                for k in dead:
                    del self._data[k]
                return len(dead)

        def __len__(self):
            """Nombre d'entrées VALIDES (non expirées)."""
            with self._lock:
                return len(self._data)

        def __contains__(self, key):
            with self._lock:
                item = self._data.get(key, _ABSENT)
                return item is not _ABSENT and not self._is_expired(item[1])

        def stats(self):
            """Dictionnaire {hits, misses, evictions, size, hit_rate}."""
            with self._lock:
                total = self._hits + self._misses
                return {"hits": self._hits, "misses": self._misses, "evictions": self._evictions,
                        "size": len(self), "hit_rate": self._hits / total if total else 0.0}
''')
w("work/t3/test_ttlcache.py", '''
    import unittest
    from ttlcache import TTLCache
    class Horloge:
        def __init__(self): self.t = 0.0
        def __call__(self): return self.t
    class T(unittest.TestCase):
        def test_expiration(self):
            h = Horloge(); c = TTLCache(4, ttl=10, clock=h); c.set("a", 1)
            h.t = 9.9; self.assertEqual(c.get("a"), 1); h.t = 10; self.assertIsNone(c.get("a"))
        def test_lru(self):
            c = TTLCache(2, ttl=None); c.set("a", 1); c.set("b", 2); c.get("a"); c.set("c", 3)
            self.assertIn("a", c); self.assertNotIn("b", c)
        def test_len_ignore_expires(self):
            h = Horloge(); c = TTLCache(4, ttl=5, clock=h); c.set("a", 1); c.set("b", 2); h.t = 6
            self.assertEqual(len(c), 0)
    if __name__ == "__main__": unittest.main()
''')
w("prompts/t3.txt", '''
    Le dossier contient ttlcache.py et test_ttlcache.py. Fais deux choses :
    1) Lis ttlcache.py et écris RESUME.md : un résumé fidèle (10 à 20 lignes) de son rôle, de son API publique, de ses garanties (éviction, expiration, concurrence) et de ses limites. N'invente rien : chaque affirmation doit être vérifiable dans le code.
    2) Un test échoue (python3 -m unittest). Trouve la cause dans ttlcache.py et corrige-la avec le changement MINIMAL (ne réécris pas le module, ne modifie pas les tests). Relance les tests pour confirmer.
''')
w("verif/t3_hidden.py", '''
    import sys, unittest
    sys.path.insert(0, sys.argv[1])
    from ttlcache import TTLCache
    class H:
        def __init__(s): s.t = 0.0
        def __call__(s): return s.t
    class T(unittest.TestCase):
        def test_len_expired(self):
            h = H(); c = TTLCache(4, ttl=5, clock=h); c.set("a", 1); c.set("b", 2); h.t = 6; self.assertEqual(len(c), 0)
        def test_len_mixed(self):
            h = H(); c = TTLCache(4, ttl=5, clock=h); c.set("a", 1); h.t = 3; c.set("b", 2, ttl=10); h.t = 6; self.assertEqual(len(c), 1)
        def test_stats_size(self):
            h = H(); c = TTLCache(4, ttl=5, clock=h); c.set("a", 1); h.t = 6; self.assertEqual(c.stats()["size"], 0)
        def test_still_works(self):
            c = TTLCache(2, ttl=None); c.set("a", 1); c.set("b", 2); c.get("a"); c.set("c", 3)
            self.assertEqual(len(c), 2); self.assertIn("a", c); self.assertNotIn("b", c)
        def test_purge(self):
            h = H(); c = TTLCache(4, ttl=5, clock=h); c.set("a", 1); c.set("b", 2, ttl=100); h.t = 6; self.assertEqual(c.purge(), 1); self.assertEqual(len(c), 1)
    unittest.main(argv=["x"])
''')
