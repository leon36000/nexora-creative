// Rastérise les logos officiels de Nexora AI (SVG du dépôt du site, jamais modifiés) en PNG transparents pour le montage vidéo.
import { chromium } from "/home/pc6/Desktop/NexoraSite/web/node_modules/@playwright/test/index.mjs";
import { readFileSync, writeFileSync } from "node:fs";
const SRC = "/home/pc6/Desktop/NexoraSite/docs/marque/logos/";
const OUT = decodeURIComponent(new URL("../sources/logo/", import.meta.url).pathname);
const b = await chromium.launch();
async function png(nom, svg, w, h) {
  const p = await b.newPage({ viewport: { width: w, height: h } });
  await p.setContent(`<style>html,body{margin:0;background:transparent}svg{display:block;width:${w}px;height:${h}px}</style>${readFileSync(SRC + svg, "utf8")}`);
  writeFileSync(OUT + nom, await p.screenshot({ omitBackground: true, clip: { x: 0, y: 0, width: w, height: h } }));
  await p.close();
}
await png("logo-sombre-2400.png", "nexora-ai-logo-sombre.svg", 2400, Math.round(2400 * 52 / 285.55));
await png("symbole-sombre-1040.png", "nexora-ai-symbole-sombre.svg", 1040, 1040);
await png("logo-blanc-2400.png", "nexora-ai-logo-blanc.svg", 2400, Math.round(2400 * 52 / 285.55));
await b.close();
console.log("ok");
