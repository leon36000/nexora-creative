"""Étape « rapport » du comparatif v2 : une fiche par film + la synthèse (coût LLM, prix client en crédits, secondes GPU par
machine, réparations, rythme, mesures audio, notes sévères écrites à la main dans notes.json).

  python3 rapport.py         → rapports/<film>.md et rapports/SYNTHESE.md (pas de binaire : les planches restent sur disque)
Prix client = coût fournisseur × 1,10 × 1,4025 × 100 crédits (1 crédit = 1 ¢ CA). Opus 5.5 (abonnement de l'outil) : jetons
du sous-agent seulement, pas de coût fournisseur mesuré.
"""
import json
from pathlib import Path

ICI = Path(__file__).resolve().parent
TRAVAIL = ICI / "films"  # copies des JSON de chaque film (les binaires sont sur pc1)
CRITERES = ["concept", "produit", "accroche", "spectacle", "texte_voix", "rythme", "son", "finition"]
LIB = {"eco": "Éco · DeepSeek V4.1 Flash", "equilibre": "Équilibré · Muse Spark 1.3", "expert": "Expert · Gemini 4 Argon Flex",
       "opus": "Opus 5.5 (effort high)"}


def lire(f, defaut=None):
    return json.loads(f.read_text()) if f.exists() else defaut


def main():
    notes = lire(ICI / "notes.json", {})
    out = ICI / "rapports"
    out.mkdir(exist_ok=True)
    lignes = ["# Comparatif v2 : 12 films écrits entièrement par le modèle (synthèse)", "",
              "| Film | Palier | Effort | Jetons e/s | USD LLM | Crédits client | GPU GB10 (s) | GPU pc1 (s) | Réparations | Plans | BPM mesuré | LUFS / dBTP | Note /10 |",
              "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for b in ("creative", "opsys", "workstudio"):
        for p in ("eco", "equilibre", "expert", "opus"):
            nom = f"{b}-{p}"
            dos = TRAVAIL / nom
            a = lire(dos / "auteur.json", {})
            pl = lire(dos / "plaques.json", {"gpu_s": {}, "plaques": {}})
            r = lire(dos / "rythme.json", {})
            rv = next(iter(lire(dos / "revue.json", {}).values()), {})
            n = notes.get(nom, {})
            g = pl["gpu_s"]
            gb10, pc1 = g.get("gb10-qwen", 0) + g.get("gb10-music3", 0), g.get("pc1-h3-fast", 0) + g.get("pc1-h3-max", 0)
            moy = round(sum(n.get(c, 0) for c in CRITERES) / len(CRITERES), 1) if n else None
            rep = len(a.get("reparations_modele", [])), len(a.get("reparations_code", []))
            regen = sum(x.get("regen_cle", 0) + x.get("regen_video", 0) + (1 if x.get("rejet_visuel") else 0) for x in pl["plaques"].values())
            usd = a.get("usd")
            cr = a.get("credits_client")
            jet = f"{a['jetons_sous_agent_total']} (total sous-agent)" if a.get("jetons_sous_agent_total") else \
                f"{a.get('jetons_entree', '?')}/{a.get('jetons_sortie', '?')}"
            lignes.append(f"| {b} | {LIB[p]} | {a.get('effort', 'high' if p == 'opus' else '?')} | {jet} | {usd if usd is not None else '—'} | "
                          f"{cr if cr is not None else '—'} | {gb10:.0f} | {pc1:.0f} | modèle {rep[0]}, code {rep[1]}, plaques {regen} | "
                          f"{r.get('plans', '?')} | {r.get('musique', {}).get('bpm', '?')} | {rv.get('lufs', '?')} / {rv.get('crete_dbtp', '?')} | {moy if moy is not None else '—'} |")
            fiche = [f"# {nom} ({LIB[p]})", "",
                     f"Fichier : `~/nexora-creative-data/promo/montage/Test2-{b}-{p}-16x9-fr.mp4` · planches : `pc1:~/Bureau/Nexora-Livrables/2026-11-03/rapports/planches/planche-{nom}-16x9-fr-long.jpg` et `planche-plaques-{nom}.jpg`", "",
                     f"- Effort : {a.get('effort', 'high' if p == 'opus' else '?')} ; essais d'effort refusés : {a.get('effort_essais', [])}",
                     f"- Jetons entrée/sortie : {jet} ; coût LLM {usd} USD ; prix client {cr} crédits ; latence {a.get('latence_s', '?')} s",
                     f"- Réparations demandées au modèle : {a.get('reparations_modele', [])}",
                     f"- Réparations du code : {a.get('reparations_code', [])} ; violations finales : {a.get('violations_finales', [])}",
                     f"- GPU : GB10 {gb10:.0f} s (Qwen {g.get('gb10-qwen', 0):.0f}, Music3 {g.get('gb10-music3', 0):.0f}) ; pc1 RTX 5090 {pc1:.0f} s "
                     f"(h3-fast {g.get('pc1-h3-fast', 0):.0f}, h3-max {g.get('pc1-h3-max', 0):.0f}) ; plaques régénérées : {regen}",
                     f"- Rythme : {r.get('plans')} plans, plan moyen {r.get('plan_moyen_s')} s, tempo demandé {lire(dos / 'film.json', {}).get('musique', {}).get('tempo_bpm')} "
                     f"→ mesuré {r.get('musique', {}).get('bpm')} BPM, écart moyen des coupes recalées {r.get('ecart_coupes_moyen_s')} s, durée {r.get('duree_s')} s",
                     f"- Audio : {rv.get('lufs')} LUFS, crête vraie {rv.get('crete_dbtp')} dBTP, LRA {rv.get('lra')}", "",
                     "## Notes sévères (/10)", "", " · ".join(f"{c} {n.get(c, '—')}" for c in CRITERES) + f" → **{moy}**", "",
                     n.get("commentaire", ""), ""]
            (out / f"{nom}.md").write_text("\n".join(fiche))
    lignes += ["", "Notes : grille sévère de l'étranger (concept, produit évident, accroche, spectacle, texte/voix, rythme, son, finition), "
               "écrite à la main après visionnage des planches et des films ; voir chaque fiche. Le fondateur est le juge."]
    (out / "SYNTHESE.md").write_text("\n".join(lignes) + "\n")
    print("\n".join(lignes))


if __name__ == "__main__":
    main()
