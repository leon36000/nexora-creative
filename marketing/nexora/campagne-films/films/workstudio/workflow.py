"""Workflow réel filmé dans WorkStudio : « Tri du courrier entrant » (courriel → tri → brouillon → validation humaine → envoi).

Construit à partir de la structure du modèle « Contrôle de conformité » (bloc de validation human_in_the_loop_v2 et condition
identiques), avec un contenu générique (boulangerie fictive, aucune donnée de client). L'envoi (bloc SMTP, le bloc API refuse le texte multiligne dans un corps JSON) part vers le SMTP de Mailpit, le courrier
factice interne de la VM 203 : rien ne sort du réseau.
Deux langues (fr, en) et deux courriels entrants (1 : changement de commande ; 2 : demande de soumission) pour filmer deux vraies exécutions
différentes. Usage :
  python3 workflow.py creer <fr|en> > charge.js   puis   node api.mjs <temoins> charge.js   (crée le workflow, affiche son id)
  python3 workflow.py maj <id> <fr|en> <1|2> > charge.js   (remplace l’état : change le courriel entrant et le sujet de l’envoi)
"""
import json
import uuid

ESPACE = "2c6a3931-c0e3-4a3f-b3f8-9bb7f517f45a"
MODELE = "vllm/nexora-default"
TEXTES = {
    "fr": {
        "nom": "Tri du courrier entrant", "desc": "Trie un courriel, rédige la réponse et attend votre accord avant l’envoi.",
        "blocs": ("Tri", "Brouillon", "Validation", "Approbation", "Envoi"), "champ": "envoyer", "entree": "courriel",
        "entree_desc": "Courriel reçu", "question": "Envoyer cette réponse à la cliente ?",
        "systeme": ("Vous écrivez pour une petite entreprise québécoise : français professionnel du Québec, vouvoiement, phrases courtes, "
                    "aucune information inventée. Si une donnée manque, signalez-la entre crochets."),
        "tri": "Vous triez le courrier entrant.",
        "tri_u": "Courriel reçu :\n<start.courriel>\n\nRépondez en trois lignes exactement :\nCatégorie : …\nUrgence : basse, moyenne ou haute, avec la raison en cinq mots\nÀ faire : une action concrète",
        "brou": "Vous répondez aux clients d'une boulangerie. Ne promettez rien qui n'est pas confirmé : proposez, et dites que l'équipe confirme.",
        "brou_u": "Courriel reçu :\n<start.courriel>\n\nTri :\n<tri.content>\n\nRédigez la réponse (cinq lignes au plus, texte simple sans mise en forme, signée « L'équipe de la boulangerie »).",
        "courriels": {
            1: ("Bonjour,\nJ'ai commandé un gâteau pour samedi 14 h (commande 4127). Serait-il possible de changer la saveur pour "
                "chocolat-framboise et de le livrer plutôt à 11 h ?\nMerci beaucoup,\nJulie"),
            2: ("Bonjour,\nPourriez-vous me faire une soumission pour 40 croissants et 20 pains au chocolat, livrés vendredi à 8 h 30 "
                "à notre bureau ?\nMerci,\nMarc")},
        "sujets": {1: "Votre commande 4127", 2: "Votre soumission"}, "dest": {1: "julie@exemple.test", 2: "marc@exemple.test"},
    },
    "en": {
        "nom": "Incoming mail triage", "desc": "Sorts an email, drafts the reply and waits for your approval before sending.",
        "blocs": ("Triage", "Draft", "Review", "Approved", "Send"), "champ": "send", "entree": "email",
        "entree_desc": "Email received", "question": "Send this reply to the customer?",
        "systeme": ("You write for a small Canadian business: clear, professional English, short sentences, "
                    "nothing invented. If a detail is missing, flag it in square brackets."),
        "tri": "You triage incoming mail.",
        "tri_u": "Email received:\n<start.email>\n\nAnswer in exactly three lines:\nCategory: …\nUrgency: low, medium or high, with the reason in five words\nTo do: one concrete action",
        "brou": "You reply to the customers of a bakery. Promise nothing that is not confirmed: propose, and say the team will confirm.",
        "brou_u": "Email received:\n<start.email>\n\nTriage:\n<triage.content>\n\nWrite the reply (five lines at most, plain text, no formatting, signed \"The bakery team\").",
        "courriels": {
            1: ("Hello,\nI ordered a cake for Saturday at 2 pm (order 4127). Could you change the flavour to "
                "chocolate-raspberry and deliver it at 11 am instead?\nThank you,\nJulie"),
            2: ("Hello,\nCould you send me a quote for 40 croissants and 20 pains au chocolat, delivered Friday at 8:30 am "
                "to our office?\nThanks,\nMarc")},
        "sujets": {1: "Your order 4127", 2: "Your quote"}, "dest": {1: "julie@exemple.test", 2: "marc@exemple.test"},
    },
}


def u():
    return str(uuid.uuid4())


def sb(id_, type_, valeur):
    return {"id": id_, "type": type_, "value": valeur}


def bloc(id_, type_, nom, x, y, sous):
    return {"id": id_, "type": type_, "name": nom, "position": {"x": x, "y": y}, "subBlocks": {k: sb(k, t, v) for k, (t, v) in sous.items()},
            "outputs": {}, "enabled": True, "horizontalHandles": True, "advancedMode": False, "triggerMode": False, "height": 0}


def etat(langue="fr", n=1):
    T = TEXTES[langue]
    n_tri, n_brou, n_val, n_app, n_env = T["blocs"]
    ref = lambda b, c: f"<{b.lower()}.{c}>"  # noqa: E731
    d, t, b, v, c, e = (u() for _ in range(6))
    blocs = [
        bloc(d, "start_trigger", "Start", 0, 0, {"nexoraView": ("short-input", "etapes"), "inputFormat": ("input-format", [
            {"id": u(), "name": T["entree"], "type": "string", "value": T["courriels"][n], "collapsed": False, "description": T["entree_desc"]}])}),
        bloc(t, "agent", n_tri, 360, 0, {"model": ("combobox", MODELE), "messages": ("messages-input", [
            {"role": "system", "content": T["systeme"] + " " + T["tri"]}, {"role": "user", "content": T["tri_u"]}])}),
        bloc(b, "agent", n_brou, 720, 0, {"model": ("combobox", MODELE), "messages": ("messages-input", [
            {"role": "system", "content": T["systeme"] + " " + T["brou"]}, {"role": "user", "content": T["brou_u"]}])}),
        bloc(v, "human_in_the_loop_v2", n_val, 1080, 0, {
            "builderData": ("input-format", [{"id": u(), "name": "brouillon" if langue == "fr" else "draft", "type": "string",
                                              "value": ref(n_brou, "content"), "collapsed": False}]),
            "inputFormat": ("input-format", [{"id": u(), "name": T["champ"], "type": "boolean", "value": "", "required": True, "collapsed": False,
                                              "description": T["question"]}]),
            "notification": ("tool-input", [])}),
        bloc(c, "condition", n_app, 1440, 0, {"conditions": ("condition-input", json.dumps([
            {"id": f"{c}-if", "title": "if", "value": "String(" + ref(n_val, T["champ"]) + " ?? '').trim().toLowerCase() === \"true\""},
            {"id": f"{c}-else", "title": "else", "value": ""}]))}),
        bloc(e, "smtp", n_env, 1800, 0, {"smtpHost": ("short-input", "mailpit"), "smtpPort": ("short-input", "1025"),
                                        "smtpUsername": ("short-input", "essai"), "smtpPassword": ("short-input", "essai"),
                                        "smtpSecure": ("dropdown", "None"), "from": ("short-input", "commandes@boulangerie.test"),
                                        "to": ("short-input", T["dest"][n]), "subject": ("short-input", T["sujets"][n]),
                                        "body": ("long-input", ref(n_brou, "content")), "contentType": ("dropdown", "text")}),
    ]
    aretes = [{"id": u(), "source": a, "target": z, "sourceHandle": h, "targetHandle": "target", "type": "default", "data": {}}
              for a, z, h in ((d, t, "source"), (t, b, "source"), (b, v, "source"), (v, c, "source"), (c, e, f"condition-{c}-if"))]
    return {"blocks": {x["id"]: x for x in blocs}, "edges": aretes, "loops": {}, "parallels": {}}


if __name__ == "__main__":
    import sys
    cmd = sys.argv[1]
    if cmd == "json":  # python3 workflow.py json <langue> <n> : l'état seul (utilisé par capturer.mjs)
        print(json.dumps(etat(sys.argv[2], int(sys.argv[3])), ensure_ascii=False))
    elif cmd == "maj":  # python3 workflow.py maj <id> <langue> <n>
        _, _, i, l, n = sys.argv
        print(f"const r = await fetch('/api/workflows/{i}/state', {{ method: 'PUT', headers: {{ 'Content-Type': 'application/json' }}, body: JSON.stringify({json.dumps(etat(l, int(n)), ensure_ascii=False)}) }}); return [r.status, (await r.text()).slice(0, 300)];")
    else:  # python3 workflow.py creer <langue>
        l = sys.argv[2]
        print(f"""const c = await (await fetch('/api/workflows', {{ method: 'POST', headers: {{ 'Content-Type': 'application/json' }},
  body: JSON.stringify({{ name: {json.dumps(TEXTES[l]['nom'], ensure_ascii=False)}, description: {json.dumps(TEXTES[l]['desc'], ensure_ascii=False)},
  workspaceId: '{ESPACE}', color: '#FF5A1F' }}) }})).json();
const id = c.id || c.data?.id;
const r = await fetch('/api/workflows/' + id + '/state', {{ method: 'PUT', headers: {{ 'Content-Type': 'application/json' }},
  body: JSON.stringify({json.dumps(etat(l, 1), ensure_ascii=False)}) }});
return {{ id, etat: r.status, corps: (await r.text()).slice(0, 300) }};""")
