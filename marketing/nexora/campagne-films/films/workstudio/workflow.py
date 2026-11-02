"""Workflow réel filmé dans WorkStudio : « Tri du courrier entrant » (courriel → tri → brouillon → validation humaine → envoi).

Construit à partir de la structure du modèle « Contrôle de conformité » (bloc de validation human_in_the_loop_v2 et condition
identiques), avec un contenu générique (boulangerie fictive, aucune donnée de client). L'envoi (bloc API) part vers l'API de Mailpit, le courrier
factice interne de la VM 203 : rien ne sort du réseau.
Usage : python3 workflow.py > charge.js   puis   node api.mjs <temoins> charge.js   (crée le workflow, affiche son id)
"""
import json
import uuid

ESPACE = "2c6a3931-c0e3-4a3f-b3f8-9bb7f517f45a"
MODELE = "vllm/nexora-default"
SYSTEME = ("Vous écrivez pour une petite entreprise québécoise : français professionnel du Québec, vouvoiement, phrases courtes, "
           "aucune information inventée. Si une donnée manque, signalez-la entre crochets.")
COURRIEL = ("Bonjour,\nJ'ai commandé un gâteau pour samedi 14 h (commande 4127). Serait-il possible de changer la saveur pour "
            "chocolat-framboise et de le livrer plutôt à 11 h ?\nMerci beaucoup,\nJulie")


def u():
    return str(uuid.uuid4())


def sb(id_, type_, valeur):
    return {"id": id_, "type": type_, "value": valeur}


def bloc(id_, type_, nom, x, y, sous):
    return {"id": id_, "type": type_, "name": nom, "position": {"x": x, "y": y}, "subBlocks": {k: sb(k, t, v) for k, (t, v) in sous.items()},
            "outputs": {}, "enabled": True, "horizontalHandles": True, "advancedMode": False, "triggerMode": False, "height": 0}


def etat():
    d, t, b, v, c, e = (u() for _ in range(6))
    blocs = [
        bloc(d, "start_trigger", "Start", 0, 0, {"nexoraView": ("short-input", "etapes"), "inputFormat": ("input-format", [
            {"id": u(), "name": "courriel", "type": "string", "value": COURRIEL, "collapsed": False, "description": "Courriel reçu"}])}),
        bloc(t, "agent", "Tri", 360, 0, {"model": ("combobox", MODELE), "messages": ("messages-input", [
            {"role": "system", "content": SYSTEME + " Vous triez le courrier entrant."},
            {"role": "user", "content": "Courriel reçu :\n<start.courriel>\n\nRépondez en trois lignes exactement :\nCatégorie : …\n"
                                        "Urgence : basse, moyenne ou haute, avec la raison en cinq mots\nÀ faire : une action concrète"}])}),
        bloc(b, "agent", "Brouillon", 720, 0, {"model": ("combobox", MODELE), "messages": ("messages-input", [
            {"role": "system", "content": SYSTEME + " Vous répondez aux clients d'une boulangerie. Ne promettez rien qui n'est pas "
                                                     "confirmé : proposez, et dites que l'équipe confirme."},
            {"role": "user", "content": "Courriel reçu :\n<start.courriel>\n\nTri :\n<tri.content>\n\nRédigez la réponse (cinq lignes au plus, "
                                        "texte simple sans mise en forme, signée « L'équipe de la boulangerie »)."}])}),
        bloc(v, "human_in_the_loop_v2", "Validation", 1080, 0, {
            "builderData": ("input-format", [{"id": u(), "name": "brouillon", "type": "string", "value": "<brouillon.content>", "collapsed": False}]),
            "inputFormat": ("input-format", [{"id": u(), "name": "envoyer", "type": "boolean", "value": "", "required": True, "collapsed": False,
                                              "description": "Envoyer cette réponse à la cliente ?"}]),
            "notification": ("tool-input", [])}),
        bloc(c, "condition", "Approbation", 1440, 0, {"conditions": ("condition-input", json.dumps([
            {"id": f"{c}-if", "title": "if", "value": "String(<validation.envoyer> ?? '').trim().toLowerCase() === \"true\""},
            {"id": f"{c}-else", "title": "else", "value": ""}]))}),
        bloc(e, "api", "Envoi", 1800, 0, {"url": ("short-input", "http://mailpit:8025/api/v1/send"), "method": ("dropdown", "POST"),
                                          "headers": ("table", [{"id": u(), "cells": {"Key": "Content-Type", "Value": "application/json"}}]),
                                          "body": ("code", '{"From": {"Email": "commandes@boulangerie.test"}, "To": [{"Email": "julie@exemple.test"}], '
                                                           '"Subject": "Votre commande 4127", "Text": <brouillon.content>}')}),
    ]
    aretes = [{"id": u(), "source": a, "target": z, "sourceHandle": h, "targetHandle": "target", "type": "default", "data": {}}
              for a, z, h in ((d, t, "source"), (t, b, "source"), (b, v, "source"), (v, c, "source"), (c, e, f"condition-{c}-if"))]
    return {"blocks": {x["id"]: x for x in blocs}, "edges": aretes, "loops": {}, "parallels": {}}


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:  # mise à jour : python3 workflow.py <id>
        print(f"const r = await fetch('/api/workflows/{sys.argv[1]}/state', {{ method: 'PUT', headers: {{ 'Content-Type': 'application/json' }}, body: JSON.stringify({json.dumps(etat(), ensure_ascii=False)}) }}); return [r.status, (await r.text()).slice(0, 300)];")
        sys.exit()
    print(f"""const c = await (await fetch('/api/workflows', {{ method: 'POST', headers: {{ 'Content-Type': 'application/json' }},
  body: JSON.stringify({{ name: 'Tri du courrier entrant', description: 'Trie un courriel, rédige la réponse et attend votre accord avant l’envoi.',
  workspaceId: '{ESPACE}', color: '#FF5A1F' }}) }})).json();
const id = c.id || c.data?.id;
const r = await fetch('/api/workflows/' + id + '/state', {{ method: 'PUT', headers: {{ 'Content-Type': 'application/json' }},
  body: JSON.stringify({json.dumps(etat(), ensure_ascii=False)}) }});
return {{ id, etat: r.status, corps: (await r.text()).slice(0, 300) }};""")
