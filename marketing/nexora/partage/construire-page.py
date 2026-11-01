"""Génère partage/index.html : la galerie du kit de lancement (page autonome, médias relatifs)."""
from pathlib import Path
ICI = Path(__file__).resolve().parent
LOGO = Path("/home/pc6/Desktop/NexoraSite/docs/marque/logos/nexora-ai-logo-sombre.svg").read_text()
def img(n, alt, cls=""): 
    return f'<figure class="{cls}"><img src="img/{n}.jpg" alt="{alt}" loading="lazy"></figure>'
def vid(n, titre, cls="", legende=""):
    return (f'<figure class="v {cls}"><video controls preload="none" playsinline poster="img/{n}.jpg"><source src="video/{n}.mp4" type="video/mp4"></video>'
            f'<figcaption><b>{titre}</b>{(" · " + legende) if legende else ""}</figcaption></figure>')
teasers = [("workstudio", "WorkStudio", "Des agents qui les assemblent."), ("code", "Code", "Marche après marche."), ("rag", "RAG", "Une réponse s’allume."),
           ("bot", "Bot", "Un compagnon qui éclaire."), ("creative", "Creative", "Elle devient film."), ("webpilot", "WebPilot", "Une lanterne trace la route."),
           ("privacy-router", "Privacy Router", "Vos données, à l’abri."), ("vps", "VPS au Québec", "Ici, au Québec.")]
html = f"""<title>Kit de lancement Nexora</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600&family=Inter:wght@400;500&family=JetBrains+Mono:wght@500&display=swap">
<style>
/* Mise en page : une galerie sombre à rails de filets comme le site Nexora ; le film occupe le haut de page, chaque famille suit dans l'ordre où on la montrerait à un client. */
:root {{
  --encre: #0A0A0E; --surface: #121218; --filet: #2B2B38; --os: #F5F4EF; --brume: #A8A8B6; --signal: #FF5A1F; --accent: #FF7A45;
  --titre: "Geist", "Inter", system-ui, sans-serif; --texte: "Inter", system-ui, sans-serif; --mono: "JetBrains Mono", ui-monospace, monospace;
  color-scheme: dark;
}}
* {{ box-sizing: border-box; }}
body {{ margin: 0; background: var(--encre); color: var(--os); font: 400 16px/1.6 var(--texte);
  padding-block: 0 80px; padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); }}
.cadre {{ max-width: 1180px; margin: 0 auto; }}
header {{ padding-block: 28px 8px; display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 16px; }}
header svg {{ height: 30px; width: auto; display: block; }}
nav {{ display: flex; flex-wrap: wrap; gap: 6px; font: 500 12px/1 var(--mono); letter-spacing: .06em; text-transform: uppercase; }}
nav a {{ color: var(--brume); text-decoration: none; padding: 9px 12px; border: 1px solid var(--filet); border-radius: 6px; }}
nav a:hover, nav a:focus-visible {{ color: var(--encre); background: var(--signal); border-color: var(--signal); outline: none; }}
h1 {{ font: 500 clamp(38px, 7vw, 84px)/1.0 var(--titre); letter-spacing: -.03em; margin: 56px 0 12px; text-wrap: balance; }}
h1 em {{ font-style: normal; color: var(--accent); }}
.chapeau {{ max-width: 46rem; color: var(--brume); font-size: 18px; margin: 0 0 8px; }}
section {{ border-top: 1px solid var(--filet); margin-top: 72px; padding-top: 28px; scroll-margin-top: 16px; }}
h2 {{ font: 500 clamp(26px, 4vw, 40px)/1.1 var(--titre); letter-spacing: -.024em; margin: 0 0 6px; text-wrap: balance; }}
.sur {{ font: 500 12px/1 var(--mono); letter-spacing: .06em; text-transform: uppercase; color: var(--accent); margin-bottom: 14px; display: block; }}
.note {{ color: var(--brume); max-width: 46rem; margin: 0 0 22px; }}
figure {{ margin: 0; }}
img, video {{ display: block; width: 100%; height: auto; border-radius: 6px; background: var(--surface); }}
.v figcaption {{ font-size: 13px; color: var(--brume); padding-top: 8px; }}
.v figcaption b {{ color: var(--os); font-weight: 500; }}
.grille {{ display: grid; gap: 14px; grid-template-columns: repeat(auto-fill, minmax(min(100%, 260px), 1fr)); }}
.grille.large {{ grid-template-columns: repeat(auto-fill, minmax(min(100%, 380px), 1fr)); }}
.grille.etroit {{ grid-template-columns: repeat(auto-fill, minmax(min(100%, 150px), 1fr)); }}
.film {{ display: grid; gap: 14px; grid-template-columns: minmax(0, 2.4fr) minmax(0, 1fr); align-items: start; }}
@media (max-width: 760px) {{ .film {{ grid-template-columns: minmax(0, 1fr); }} .film .v.vert {{ max-width: 280px; }} }}
.sel {{ display: inline-flex; gap: 0; border: 1px solid var(--filet); border-radius: 6px; margin-bottom: 12px; overflow: hidden; }}
.sel button {{ font: 500 12px/1 var(--mono); letter-spacing: .06em; text-transform: uppercase; background: transparent; color: var(--brume); border: 0; padding: 10px 14px; cursor: pointer; }}
.sel button[aria-pressed="true"] {{ background: var(--signal); color: var(--encre); }}
.sel button:focus-visible {{ outline: 2px solid var(--os); outline-offset: -2px; }}
.planche img {{ border: 1px solid var(--filet); }}
footer {{ margin-top: 80px; padding-top: 24px; border-top: 1px solid var(--filet); color: var(--brume); font-size: 14px; max-width: 46rem; }}
code {{ font: 500 13px var(--mono); color: var(--os); background: var(--surface); padding: 2px 6px; border-radius: 4px; word-break: break-all; }}
</style>
<div class="cadre">
<header>{LOGO}<nav aria-label="Sections"><a href="#film">Film</a><a href="#spots">Spots</a><a href="#teasers">Teasers</a><a href="#identite">Identité</a><a href="#social">Social</a><a href="#objets">Objets</a></nav></header>

<h1>Rêvez grand.<br><em>Gardez le contrôle.</em></h1>
<p class="chapeau">Le lancement de Nexora AI, produit avec Nexora Creative : image par Qwen-Image-2.1, plans vidéo par MiniMax H3, musique par MiniMax-Music3. Tout le texte et tous les logos sont posés en code, jamais dessinés par l’IA.</p>

<section id="film">
<span class="sur">Le film · 60 s</span>
<h2>Tout commence par une lumière.</h2>
<p class="note">Du premier cube de lumière jusqu’au logo : une nuit québécoise, un atelier, une aurore, un pont de carrés sur le fleuve, une main qui garde la lumière. Les images sont de petits aperçus ; les fichiers 1080p sont sur le poste.</p>
<div class="sel" role="group" aria-label="Langue du film"><button id="b-fr" aria-pressed="true">Français</button><button id="b-en" aria-pressed="false">English</button></div>
<div class="film">
  <figure class="v"><video id="film-h" controls preload="none" playsinline poster="img/film-marque-16x9-fr.jpg"><source src="video/film-marque-16x9-fr.mp4" type="video/mp4"></video><figcaption><b>Film de marque</b> · 16:9 · aussi en 9:16 et 1:1</figcaption></figure>
  {vid("film-marque-9x16-fr", "Version verticale", "vert", "9:16, réseaux sociaux")}
</div>
</section>

<section id="spots">
<span class="sur">Spots courts</span>
<h2>30 s, 15 s, 6 s, et la signature.</h2>
<p class="note">Chaque spot a sa propre musique et existe en 16:9, 9:16 et 1:1, en français et en anglais.</p>
<div class="grille large">
{vid("spot-30s-16x9-fr", "Spot 30 s", "", "16:9")}
{vid("spot-15s-9x16-fr", "Spot 15 s", "", "9:16")}
{vid("spot-6s-1x1-fr", "Bumper 6 s", "", "1:1")}
{vid("sting-nexora-16x9", "Signature animée", "", "4,6 s, avec son")}
</div>
</section>

<section id="teasers">
<span class="sur">Huit outils, huit rêves</span>
<h2>Un teaser de 15 s par outil.</h2>
<p class="note">L’état affiché sur chaque carte de fin est celui du site : aucun outil n’annonce plus que ce qui est prêt.</p>
<div class="grille etroit">
{''.join(vid("teaser-"+k+"-fr-9x16", n, "", t) for k, n, t in teasers)}
</div>
</section>

<section id="identite">
<span class="sur">Identité et imprimés</span>
<h2>Cartes, affiches, papeterie, salon.</h2>
<p class="note">Le logo officiel n’est jamais modifié. Les coordonnées sont encore des marqueurs à compléter : tout se régénère d’une commande.</p>
<div class="grille large">{img("carte-recto","Carte d’affaires, recto")}{img("carte-verso-fr","Carte d’affaires, verso clair")}{img("carte-verso-braise","Carte d’affaires, verso braise")}</div>
<div class="grille" style="margin-top:14px">{img("affiche-heros","Affiche : Rêvez grand. Gardez le contrôle.")}{img("affiche-quebec","Affiche : IA souveraine au Québec")}{img("affiche-famille","Affiche : la famille Nexora")}{img("affiche-typo","Affiche typographique : le N en mosaïque")}</div>
<div class="grille large" style="margin-top:14px">{img("guide-1","Kit de marque, couverture")}{img("guide-6","Kit de marque, page 6")}{img("guide-9","Kit de marque, page 9")}</div>
<div class="planche" style="margin-top:14px">{img("apercu-imprimes","Toutes les pièces imprimées")}</div>
</section>

<section id="social">
<span class="sur">Réseaux sociaux et publicité</span>
<h2>Facebook, Instagram, LinkedIn, X, YouTube, TikTok.</h2>
<p class="note">Couvertures, publications, carrousels, stories, bannières publicitaires, courriels et une page d’atterrissage : 185 pièces pour le social, 90 pour la publicité.</p>
<div class="grille large">{img("fb-aurore","Couverture Facebook, aurore")}{img("fb-nuit","Couverture Facebook, nuit")}{img("fb-mosaique","Couverture Facebook, mosaïque")}</div>
<div class="grille" style="margin-top:14px">{img("ig-1","Carrousel Instagram, 1 sur 7")}{img("ig-2","Carrousel Instagram, 2 sur 7")}{img("ig-3","Carrousel Instagram, 3 sur 7")}{img("site-390","Page d’atterrissage sur téléphone")}</div>
<div class="grille large" style="margin-top:14px">{img("site-1440","Page d’atterrissage sur ordinateur")}</div>
<div class="planche" style="margin-top:14px">{img("apercu-social","Toutes les pièces sociales")}{img("apercu-publicite","Toute la publicité")}</div>
</section>

<section id="objets">
<span class="sur">Objets promotionnels</span>
<h2>Ceux qu’on veut porter et garder.</h2>
<p class="note">24 objets avec fichier de fabrication à l’échelle réelle (calques, notes d’impression, Pantone approchés) et maquette réaliste. Les logos sont posés en code sur des photos vierges.</p>
<div class="grille">{img("obj-tshirt","T-shirt")}{img("obj-hoodie","Chandail à capuchon")}{img("obj-tasse","Tasse")}{img("obj-tote","Sac fourre-tout")}{img("obj-carnet","Carnet")}{img("obj-trousse","Trousse de bienvenue")}{img("obj-coffret","Coffret de lancement")}{img("obj-lampe","Lampe carré orange")}{img("obj-kiosque","Fond de kiosque")}</div>
<div class="planche" style="margin-top:14px">{img("apercu-objets","Les 24 objets")}</div>
</section>

<footer>
<p>Tout est dans <code>marketing/nexora/</code> sur pc6 : films en 1080p dans <code>video/final/</code>, teasers, stings et boucles dans <code>video/teasers/</code>, sources reproductibles dans chaque dossier.</p>
<p>Pour finir les imprimés, il manque un fichier : <code>coordonnees.json</code> (nom, titre, courriel, téléphone, adresse, domaine).</p>
</footer>
</div>
<script>
(function () {{
  var v = document.getElementById("film-h"), fr = document.getElementById("b-fr"), en = document.getElementById("b-en");
  function langue(l) {{
    var t = v.currentTime, p = !v.paused;
    v.poster = "img/film-marque-16x9-" + l + ".jpg";
    v.querySelector("source").src = "video/film-marque-16x9-" + l + ".mp4";
    v.load(); v.currentTime = t || 0; if (p) v.play();
    fr.setAttribute("aria-pressed", l === "fr"); en.setAttribute("aria-pressed", l === "en");
  }}
  fr.onclick = function () {{ langue("fr"); }}; en.onclick = function () {{ langue("en"); }};
}})();
</script>
"""
(ICI / "index.html").write_text(html)
print(len(html) // 1024, "Ko")
