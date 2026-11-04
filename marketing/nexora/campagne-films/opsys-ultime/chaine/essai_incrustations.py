"""Rendu des deux planches et mesure reproductible du moteur OPSYS-AI.

Exécuter : python3 essai_incrustations.py
Les effets courts sont prolongés sur la planche pour comparer les cinq instants
imposés. Le flash est déjà éteint après sa quatrième image, comme au montage.
"""
from pathlib import Path
from time import perf_counter
import json

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from incrustations import Incrustations, Surface, TYPES, compteur_texte

MARQUE = {
    'nom':'OPSYS-AI','logo':None,'editeur':'par Nexora',
    'signature':"Les ressources d'une grande entreprise. À *votre* taille.",
    'mentions':'Film de vision. Certaines fonctions sont en préparation. Données fictives.',
    'couleurs':{'encre':[8,8,10],'os':[246,244,238],'brume':[160,160,172],
                'signal':[255,90,31],'ion':[90,170,255]},
    'polices':{'dossier':'~/Desktop/NexoraSite/web/src/fonts',
               'titre':'geist-latin-wght-normal.woff2',
               'mono':'jetbrains-mono-latin-wght-normal.woff2'}
}
EXEMPLES = {
    'statut':{'texte':'Photo reçue. Mesures en cours…'},
    'document':{'titre':'SOUMISSION 2417','destinataire':'M. Morin · revêtement de vinyle',
                'lignes':[['Mur avant','38,2 m²'],['Mur latéral','24,6 m²'],
                          ['Moulures et coins','46 m'],["Main-d'œuvre",'3 jours']],
                'total':'18 940 $','tampon':'PRÊTE'},
    'compteur':{'de':0,'a':7,'suffixe':' %','etiquette':'PRODUCTIVITÉ'},
    'courbe':{'points':[10,12,11,14,15,17,18,21,23],'pointille_depuis':5,
              'etiquette':'PROFITS ANTICIPÉS','valeur':'+7 %'},
    'cedule':{'semaines':3,'titre':'CÉDULE · 3 SEMAINES',
              'blocs':[[0,0,2,0,'Chantier Morin'],[0,3,4,1,'Gouttières Lavoie'],
                       [1,0,1,0,'Soffite Gagnon'],[1,2,4,2,'Revêtement Roy'],
                       [2,0,4,0,'Chantier Côté']]},
    'pointage':{'heure':'06:58','nom':'Kevin Tremblay','etat':'ARRIVÉE'},
    'appel':{'nom':'Adjointe','sous_titre':'Appel entrant','voix':'demo'},
    'trajet':{'points':[[.1,.8],[.35,.3],[.6,.55],[.9,.2]],'couleur':'ion'},
    'flash':{'intensite':.85,'duree_f':24},
    'glitch':{'intensite':.65,'duree_f':24},
    'carton':{}
}
SPECS = {t:dict(type=t,duree_f=120,**EXEMPLES[t]) if 'duree_f' not in EXEMPLES[t]
         else dict(type=t,**EXEMPLES[t]) for t in TYPES}


def fond_simule(W,H):
    """Bleu nuit photographique, grain fixe et volumes flous simulés."""
    rng = np.random.default_rng(412)
    y,x = np.mgrid[0:H,0:W].astype(np.float32)
    x/=W
    y/=H
    lumiere = np.exp(-((x-.27)**2/.21+(y-.35)**2/.3))
    grain = rng.normal(0,1.9,(H,W)).astype(np.float32)
    rgb = np.empty((H,W,3),dtype=np.uint8)
    for i,(base,force) in enumerate(((6,13),(13,22),(25,34))):
        rgb[:,:,i]=np.clip(base+force*lumiere+grain,0,255).astype(np.uint8)
    im = Image.fromarray(rgb)
    # Volumes architecturaux discrets, pour juger la transparence du verre.
    formes = Image.new('RGB',(W//8,H//8))
    d = ImageDraw.Draw(formes)
    d.polygon([(0,H//8),(W*.15/8,H*.45/8),(W*.53/8,H*.34/8),
               (W*.74/8,H//8)],fill=(19,28,40))
    d.rectangle((W*.72/8,0,W*.87/8,H//8),fill=(9,14,23))
    formes=formes.filter(ImageFilter.GaussianBlur(3)).resize((W,H),Image.Resampling.BILINEAR)
    return Image.blend(im,formes,.22)


def enveloppe_demo():
    # Enveloppe float32 à 24 i/s : pauses et syllabes, pour exercer l'entrée voix.
    t=np.arange(240,dtype=np.float32)/24
    return np.clip((.5+.4*np.sin(t*3.7))*(.3+.7*np.sin(t*11)**2),0,1).astype(np.float32)


def planche(W,H,chemin):
    moteur=Incrustations(MARQUE,W,H,{'demo':enveloppe_demo()})
    fond=fond_simule(W,H)
    vw,vh=384,round(384*H/W)
    marge,legende,haut=18,48,74
    resultat=Image.new('RGB',(5*vw+6*marge,haut+len(TYPES)*(vh+legende+marge)+marge),(12,14,20))
    d=ImageDraw.Draw(resultat)
    f=moteur.font(16,True)
    d.text((marge,17),f'OPSYS-AI  /  ÉTUDE DE MOUVEMENT  /  {W} × {H}',font=moteur.font(23),fill=(246,244,238))
    d.text((marge,47),'Lecture par ligne : entrée, déploiement, contenu, milieu, fin.',font=f,fill=(160,160,172))
    for ligne,typ in enumerate(TYPES):
        spec=SPECS[typ]
        duree=spec['duree_f']/24
        instants=[.15,.4,.8,.5*duree,.9*duree]
        for colonne,u in enumerate(instants):
            rendu=moteur.poser(fond,spec,u)
            assert rendu.mode=='RGB' and rendu.size==(W,H)
            # L'animation ne doit modifier ni le fond ni la spécification.
            x,y=marge+colonne*(vw+marge),haut+ligne*(vh+legende+marge)
            resultat.paste(rendu.resize((vw,vh),Image.Resampling.LANCZOS),(x,y))
            d.text((x,y+vh+8),f'{typ.upper()}   {u:.2f} s',font=f,fill=(246,244,238))
            phase=['entrée','déploiement','contenu','50 %','90 %'][colonne]
            d.text((x,y+vh+28),phase,font=moteur.font(12,True),fill=(160,160,172))
        print(f'  {W}×{H} : {typ}',flush=True)
    resultat.save(chemin,quality=90,subsampling=0)
    return moteur,fond


def mesurer(moteur,fond):
    print('\nCoût moyen 1920×1080 — 20 images/type, caches chauds, copie et composition incluses :')
    mesures={}
    for typ,spec in SPECS.items():
        duree=spec['duree_f']/24
        instants=np.linspace(.04,duree-.025,20)
        for u in (.4,min(.8,duree*.5)):
            moteur.poser(fond,spec,u)
        debut=perf_counter()
        for u in instants:
            moteur.poser(fond,spec,float(u))
        ms=(perf_counter()-debut)*1000/len(instants)
        mesures[typ]=round(ms,3)
        print(f'  {typ:11s} {ms:7.2f} ms  {"OK" if ms<60 else "À OPTIMISER"}',flush=True)
    Path('mesures-incrustations.json').write_text(json.dumps(mesures,indent=2)+'\n',encoding='utf-8')
    return mesures


def verifier(moteur,fond):
    """Contrôles utiles : pureté, déterminisme et fin des effets transitoires."""
    avant=fond.tobytes()
    specs_avant=json.dumps(SPECS,sort_keys=True)
    for typ,spec in SPECS.items():
        a=moteur.poser(fond,spec,.8)
        b=moteur.poser(fond,spec,.8)
        assert a.tobytes()==b.tobytes(),f'{typ} non déterministe'
        assert moteur.poser(fond,spec,spec['duree_f']/24).tobytes()==avant
    assert fond.tobytes()==avant,'Le fond a été modifié'
    assert json.dumps(SPECS,sort_keys=True)==specs_avant
    assert compteur_texte('18 940 $',1)=='18\u202f940 $'
    assert compteur_texte('+12,50 $',1)=='+12,50 $'
    assert moteur.poser(fond,SPECS['flash'],4/24).tobytes()==avant
    # Les types de production courts et les variantes du contrat.
    moteur.poser(fond,dict(type='glitch',duree_f=6,intensite=1),.15)
    moteur.poser(fond,dict(type='compteur',duree_f=72,de=1234,a=2345,
                         decimales=2,prefixe='$ ',suffixe='',etiquette='REVENU'),1)
    moteur.poser(fond,dict(type='courbe',duree_f=48,points=[10,10],valeur='10'),.8)
    pic=moteur.poser(fond,dict(type='flash',duree_f=6,intensite=1),1/24)
    assert pic.getextrema()==((255,255),(246,246),(230,230))
    # Une valeur réelle de voix doit modifier l'onde à temps égal.
    silence=Incrustations(MARQUE,moteur.W,moteur.H,{'demo':np.zeros(48,dtype=np.float32)})
    parole=Incrustations(MARQUE,moteur.W,moteur.H,{'demo':np.ones(48,dtype=np.float32)})
    assert silence.poser(fond,SPECS['appel'],.8).tobytes()!=parole.poser(fond,SPECS['appel'],.8).tobytes()
    # Vérifier les marges réelles dans les deux orientations et à grande échelle.
    positions=['centre','gauche','droite','haut','bas','haut-gauche',
               'haut-droite','bas-gauche','bas-droite']
    for W,H in [(1920,1080),(1080,1920)]:
        m=Incrustations(MARQUE,W,H)
        for position in positions:
            for echelle in [.65,1,1.8]:
                a=Surface(m,{'position':position,'echelle':echelle},(590,660),'droite')
                x,y=m._emplacement(a)
                mx,my=m.marges
                assert x+a.pad>=mx-1 and y+a.pad>=my-1
                assert x+a.pad+a.w<=W-mx+1 and y+a.pad+a.hh<=H-my+1
    moteur.poser(fond,dict(type='statut',duree_f=72,texte='Analyse|*terminée*.'),1)
    print('Contrôles : RGB, déterminisme, entrées immuables, flash, voix, marges et variantes — OK')


if __name__=='__main__':
    paysage,fond=planche(1920,1080,'planche-16x9.jpg')
    planche(1080,1920,'planche-9x16.jpg')
    verifier(paysage,fond)
    mesures=mesurer(paysage,fond)
    assert max(mesures.values())<60,'Budget de 60 ms dépassé.'
    print('\nPlanches enregistrées : planche-16x9.jpg et planche-9x16.jpg')
