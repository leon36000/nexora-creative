// Documents de la publicité : textes d'annonces (md + csv), storyboards vidéo (md + json), archives .zip des bannières HTML5.
import fs from "node:fs";
import path from "node:path";
import { execFileSync } from "node:child_process";
import { ACCROCHES, CARROUSELS, VIDEO6, VIDEO15, LIMITES } from "./textes.mjs";
import { TXT } from "../../social/sources/moteur/marque.mjs";
const RAC = path.resolve(import.meta.dirname, "..");
const FINAL = path.join(RAC, "final");
const n = (s) => [...s].length;

export function textesAnnonces() {
  const md = ["# Textes des annonces Facebook et Instagram", "",
    `Limites respectées (vérifiées à chaque génération) : titre ${LIMITES.titre} caractères, texte principal ${LIMITES.principal} avant « voir plus », description ${LIMITES.description}. Aucun chiffre, prix, date, client ni statistique. **Appels à l’action** selon l’état réel des outils (\`web/src/i18n/apps.ts\`) : aucun outil n’est vendu en libre-service ; WorkStudio est livré avec démonstration sur demande ; l’accompagnement sur mesure existe. On écrit donc « Planifier un diagnostic », « Voir les solutions » ou « Rejoindre la liste d’attente » ; « Essayer Nexora Creative » n’est pas utilisé tant que Nexora Creative est à une étape ultérieure. Le bouton de la plateforme est l’un des boutons fixes de Meta (colonne « Bouton Meta ») ; le libellé sobre vit dans l’image et le texte.`, ""];
  const rows = [["accroche", "langue", "titre", "n_titre", "texte_principal", "n_principal", "description", "n_description", "bouton_meta", "appel_a_l_action"]];
  for (const lang of ["fr", "en"]) {
    md.push(`## ${lang === "fr" ? "fr-CA" : "en-CA"}`, "", "| Accroche | Titre | Texte principal | Description | Bouton Meta | Appel à l’action (dans l’image) |", "|---|---|---|---|---|---|");
    for (const a of ACCROCHES) {
      const cta = TXT[a.cta][lang];
      md.push(`| ${a.id} | ${a.titre[lang]} (${n(a.titre[lang])}) | ${a.principal[lang]} (${n(a.principal[lang])}) | ${a.description[lang]} (${n(a.description[lang])}) | ${a.boutonMeta[lang]} | ${cta} |`);
      rows.push([a.id, lang, a.titre[lang], n(a.titre[lang]), a.principal[lang], n(a.principal[lang]), a.description[lang], n(a.description[lang]), a.boutonMeta[lang], cta]);
    }
    md.push("", `### Carrousels (${lang})`, "", "| Carrousel | Titre | Texte principal | Cartes |", "|---|---|---|---|");
    for (const [k, c] of Object.entries(CARROUSELS)) md.push(`| ${k} | ${c.titre[lang]} (${n(c.titre[lang])}) | ${c.principal[lang]} (${n(c.principal[lang])}) | ${c.cartes.join(", ")} |`);
    md.push("");
  }
  md.push("## Associations image et texte", "", "Chaque accroche existe en 4 formats (`1x1`, `4x5`, `paysage` 1200 × 628, `9x16`) dans `accroches/<accroche>/` ; le même texte s’applique aux quatre. Pour un jeu A/B, croiser les trois accroches avec les quatre formats (douze combinaisons par langue).", "",
    "## Rappel sur la limite de texte dans l’image", "", "Le texte des images se limite au titre et au logo (le titre dépasse rarement six mots) : lisible à 360 px de large.", "");
  fs.writeFileSync(path.join(FINAL, "facebook-instagram", "textes-annonces.md"), md.join("\n"));
  fs.writeFileSync(path.join(FINAL, "facebook-instagram", "textes-annonces.csv"), rows.map((r) => r.map((c) => `"${String(c).replace(/"/g, '""')}"`).join(",")).join("\n"));
}

export function storyboards() {
  const dir = path.join(FINAL, "facebook-instagram");
  for (const [dur, liste, total] of [["6s", VIDEO6, 6], ["15s", VIDEO15, 15]]) {
    const md = [`# Annonce vidéo de ${total} s : plans fixes prêts pour l’animation`, "",
      `Images numérotées dans \`video-${dur}/9x16\` (1080 × 1920, Stories et Reels ; texte hors des zones masquées : 250 px en haut, 340 px en bas) et \`video-${dur}/1x1\` (1080 × 1080, fil). Les plans portent le même nom en fr et en. Animation CSS ou montage : ${dur === "6s" ? "trois plans de 2 s" : "six plans de 2,5 s"}, fondu enchaîné de 0,3 s, poussée lente de 4 % sur les plans photographiques, aucune transition spectaculaire. Le logo et le texte ne bougent jamais (ils sont posés en code). Musique : MiniMax-Music3 (Nexora Creative), ambiance « nuit québécoise », sans voix ; à générer avec \`outils/generer.py musique\`.`, "",
      "| № | Temps | Plan | Texte fr | Texte en | Mouvement |", "|---|---|---|---|---|---|"];
    for (const s of liste) md.push(`| ${s.n} | ${s.t} | ${s.plan} | ${s.texte.fr} | ${s.texte.en} | ${s.mouvement} |`);
    fs.writeFileSync(path.join(dir, `storyboard-${dur}.md`), md.join("\n") + "\n");
    fs.writeFileSync(path.join(dir, `sequence-${dur}.json`), JSON.stringify({ duree_s: total, fps: 30, plans: liste.map((s, i) => ({ n: s.n, image_9x16: `video-${dur}/9x16/plan-${String(s.n).padStart(2, "0")}-${s.plan}.{l}.png`, image_1x1: `video-${dur}/1x1/plan-${String(s.n).padStart(2, "0")}-${s.plan}.{l}.png`, debut_s: i * (total / liste.length), fin_s: (i + 1) * (total / liste.length), texte: s.texte, mouvement: s.mouvement, transition_fondu_s: 0.3 })) }, null, 2));
  }
}

export function zips() {
  const base = path.join(FINAL, "display", "html5");
  if (!fs.existsSync(base)) return 0;
  const py = `import zipfile,sys,os\nb=sys.argv[1]\nfor d in sorted(os.listdir(b)):\n    p=os.path.join(b,d)\n    if os.path.isdir(p):\n        z=zipfile.ZipFile(p+'.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9);z.write(os.path.join(p,'index.html'),'index.html');z.close()\n        s=os.path.getsize(p+'.zip')\n        if s>150*1024: print('TROP LOURD',d,s)\n`;
  execFileSync("python3", ["-c", py, base]);
  return fs.readdirSync(base).filter((f) => f.endsWith(".zip")).length;
}
if (import.meta.main) { fs.mkdirSync(path.join(FINAL, "facebook-instagram"), { recursive: true }); textesAnnonces(); storyboards(); console.log("zips:", zips()); }
