// Rendu Chromium (Playwright) : svg/html -> png ou pdf. Usage : bun rend.mjs jobs.json
// job : {type:"png"|"pdf", src:"/chemin.svg|.html", out:"...", width:px, height:px, transparent:true, scale:1, wmm, hmm}
import { chromium } from "/home/pc6/Desktop/NexoraSite/web/node_modules/@playwright/test/index.mjs";
import { readFileSync } from "node:fs";
const jobs = JSON.parse(readFileSync(process.argv[2], "utf8"));
const b = await chromium.launch();
for (const j of jobs) {
  const ctx = await b.newContext({ viewport: { width: j.width || 1000, height: j.height || 1000 }, deviceScaleFactor: j.scale || 1 });
  const p = await ctx.newPage();
  await p.goto("file://" + j.src, { waitUntil: "load" });
  await p.evaluate(() => document.fonts && document.fonts.ready);
  if (j.type === "png") {
    await p.screenshot({ path: j.out, omitBackground: !!j.transparent, fullPage: false });
  } else {
    await p.pdf({ path: j.out, width: j.wmm + "mm", height: j.hmm + "mm", printBackground: true, margin: { top: 0, right: 0, bottom: 0, left: 0 }, preferCSSPageSize: false });
  }
  await ctx.close();
}
await b.close();
