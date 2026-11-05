"""Incrustations OPSYS-AI, déterministes, à 24 images/s (numpy et Pillow).

Les coordonnées graphiques sont exprimées sur une base de 1080 pixels courts.
Le verre est précalculé par taille ; seul le rectangle utile est composé en RGBA.
Aucun état d'animation mutable : un appel dépend uniquement de ses arguments.
"""
from __future__ import annotations

import math
import re
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FPS = 24


def borne(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def doux(x):
    x = borne(x)
    return x * x * (3 - 2 * x)


def sortie(x):
    return 1 - (1 - borne(x)) ** 3


def progression(u, debut, fin):
    return doux((u - debut) / max(0.001, fin - debut))


def nombre(v, decimales=0):
    """Groupes de milliers fins et virgule française, sans dépendre de locale."""
    return f'{v:,.{decimales}f}'.replace(',', '\u202f').replace('.', ',')


def compteur_texte(texte, t):
    m = re.search(r'[-+]?\d(?:[\d\s\u202f\u00a0]*\d)?(?:[,.]\d+)?', texte)
    if not m:
        return texte
    brut = re.sub(r'\s', '', m.group()).replace(',', '.')
    dec = len(brut.split('.')[1]) if '.' in brut else 0
    signe = '+' if brut.startswith('+') else ''
    return texte[:m.start()] + signe + nombre(float(brut) * t, dec) + texte[m.end():]


@lru_cache(maxsize=192)
def police(chemin, taille, graisse=600):
    """Les fontes variables ne sont modifiées qu'à leur création."""
    candidats = [chemin, '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf']
    for candidat in candidats:
        try:
            f = ImageFont.truetype(candidat, max(1, taille))
            try:
                f.set_variation_by_axes([graisse])
            except (OSError, ValueError, AttributeError):
                pass
            return f
        except OSError:
            continue
    return ImageFont.load_default()


class Surface:
    """Petit espace de dessin avec mesures logiques et typographie commune."""
    def __init__(self, moteur, spec, dimensions, position, verre=True):
        self.m = moteur
        self.l, self.h = dimensions
        sx, sy = moteur.marges
        disponible = min((moteur.W - 2 * sx) / self.l,
                         (moteur.H - 2 * sy) / self.h)
        self.k = min(moteur.s * max(.1, float(spec.get('echelle', 1))), disponible)
        self.w, self.hh = round(self.l * self.k), round(self.h * self.k)
        self.pad = max(2, round(22 * self.k))
        self.im = Image.new('RGBA', (self.w + 2*self.pad, self.hh + 2*self.pad))
        self.d = ImageDraw.Draw(self.im)
        self.position = spec.get('position', position)
        self.verre = verre

    def xy(self, x, y):
        return (round(x*self.k) + self.pad, round(y*self.k) + self.pad)

    def box(self, box):
        return (*self.xy(*box[:2]), *self.xy(*box[2:]))

    def font(self, taille, mono=False, gras=600):
        return self.m.font(taille*self.k, mono, gras)

    def largeur(self, texte, taille, mono=False, gras=600):
        lignes = str(texte).replace('*','').split('|')
        return max(self.font(taille, mono, gras).getlength(t) for t in lignes) / self.k

    def texte(self, x, y, texte, taille=24, couleur='os', mono=False,
              alpha=255, ancre='lt', gras=600):
        texte = str(texte)
        if '*' in texte or '|' in texte:
            # Conserver les ancres des chiffres et des libellés alignés à droite.
            for i, ligne in enumerate(texte.split('|')):
                largeur = self.largeur(ligne,taille,mono,gras)
                net = ligne.replace('*','')
                f = self.font(taille,mono,gras)
                decalage = (f.getbbox(net,anchor='l'+ancre[1])[1]
                            - f.getbbox(net,anchor='ls')[1])/self.k
                xx = x - largeur * {'l':0,'m':.5,'r':1}.get(ancre[0],0)
                for j, morceau in enumerate(ligne.split('*')):
                    self.texte(xx,y+decalage+i*taille*1.35,morceau,taille,
                               'signal' if j==1 else couleur,mono,alpha,'ls',gras)
                    xx += self.largeur(morceau,taille,mono,gras)
            return
        col = self.m.c[couleur] if isinstance(couleur, str) else couleur
        self.d.text(self.xy(x, y), texte, font=self.font(taille, mono, gras),
                    fill=(*col[:3], round(borne(alpha, 0, 255))), anchor=ancre)

    def ligne(self, points, couleur='ion', alpha=255, ep=1.5):
        col = self.m.c[couleur] if isinstance(couleur, str) else couleur
        if len(points) > 1:
            self.d.line([self.xy(*p) for p in points], fill=(*col[:3], round(alpha)),
                        width=max(1, round(ep*self.k)), joint='curve')

    def rect(self, box, couleur='ion', alpha=255, rayon=0, contour=False, ep=1.5):
        col = self.m.c[couleur] if isinstance(couleur, str) else couleur
        kw = {'outline' if contour else 'fill': (*col[:3], round(alpha))}
        self.d.rounded_rectangle(self.box(box), radius=round(rayon*self.k),
                                width=max(1, round(ep*self.k)), **kw)

    def cercle(self, x, y, r, couleur='ion', alpha=255, contour=False, ep=1.5):
        col = self.m.c[couleur] if isinstance(couleur, str) else couleur
        kw = {'outline' if contour else 'fill': (*col[:3], round(alpha))}
        self.d.ellipse(self.box((x-r, y-r, x+r, y+r)),
                       width=max(1, round(ep*self.k)), **kw)

    def tronque(self, texte, largeur, taille, mono=False):
        if self.largeur(texte, taille, mono) <= largeur:
            return texte
        while texte and self.largeur(texte + '…', taille, mono) > largeur:
            texte = texte[:-1]
        return texte.rstrip() + '…'

    def riche(self, x, y, texte, taille, largeur, interligne=1.35,
              alpha=255, mots_visibles=None, mono=False, couleur='os'):
        """Retour voulu, retour automatique et une seule emphase orange."""
        xx, yy, compte, accent = x, y, 0, False
        actif = False
        base = -self.font(taille,mono).getbbox('H',anchor='ls')[1]/self.k
        for token in re.findall(r'\*|\||[^\s*|]+|[ \t]+', texte):
            if token == '*':
                actif = not actif
                continue
            if token == '|':
                xx, yy = x, yy + taille*interligne
                continue
            espace = token.isspace()
            longueur = self.largeur(token, taille, mono)
            if xx + longueur > x + largeur and not espace and xx > x:
                xx, yy = x, yy + taille*interligne
            if espace and xx == x:
                continue
            if not espace:
                compte += 1
            if mots_visibles is None or compte <= mots_visibles:
                self.texte(xx, yy+base, token, taille,
                           'signal' if actif and not accent else couleur, mono, alpha,ancre='ls')
            if actif and not espace:
                accent = True
            xx += longueur
        self.curseur = (xx, yy)
        return yy + taille*interligne


class Incrustations:
    def __init__(self, marque: dict, W: int, H: int, enveloppes: dict | None = None):
        if W <= 0 or H <= 0:
            raise ValueError('Les dimensions doivent être positives.')
        self.marque, self.W, self.H = marque, int(W), int(H)
        self.s = min(W, H) / 1080
        self.portrait = H > W
        self.marges = (W * (.08 if self.portrait else .06),
                       H * (.105 if self.portrait else .06))
        defauts = dict(encre=[8,8,10], os=[246,244,238], brume=[160,160,172],
                       signal=[255,90,31], ion=[90,170,255])
        self.c = {k: tuple(marque.get('couleurs', {}).get(k, v)) for k,v in defauts.items()}
        p = marque.get('polices', {})
        dossier = Path(p.get('dossier', '')).expanduser()
        self.fonts = [str(dossier / p.get('titre', 'geist-latin-wght-normal.woff2')),
                      str(dossier / p.get('mono', 'jetbrains-mono-latin-wght-normal.woff2'))]
        self.enveloppes = enveloppes or {}
        self._logo = None
        if marque.get('logo'):
            with Image.open(Path(marque['logo']).expanduser()) as logo:
                self._logo = logo.convert('RGBA')

    def font(self, taille, mono=False, gras=600):
        return police(self.fonts[bool(mono)], max(1, round(taille)), gras)

    @lru_cache(maxsize=32)
    def _verre(self, w, h, pad, k):
        taille = (w + 2*pad, h + 2*pad)
        # Flou réduit : doux à l'écran, indépendant du nombre de pixels du film.
        petit = Image.new('RGBA', (max(1, taille[0]//3), max(1, taille[1]//3)))
        d = ImageDraw.Draw(petit)
        d.rounded_rectangle(tuple(round(v/3) for v in (pad,pad,pad+w-1,pad+h-1)),
                            radius=max(1,round(14*k/3)), outline=(*self.c['ion'], 90), width=max(1, round(4*k/3)))
        petit = petit.filter(ImageFilter.GaussianBlur(max(1, 7*k/3)))
        fond = petit.resize(taille, Image.Resampling.BILINEAR)
        d = ImageDraw.Draw(fond)
        boite = (pad, pad, pad+w-1, pad+h-1)
        d.rounded_rectangle(boite, radius=14*k, fill=(*self.c['encre'], 166),
                            outline=(*self.c['ion'], 204), width=max(1, round(1.5*k)))
        balayage = Image.new('RGBA', taille)
        bd = ImageDraw.Draw(balayage)
        for y in range(pad+2, pad+h-2, max(2, round(4*k))):
            bd.line((pad+2, y, pad+w-3, y), fill=(*self.c['ion'], 13))
        masque = Image.new('L', taille)
        ImageDraw.Draw(masque).rounded_rectangle(boite, radius=14*k, fill=255)
        balayage.putalpha(Image.composite(balayage.getchannel('A'), Image.new('L', taille), masque))
        return Image.alpha_composite(fond, balayage)

    def _emplacement(self, surface):
        pos = surface.position
        mx, my = self.marges
        x, y = (self.W-surface.w)/2, (self.H-surface.hh)/2
        if 'gauche' in pos:
            x = mx
        elif 'droite' in pos:
            x = self.W-mx-surface.w
        if 'haut' in pos:
            y = my
        elif 'bas' in pos:
            y = self.H-my-surface.hh
        return round(x)-surface.pad, round(y)-surface.pad

    def _coller(self, im, calque, x, y):
        """Composition RGBA du rectangle utile, avec découpe sûre aux bords."""
        x, y = round(x), round(y)
        x0, y0 = max(0,x), max(0,y)
        x1, y1 = min(self.W,x+calque.width), min(self.H,y+calque.height)
        resultat = im.copy()
        if x1 > x0 and y1 > y0:
            morceau = calque.crop((x0-x,y0-y,x1-x,y1-y))
            fond = im.crop((x0,y0,x1,y1)).convert('RGBA')
            resultat.paste(Image.alpha_composite(fond,morceau).convert('RGB'), (x0,y0))
        return resultat

    def _finir(self, im, a, spec, u):
        entree = progression(u, 0, .44)
        contenu = progression(u, .17, .50)
        sortie_alpha = progression(self._duree(spec)-u, 0, .22)
        if a.verre:
            base = self._verre(a.w,a.hh,a.pad,a.k).copy()
            # Un reflet unique traverse à l'entrée, découpé aux coins du verre.
            if .08 < u < .64:
                reflet = Image.new('RGBA', base.size)
                rd = ImageDraw.Draw(reflet)
                centre = -100 + (a.w+200)*progression(u,.08,.64)
                rd.polygon([(centre-60,a.pad),(centre,a.pad),
                            (centre+90,a.pad+a.hh),(centre+30,a.pad+a.hh)],
                           fill=(*self.c['os'],17))
                masque = Image.new('L',base.size)
                ImageDraw.Draw(masque).rounded_rectangle(
                    (a.pad,a.pad,a.pad+a.w-1,a.pad+a.hh-1),14*a.k,fill=255)
                reflet.putalpha(Image.composite(reflet.getchannel('A'),Image.new('L',base.size),masque))
                base = Image.alpha_composite(base,reflet)
            a.im.putalpha(a.im.getchannel('A').point(lambda v: round(v*contenu)))
            base = Image.alpha_composite(base,a.im)
            hauteur = round((a.hh+2*a.pad)*entree)
            milieu = base.height//2
            masque = Image.new('L',base.size)
            if hauteur:
                ImageDraw.Draw(masque).rectangle((0,milieu-hauteur//2,base.width,
                                                  milieu+(hauteur+1)//2),fill=255)
            base.putalpha(Image.composite(base.getchannel('A'),Image.new('L',base.size),masque))
        else:
            base = a.im
            base.putalpha(base.getchannel('A').point(lambda v: round(v*entree)))
        if sortie_alpha < 1:
            base.putalpha(base.getchannel('A').point(lambda v: round(v*sortie_alpha)))
        x,y = self._emplacement(a)
        return self._coller(im,base,x,y+round((1-sortie_alpha)*14*a.k))

    @staticmethod
    def _duree(spec):
        return max(1/24, float(spec['duree_f'])/24)

    def poser(self, im: Image.Image, spec: dict, u: float) -> Image.Image:
        if im.mode != 'RGB' or im.size != (self.W,self.H):
            raise ValueError('im doit être RGB, aux dimensions du moteur.')
        if spec.get('type') not in TYPES:
            raise ValueError(f"Type inconnu : {spec.get('type')}")
        if not math.isfinite(u) or u < 0:
            raise ValueError('u doit être un temps positif fini.')
        if u >= self._duree(spec):
            return im.copy()
        return getattr(self, '_'+spec['type'])(im,spec,u)

    def _statut(self, im, spec, u):
        texte = spec.get('texte','')
        a = Surface(self,spec,(min(900,max(400,100+len(texte)*16)),112),'bas-gauche')
        a.cercle(37,56,5+1.5*math.sin(u*5),'ion' if '*' in texte else 'signal')
        # Les marqueurs ne consomment pas de temps de frappe.
        restant = max(0,int((u-.22)*28))
        morceaux = []
        for caractere in texte:
            if caractere != '*':
                if restant <= 0:
                    break
                restant -= 1
            morceaux.append(caractere)
        visible = ''.join(morceaux)
        a.riche(62,39,visible,23,a.l-96,mono=True)
        if int(u*2.5)%2 == 0:
            x,y = a.curseur
            a.rect((min(x+3,a.l-49),y,min(x+3,a.l-49)+12,y+25),'os',190)
        return self._finir(im,a,spec,u)

    def _document(self, im, spec, u):
        lignes = spec.get('lignes',[])
        a = Surface(self,spec,(590,max(660,360+len(lignes)*61)),'droite')
        a.texte(38,35,'OPSYS / DOCUMENT',14,'brume',True)
        a.riche(38,75,spec.get('titre','DOCUMENT'),32,514)
        fin = a.riche(38,129,spec.get('destinataire',''),19,514,couleur='brume')
        # Le destinataire garde sa teinte secondaire, même sur plusieurs lignes.
        debut = max(210,fin+30)
        a.ligne([(38,debut-22),(552,debut-22)],alpha=80)
        for i,(libelle,valeur) in enumerate(lignes):
            t = progression(u,.34+i*.12,.56+i*.12)
            y = debut+i*61
            a.texte(38,y,a.tronque(libelle,320,21),21,alpha=255*t)
            a.texte(552,y,a.tronque(valeur,170,19,True),19,mono=True,alpha=255*t,ancre='rt')
            a.ligne([(38,y+40),(38+514*t,y+40)],alpha=55,ep=1)
        ytotal = debut+len(lignes)*61+23
        a.texte(38,ytotal,'TOTAL',14,'brume',True)
        t = sortie((u-.45)/max(.3,min(1.35,self._duree(spec)*.45)))
        a.texte(552,ytotal-5,compteur_texte(spec.get('total',''),t),35,mono=True,ancre='rt')
        tampon = spec.get('tampon')
        debut_tampon = min(.57+max(.3,min(1.35,self._duree(spec)*.45)),
                           self._duree(spec)*.65)
        t = progression(u,debut_tampon,debut_tampon+.22)
        if tampon and t:
            largeur = min(245,80+a.largeur(tampon,29,True))
            stamp = Image.new('RGBA',(round(largeur*a.k),round(68*a.k)))
            sd = ImageDraw.Draw(stamp)
            sd.rounded_rectangle((2,2,stamp.width-3,stamp.height-3),radius=4*a.k,
                                 outline=(*self.c['signal'],round(255*t)),width=max(1,round(2*a.k)))
            sd.text((stamp.width/2,stamp.height/2),tampon,font=a.font(29,True),
                    anchor='mm',fill=(*self.c['signal'],round(255*t)))
            facteur = 1+.3*(1-t)-.035*math.sin(math.pi*t)
            stamp = stamp.resize((round(stamp.width*facteur),round(stamp.height*facteur)),Image.Resampling.BICUBIC)
            stamp = stamp.rotate(8,resample=Image.Resampling.BICUBIC,expand=True)
            # Pillow : +8° visuel correspond à une inclinaison de texte de −8°.
            a.im.alpha_composite(stamp,(round(a.pad+38*a.k),round(a.pad+(a.h-116)*a.k)))
        return self._finir(im,a,spec,u)

    def _halo(self, a, x, y, rx, ry, alpha=60):
        petit = Image.new('RGBA',(max(1,a.im.width//4),max(1,a.im.height//4)))
        d = ImageDraw.Draw(petit)
        p = a.box((x-rx,y-ry,x+rx,y+ry))
        d.ellipse(tuple(v/4 for v in p),fill=(*self.c['ion'],alpha))
        petit = petit.filter(ImageFilter.GaussianBlur(max(1,26*a.k/4)))
        a.im.alpha_composite(petit.resize(a.im.size,Image.Resampling.BILINEAR))

    def _compteur(self, im, spec, u):
        a = Surface(self,spec,(870 if self.portrait else 1260,460),'centre',False)
        t = sortie(u/(self._duree(spec)*.7))
        valeur = spec.get('de',0)+(spec.get('a',0)-spec.get('de',0))*t
        texte = str(spec.get('prefixe',''))+nombre(valeur,int(spec.get('decimales',0)))
        suffixe = str(spec.get('suffixe',''))
        taille = 238
        total = a.largeur(texte,taille)+a.largeur(suffixe,76)+22
        taille *= min(1,(a.l-80)/max(1,total))
        largeur = a.largeur(texte,taille)+a.largeur(suffixe,taille*.32)+22
        x = (a.l-largeur)/2
        self._halo(a,a.l/2,260,270,85,85)
        etiquette = spec.get('etiquette','').upper()
        ew = min(a.l-110,a.largeur(etiquette,20,True))
        a.cercle((a.l-ew)/2-23,67,5,'ion' if '*' in etiquette else 'signal')
        a.texte((a.l-ew)/2,54,a.tronque(etiquette,a.l-110,20,True),20,'brume',True)
        a.texte(x,135,texte,taille)
        a.texte(x+a.largeur(texte,taille)+22,135+taille*.65,suffixe,taille*.32)
        return self._finir(im,a,spec,u)

    def _courbe(self, im, spec, u):
        a = Surface(self,spec,(870 if self.portrait else 1300,530),'centre')
        a.texte(40,33,a.tronque(spec.get('etiquette',''),a.l-80,20,True),20,'brume',True)
        gauche,droite,haut,bas = 65,a.l-145,130,440
        for i in range(5):
            y = haut+(bas-haut)*i/4
            a.ligne([(gauche,y),(droite+25,y)],alpha=32,ep=1)
        a.ligne([(gauche,haut),(gauche,bas),(droite+25,bas)],alpha=95,ep=1)
        valeurs = list(spec.get('points',[]))
        if not valeurs:
            return self._finir(im,a,spec,u)
        if len(valeurs)==1:
            valeurs = valeurs*2
        vmin,vmax = min(valeurs),max(valeurs)
        ecart = max(1,vmax-vmin)
        points = [(gauche+i*(droite-gauche)/(len(valeurs)-1),
                   bas-20-(v-vmin)/ecart*(bas-haut-50)) for i,v in enumerate(valeurs)]
        t = sortie((u-.25)/max(.5,self._duree(spec)*.58))
        limite = t*(len(points)-1)
        trace = points[:int(limite)+1]
        if limite < len(points)-1:
            f = limite-int(limite)
            p,q = points[int(limite):int(limite)+2]
            trace.append((p[0]+(q[0]-p[0])*f,p[1]+(q[1]-p[1])*f))
        # Remplissage sous la courbe, découpé par un polygone et un dégradé alpha.
        if len(trace)>1:
            taille = a.im.size
            mask = Image.new('L',taille)
            ImageDraw.Draw(mask).polygon([a.xy(gauche,bas)]+[a.xy(*p) for p in trace]+[a.xy(trace[-1][0],bas)],fill=255)
            yy = np.arange(taille[1],dtype=np.float32)
            alpha = np.clip((a.xy(0,bas)[1]-yy)/max(1,(bas-haut)*a.k)*65,0,65).astype('uint8')
            grad = Image.fromarray(np.broadcast_to(alpha[:,None],(taille[1],taille[0])).copy())
            from PIL import ImageChops
            fill = Image.new('RGBA',taille,(*self.c['ion'],0))
            fill.putalpha(ImageChops.multiply(mask,grad))
            a.im.alpha_composite(fill)
        proj = int(spec.get('pointille_depuis',len(points)))
        for i in range(len(trace)-1):
            p,q = trace[i:i+2]
            if i >= proj:
                longueur = math.dist(p,q)
                for distance in np.arange(0,longueur,19):
                    f0,f1 = distance/max(1,longueur),min(1,(distance+10)/max(1,longueur))
                    a.ligne([(p[0]+(q[0]-p[0])*f0,p[1]+(q[1]-p[1])*f0),
                             (p[0]+(q[0]-p[0])*f1,p[1]+(q[1]-p[1])*f1)],'signal',ep=3)
            else:
                a.ligne([p,q],'ion',35,12)
                a.ligne([p,q],'ion',255,3)
        x,y = trace[-1]
        col = 'signal' if limite>proj else 'ion'
        a.cercle(x,y,10+2*math.sin(u*5),col,45)
        a.cercle(x,y,4,col)
        a.texte(min(x+18,a.l-120),y-18,spec.get('valeur',''),24,mono=True)
        return self._finir(im,a,spec,u)

    def _cedule(self, im, spec, u):
        semaines = int(borne(int(spec.get('semaines',1)),1,4))
        jours = list(spec.get('jours',['Lun','Mar','Mer','Jeu','Ven'])) or ['Jour']
        hauteur = 130+semaines*225 if self.portrait else 475
        a = Surface(self,spec,(870 if self.portrait else 1660,hauteur),'centre')
        a.texte(36,30,a.tronque(spec.get('titre','CÉDULE'),a.l-72,25),25)
        gap = 26
        sw = a.l-72 if self.portrait else (a.l-72-gap*(semaines-1))/semaines
        sh = 225 if self.portrait else 345
        grille = progression(u,.18,.65)
        for s in range(semaines):
            x = 36 if self.portrait else 36+s*(sw+gap)
            y = 100+s*sh if self.portrait else 100
            a.texte(x,y,f'SEM. {s+1}',16,'brume',True)
            cw = sw/len(jours)
            for j,jour in enumerate(jours):
                a.texte(x+(j+.5)*cw,y+35,a.tronque(jour,cw-6,14,True),14,'brume',True,ancre='mt')
            gh = sh-83
            for j in range(len(jours)+1):
                xx = x+j*cw
                a.ligne([(xx,y+63),(xx,y+63+gh*grille)],alpha=45,ep=1)
            for r in range(5):
                yy = y+63+r*gh/4
                a.ligne([(x,yy),(x+sw*grille,yy)],alpha=45,ep=1)
        taille_bloc = 18 if self.portrait else 16
        for i,(s,j0,j1,r,texte) in enumerate(spec.get('blocs',[])):
            if not (0<=s<semaines and 0<=r<4 and 0<=j0<=j1<len(jours)):
                continue
            t = progression(u,.55+i*.08,.88+i*.08)
            if t == 0:
                continue
            x = 36 if self.portrait else 36+s*(sw+gap)
            y = 100+s*sh if self.portrait else 100
            cw, rh = sw/len(jours),(sh-83)/4
            xx,yy = x+j0*cw+4+(1-t)*18,y+63+r*rh+4
            ww,hh = (j1-j0+1)*cw-8,rh-8
            col = 'signal' if i==0 else 'ion'
            a.rect((xx,yy,xx+ww,yy+hh),col,round(40*t),5)
            a.rect((xx,yy,xx+ww,yy+hh),col,round(180*t),5,True,1)
            a.rect((xx+1,yy+5,xx+3,yy+hh-5),col,round(255*t),1)
            a.texte(xx+10,yy+hh/2,a.tronque(texte,ww-20,taille_bloc),taille_bloc,alpha=255*t,ancre='lm')
        return self._finir(im,a,spec,u)

    def _pointage(self, im, spec, u):
        a = Surface(self,spec,(870,640),'centre',False)
        self._halo(a,435,220,285,70,65)
        heure = spec.get('heure','00:00')
        compte = max(0,int((u-.16)*9))
        visible = heure[:compte]
        x_heure = (a.l-a.largeur(heure,190,True))/2
        a.texte(x_heure,90,visible,190,mono=True)
        t = progression(u,.75,1.25)
        if t:
            a.d.arc(a.box((390,325,480,415)),start=-90,end=-90+359.9*t,
                    fill=(*self.c['ion'],240),width=max(1,round(3*a.k)))
        coche = progression(u,1.12,1.38)
        if coche:
            pts = [(415,369),(430,384),(457,354)]
            a.ligne(pts[:2] if coche<.4 else pts,alpha=255*coche,ep=3)
        identite = progression(u,1.2,1.52)
        a.texte(435,456,a.tronque(spec.get('nom',''),790,32),32,alpha=255*identite,ancre='mt')
        a.texte(435,516,spec.get('etat','ARRIVÉE'),18,'brume',True,alpha=255*identite,ancre='mt')
        return self._finir(im,a,spec,u)

    def _appel(self, im, spec, u):
        a = Surface(self,spec,(650,345),'haut-droite')
        a.cercle(78,81,35,'ion',30)
        a.cercle(78,81,35,'ion',155,True)
        nom = spec.get('nom','')
        a.texte(78,81,nom[:1].upper(),29,ancre='mm')
        a.texte(134,43,a.tronque(nom,400,30),30)
        a.texte(134,92,a.tronque(spec.get('sous_titre','Appel entrant'),360,18),18,'brume')
        secondes = int(u)
        a.cercle(45,161,4,'signal',round(175+60*math.sin(u*3)**2))
        a.texte(61,147,f'{secondes//60:02}:{secondes%60:02}',20,mono=True)
        env = self.enveloppes.get(spec.get('voix'))
        if env is not None and len(env):
            amplitude = float(borne(float(env[min(len(env)-1,int(u*FPS))])))
        else:
            amplitude = .35+.25*math.sin(u*2.7)**2+.15*math.sin(u*5.1)**2
        for i in range(40):
            x = 45+i*(a.l-90)/39
            fenetre = math.sin(math.pi*(i+.5)/40)**.65
            modulation = .35+.65*math.sin(i*1.7+u*9)**2
            h = 3+45*amplitude*fenetre*modulation
            a.rect((x-2,252-h,x+2,252+h),'ion',round(110+130*fenetre),2)
        return self._finir(im,a,spec,u)

    @lru_cache(maxsize=32)
    def _spline(self, points):
        """Catmull-Rom échantillonnée, puis paramétrée par longueur réelle."""
        p = np.array(points,dtype=np.float64)*[self.W,self.H]
        if len(p)<2:
            return p,np.zeros(len(p))
        ext = np.vstack((p[0],p,p[-1]))
        bouts = []
        for i in range(len(p)-1):
            p0,p1,p2,p3 = ext[i:i+4]
            t = np.linspace(0,1,80,endpoint=False)[:,None]
            bouts.append(.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t))
        courbe = np.vstack((*bouts,p[-1:]))
        longueurs = np.r_[0,np.cumsum(np.linalg.norm(np.diff(courbe,axis=0),axis=1))]
        return courbe,longueurs

    def _trajet(self, im, spec, u):
        points = tuple(tuple(p) for p in spec.get('points',[]))
        if len(points)<2:
            return im.copy()
        courbe,dist = self._spline(points)
        total = dist[-1]
        temps_trace = self._duree(spec)*.6
        trace = doux(u/max(.001,temps_trace))*total
        # Calque limité à la boîte du trajet (pas de flou pleine résolution).
        marge = round(26*self.s)
        x0,y0 = np.floor(courbe.min(axis=0)).astype(int)-marge
        x1,y1 = np.ceil(courbe.max(axis=0)).astype(int)+marge
        x0,y0,x1,y1 = max(0,x0),max(0,y0),min(self.W,x1),min(self.H,y1)
        if x1<=x0 or y1<=y0:
            return im.copy()
        calque = Image.new('RGBA',(x1-x0,y1-y0))
        d = ImageDraw.Draw(calque)
        col = self.c['signal' if spec.get('couleur')=='signal' else 'ion']
        n = int(np.searchsorted(dist,trace,side='right'))
        visible = [tuple(p-[x0,y0]) for p in courbe[:n]]
        if n<len(dist) and n>0:
            f = (trace-dist[n-1])/max(.001,dist[n]-dist[n-1])
            visible.append(tuple(courbe[n-1]+f*(courbe[n]-courbe[n-1])-[x0,y0]))
        if len(visible)>1:
            # Trois largeurs translucides forment la lueur sans coût de flou.
            for ep,alpha in ((22,14),(12,30),(6,65),(3,255)):
                d.line(visible,fill=(*col,alpha),width=max(1,round(ep*self.s)),joint='curve')
        tete = trace
        if u>=temps_trace and total:
            tete = ((u-temps_trace)/max(.65,self._duree(spec)*.22)%1)*total
            for j in range(18,0,-1):
                distance = max(0,tete-j*total*.0025)
                x = np.interp(distance,dist,courbe[:,0])-x0
                y = np.interp(distance,dist,courbe[:,1])-y0
                r = (2+3*(1-j/19))*self.s
                d.ellipse((x-r,y-r,x+r,y+r),fill=(*col,round(235*(1-j/20))))
            x = np.interp(tete,dist,courbe[:,0])-x0
            y = np.interp(tete,dist,courbe[:,1])-y0
            r = 4*self.s
            d.ellipse((x-r,y-r,x+r,y+r),fill=(*self.c['os'],255))
        for p in points:
            v = np.array(p)*[self.W,self.H]
            distance = dist[np.argmin(np.sum((courbe-v)**2,axis=1))]
            allume = distance<=trace and (u<temps_trace or abs(distance-tete)<total*.055)
            x,y = v-[x0,y0]
            r = (5 if allume else 3)*self.s
            d.ellipse((x-r,y-r,x+r,y+r),fill=(*col,255 if allume else 70))
        alpha = progression(self._duree(spec)-u,0,.22)
        if alpha<1:
            calque.putalpha(calque.getchannel('A').point(lambda v: round(v*alpha)))
        return self._coller(im,calque,x0,y0)

    def _flash(self, im, spec, u):
        t = u*FPS
        enveloppe = t if t<1 else max(0,1-(t-1)/3)
        intensite = borne(float(spec.get('intensite',1)))*enveloppe
        calque = Image.new('RGBA',im.size,(255,246,230,round(255*intensite)))
        return Image.alpha_composite(im.convert('RGBA'),calque).convert('RGB')

    def _glitch(self, im, spec, u):
        intensite = borne(float(spec.get('intensite',.5)))
        if intensite==0:
            return im.copy()
        rng = np.random.default_rng(9173+int(u*FPS))
        r,g,b = im.split()
        from PIL import ImageChops, ImageOps
        decalage = round(self.W*.022*intensite)
        r = ImageChops.offset(r,decalage,0)
        b = ImageChops.offset(b,-decalage,0)
        resultat = Image.merge('RGB',(r,g,b))
        for _ in range(int(rng.integers(3,7))):
            y = int(rng.integers(0,self.H-1))
            h = int(rng.integers(max(1,self.H//80),max(2,self.H//15)))
            bande = resultat.crop((0,y,self.W,min(self.H,y+h)))
            bande = ImageChops.offset(bande,int(rng.uniform(-1,1)*self.W*.035*intensite),0)
            resultat.paste(bande,(0,y))
        poster = ImageOps.posterize(resultat,6)
        return Image.blend(resultat,poster,intensite*.35)

    @lru_cache(maxsize=16)
    def _nom_logo(self, largeur, taille):
        if self._logo is not None:
            logo = self._logo.copy()
            logo.thumbnail((largeur,round(taille*1.6)),Image.Resampling.LANCZOS)
            return logo
        texte = self.marque.get('nom','OPSYS-AI')
        f = self.font(taille,gras=850)
        suivi = -taille*.045
        w = max(1,math.ceil(sum(f.getlength(c) for c in texte)+suivi*(len(texte)-1)))
        logo = Image.new('RGBA',(w,max(1,round(taille*1.3))))
        d = ImageDraw.Draw(logo)
        x=0
        base=taille*.12-f.getbbox(texte,anchor='ls')[1]
        for c in texte:
            d.text((x,base),c,font=f,fill=(*self.c['os'],255),anchor='ls')
            x += f.getlength(c)+suivi
        if logo.width>largeur:
            logo = logo.resize((largeur,round(logo.height*largeur/logo.width)),Image.Resampling.LANCZOS)
        return logo

    def _carton(self, im, spec, u):
        # Le fond de marque remplace explicitement le plan photographique.
        fond = Image.new('RGB',im.size,self.c['encre'])
        a = Surface(self,spec,(870 if self.portrait else 1500,1100 if self.portrait else 780),'centre',False)
        t = progression(u,0,.8)
        taille = 130 if self.portrait else 155
        logo = self._nom_logo(round((a.l-85)*a.k),round(taille*a.k))
        facteur = 1+.06*(1-t)
        if facteur>1.001:
            logo = logo.resize((round(logo.width*facteur),round(logo.height*facteur)),Image.Resampling.BICUBIC)
        if t<.995:
            logo = logo.filter(ImageFilter.GaussianBlur((1-t)*6*a.k))
        logo = logo.copy()
        logo.putalpha(logo.getchannel('A').point(lambda v: round(v*t)))
        ly = 250 if self.portrait else 130
        a.im.alpha_composite(logo,(round((a.im.width-logo.width)/2),round(a.pad+ly*a.k)))
        y = ly+taille*1.3+24
        signature = self.marque.get('signature','')
        mots = max(0,int((u-.65)*6))
        # Un seul accent orange : le trait passe à l'ion dès le mot orange révélé.
        avant = signature.split('*')[0]
        accent_visible = '*' in signature and mots>len(avant.split())
        a.rect((a.l/2-30,y,a.l/2+30,y+4),'ion' if accent_visible else 'signal',255,2)
        a.texte(a.l/2,y+36,self.marque.get('editeur',''),23,'brume',ancre='mt')
        sy = y+150 if self.portrait else y+120
        # Deux lignes éditoriales équilibrées dans chacun des formats.
        sig = signature.replace('. À ','.|À ') if '|' not in signature else signature
        lignes = sig.split('|')
        index = 0
        for ligne in lignes:
            net = ligne.replace('*','')
            fs = 42 if self.portrait else 48
            fs *= min(1,(a.l-100)/max(1,a.largeur(net,fs)))
            largeur = a.largeur(net,fs)
            a.riche((a.l-largeur)/2,sy,ligne,fs,largeur+2,mots_visibles=max(0,mots-index))
            index += len(net.split())
            sy += fs*1.6
        # Mentions ancrées au bas sûr du cadre, indépendamment du bloc central.
        mentions = self.marque.get('mentions','')
        largeur = self.W-2*self.marges[0]
        f = self.font(13*self.s,True)
        mots_mentions = mentions.split()
        lignes_mentions,ligne = [],''
        for mot in mots_mentions:
            candidat = (ligne+' '+mot).strip()
            if f.getlength(candidat)>largeur and ligne:
                lignes_mentions.append(ligne)
                ligne=mot
            else:
                ligne=candidat
        lignes_mentions.append(ligne)
        resultat = self._finir(fond,a,spec,u)
        legende = Image.new('RGBA',(self.W,round(24*self.s*len(lignes_mentions)+10)))
        d=ImageDraw.Draw(legende)
        alpha = round(255*t*progression(self._duree(spec)-u,0,.22))
        for i,ligne in enumerate(lignes_mentions):
            d.text((self.W/2,i*24*self.s),ligne,font=f,anchor='mt',fill=(*self.c['brume'],alpha))
        return self._coller(resultat,legende,0,self.H-self.marges[1]-legende.height)


TYPES = ('statut','document','compteur','courbe','cedule','pointage','appel',
         'trajet','flash','glitch','carton')
