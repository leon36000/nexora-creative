"""Photos de produits VIERGES (sans logo ni texte) generees avec Qwen-Image-2.1. Le logo se pose ensuite en code.
Usage : python3 prompts_photos.py [nom ...]   (2 rendus en parallele au plus ; saute les fichiers existants)"""
import sys, concurrent.futures as cf
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "outils"))
from generer import image

SORTIE = Path(__file__).resolve().parent / "generees"
FIN = ("Premium commercial product photography, photorealistic, sharp focus, soft diffused key light with a subtle rim light, "
       "fine natural texture, clean composition with generous empty margins around the object, completely blank unbranded product, "
       "no text, no letters, no logo, no label, no numbers, no brand marks.")
NOIR = "on a dark charcoal matte surface against a seamless near-black studio background"
CREME = "against a seamless warm cream studio background"

P = {
 "tee_dos": f"Top-down flat lay of the BACK of a plain black heavyweight cotton t-shirt, seen from behind: smooth high round neckband with no front neckline dip, short sleeves spread slightly outward, perfectly symmetrical and centered, laid flat {NOIR}. Large empty plain black back panel.",
 "tee_face": f"Top-down flat lay of the FRONT of a plain black heavyweight cotton t-shirt, round ribbed collar, short sleeves spread slightly outward, perfectly symmetrical and centered, laid flat {NOIR}. Plain smooth black chest.",
 "hoodie": f"Top-down flat lay of the front of a plain black heavyweight cotton pullover hoodie with a kangaroo pocket and blank drawcords, hood laid flat behind the neck, long sleeves resting straight along the sides of the body (not crossed), perfectly symmetrical and centered, {NOIR}. Plain smooth black chest and plain sleeves.",
 "casquette": f"Front view of a plain black six-panel baseball cap with a curved brim, seen straight on from the front at eye level, centered and symmetrical, smooth empty front panel, black adjustable strap at back not visible, {NOIR}.",
 "tuque": f"Front view of a plain black ribbed knit beanie (Canadian tuque) with a wide folded cuff, worn on an invisible round form, seen straight on, centered and symmetrical, smooth empty cuff, {NOIR}.",
 "tasse": f"Front view of a plain matte black ceramic coffee mug with a simple C-shaped handle on the right side, seen straight on at mid-height from the front, centered, vertical straight sides, {NOIR}, slate surface slightly reflecting the base.",
 "gourde": f"Front view of a plain brushed stainless steel water bottle with a black screw cap and a small black carry loop, tall cylindrical shape, seen straight on at mid-height, centered, {NOIR}.",
 "isotherme": f"Front view of a plain cream-colored (warm off-white, powder coated matte) insulated vacuum steel bottle with a matte black screw cap, tall cylindrical shape, seen straight on at mid-height, centered, {NOIR}.",
 "tote": f"Front view of a plain natural cream cotton canvas tote bag with two long flat handles, hanging flat and straight against a seamless dark charcoal wall, perfectly symmetrical and centered, visible fabric weave and a few soft natural folds, large empty front panel.",
 "carnet": f"Front view of a plain closed matte black hardcover A5 notebook with rounded corners and a black elastic band, standing upright, seen straight on from the front, centered, smooth black cover with fine leatherette texture, {NOIR}.",
 "carnet_ouvert": f"Top-down view of a blank hardcover notebook lying open flat, two empty cream-colored pages with no lines and no printing, black hard cover edges, a black ribbon bookmark, centered, {NOIR}.",
 "stylo": f"A plain matte black anodized metal ballpoint pen lying perfectly horizontal, centered in frame, clip on top, seen from the side, long clean barrel, {NOIR}, soft reflection.",
 "usb": f"A small matte black metal USB flash drive with a rectangular body, lying flat, next to its open slim matte black rigid presentation case with a dark foam inlay, seen from above at a slight angle, {NOIR}.",
 "badge": f"Top-down flat lay of a plain black woven lanyard in a gentle curve with a metal clasp, attached to a black rigid card holder with an empty blank white insert card, centered, {NOIR}.",
 "tapis": f"Overhead view slightly angled of an extra-large rectangular matte black desk mat with neatly stitched edges, lying on a dark walnut wooden desk, nothing else on it, {FIN}",
 "pochette": f"Top-down view of a plain matte black neoprene laptop sleeve with a zipper along the top edge, lying flat, rounded corners, centered, {NOIR}.",
 "trousse": f"A rigid matte black gift box with magnetic flap lid opened upright at the back, filled with crumpled black tissue paper, viewed from above at 45 degrees, empty, centered, {NOIR}.",
 "sac_papier": f"Front view of a plain matte black paper shopping bag with twisted black rope handles, standing upright with crisp folds and a gusset visible on the side, seen straight on, centered, {NOIR}.",
 "ruban": f"A roll of plain matte black packing tape with a short length of tape unrolled and curling, standing on its side, three-quarter view, {NOIR}.",
 "coffret": f"A rigid matte black presentation box with a flat lid, closed, photographed from above at a slight angle so the lid top is a large clean flat surface, centered, with a thin black ribbon pull tab, {NOIR}.",
 "kiosque": f"Wide empty trade show booth in a modern dark convention hall: a tall flat white tensioned fabric backdrop wall with nothing printed on it and a straight black reception counter in front of it, perfectly frontal view, symmetrical, soft overhead lighting, a clean dark floor, no signage, no people, no text.",
 "lampe": f"A square cube-shaped night light made of frosted opal glass lit from within with a warm saturated orange glow, sitting on a dark wooden shelf in a dim room, seen straight on, soft glow on the shelf, no text, no logo, minimal.",
 "usb2": f"Close-up product photo of a single slim rectangular matte black anodised aluminium USB flash drive with a swivel metal cover, lying flat and centered on a dark charcoal slate surface, seen from above at a slight angle, large in the frame, perfectly plain smooth top face, {NOIR}.",
 "portable": f"Front view of a closed dark grey laptop lid, perfectly flat and smooth with no logo, centered, seen from the front slightly from above, {NOIR}.",
}
if __name__ == "__main__":
    noms = sys.argv[1:] or list(P)
    SORTIE.mkdir(exist_ok=True)
    def un(n):
        f = SORTIE / f"{n}.png"
        if f.exists(): return n, "deja"
        p = P[n] + ("" if n in ("tapis",) else " " + FIN)
        try:
            image(p, f, format="1:1"); return n, "ok"
        except Exception as e:
            return n, f"ECHEC {e}"
    with cf.ThreadPoolExecutor(2) as ex:
        for n, s in ex.map(un, noms):
            print(n, s, flush=True)
