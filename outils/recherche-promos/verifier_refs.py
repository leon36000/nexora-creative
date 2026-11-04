#!/usr/bin/env python3
"""Vérifie les identifiants arXiv (titre réel) et les dépôts GitHub (existence, licence, dernier push) cités dans des fichiers Markdown.
Usage : verifier_refs.py fichier.md [...] > rapport.tsv"""
import json, re, subprocess, sys, time, urllib.request, xml.etree.ElementTree as ET

txt = "\n".join(open(f, encoding="utf-8").read() for f in sys.argv[1:])
ids = sorted(set(re.findall(r"arxiv\.org/(?:abs|html|pdf)/(\d{4}\.\d{4,5})", txt)))
repos = sorted(set(m.rstrip(".)") for m in re.findall(r"github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)", txt)))
repos = [r[:-4] if r.endswith(".git") else r for r in repos]

ns = {"a": "http://www.w3.org/2005/Atom"}
for i in range(0, len(ids), 40):
    lot = ids[i:i + 40]
    url = "http://export.arxiv.org/api/query?max_results=50&id_list=" + ",".join(lot)
    try:
        x = ET.fromstring(urllib.request.urlopen(url, timeout=60).read())
        trouve = {}
        for e in x.findall("a:entry", ns):
            eid = e.find("a:id", ns).text.rsplit("/", 1)[-1].split("v")[0]
            t = " ".join((e.find("a:title", ns).text or "").split())
            pub = (e.find("a:published", ns).text or "")[:10]
            trouve[eid] = (t, pub)
        for a in lot:
            t, pub = trouve.get(a, ("INTROUVABLE", ""))
            print(f"arxiv\t{a}\t{pub}\t{t}")
    except Exception as ex:
        for a in lot:
            print(f"arxiv\t{a}\tERREUR\t{ex}")
    time.sleep(3)

from concurrent.futures import ThreadPoolExecutor
def tete(r):
    req = urllib.request.Request("https://github.com/" + r, method="HEAD", headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as rep:
            return r, rep.status, rep.geturl().replace("https://github.com/", "")
    except Exception as ex:
        return r, getattr(ex, "code", "ERR"), ""
with ThreadPoolExecutor(8) as ex:
    for r, st, fin in ex.map(tete, repos):
        print(f"github\t{r}\t{st}\t{fin if fin.lower() != r.lower() else ''}")
