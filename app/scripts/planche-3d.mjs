/**
 * Planche contact d'un GLB : 4 vues (avant, droite, arrière, gauche) rendues par three.js dans Chromium
 * sans écran (Playwright), lumière de studio neutre. Sert à juger un résultat 3D à l'œil.
 *
 *   node scripts/planche-3d.mjs <modele.glb> <planche.jpg> [taille]
 * Playwright : NEXORA_PLAYWRIGHT=/chemin/vers/node_modules/playwright (défaut : cache npx du poste).
 */
import { createServer } from 'node:http';
import { readFileSync, existsSync } from 'node:fs';
import { resolve, dirname, extname } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const [glb, sortie, taille = '512'] = process.argv.slice(2);
if (!glb || !sortie) { console.error('usage: planche-3d.mjs <modele.glb> <planche.jpg> [taille]'); process.exit(2); }
const ici = dirname(fileURLToPath(import.meta.url));
const three = resolve(ici, '../node_modules/three');
const pw = process.env.NEXORA_PLAYWRIGHT ?? '/home/pc6/.npm/_npx/e41f203b7505f1fb/node_modules/playwright';
const { chromium } = await import(pathToFileURL(resolve(pw, 'index.mjs')).href).catch(() => import(pathToFileURL(resolve(pw, 'index.js')).href));

const page = `<!doctype html><meta charset=utf-8><body style="margin:0;background:#1a1a1a">
<script type="importmap">{"imports":{"three":"/three/build/three.module.js","three/addons/":"/three/examples/jsm/"}}</script>
<script type="module">
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
const S = ${Number(taille)};
const r = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
r.setSize(S * 2, S * 2); r.toneMapping = THREE.ACESFilmicToneMapping; document.body.append(r.domElement);
r.setScissorTest(true);
const sc = new THREE.Scene(); sc.background = new THREE.Color(0x2a2a2a);
sc.environment = new THREE.PMREMGenerator(r).fromScene(new RoomEnvironment(), 0.04).texture;
const gltf = await new GLTFLoader().loadAsync('/modele.glb');
const obj = gltf.scene; sc.add(obj);
const box = new THREE.Box3().setFromObject(obj), c = box.getCenter(new THREE.Vector3()), rad = box.getSize(new THREE.Vector3()).length() / 2;
let tris = 0; obj.traverse((o) => { if (o.isMesh) { const g = o.geometry; tris += (g.index ? g.index.count : g.attributes.position.count) / 3; } });
const cam = new THREE.PerspectiveCamera(30, 1, 0.01, 100);
[0, 90, 180, 270].forEach((yaw, i) => {
  const a = (yaw + 35) * Math.PI / 180, d = rad / Math.sin(15 * Math.PI / 180) * 1.05;
  cam.position.set(c.x + Math.sin(a) * d, c.y + rad * 0.35, c.z + Math.cos(a) * d); cam.lookAt(c);
  const x = (i % 2) * S, y = (1 - Math.floor(i / 2)) * S;
  r.setViewport(x, y, S, S); r.setScissor(x, y, S, S); r.render(sc, cam);
});
window.__fini = { tris: Math.round(tris), taille: box.getSize(new THREE.Vector3()).toArray() };
</script>`;
const srv = createServer((q, s) => {
  const u = decodeURIComponent(q.url.split('?')[0]);
  const f = u === '/' ? null : u === '/modele.glb' ? resolve(glb) : u.startsWith('/three/') ? resolve(three, u.slice(7)) : null;
  if (u === '/') { s.setHeader('content-type', 'text/html'); return s.end(page); }
  if (!f || !existsSync(f)) { s.statusCode = 404; return s.end(); }
  s.setHeader('content-type', extname(f) === '.js' ? 'text/javascript' : 'application/octet-stream'); s.end(readFileSync(f));
}).listen(0);
const port = srv.address().port;
const nav = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const p = await nav.newPage({ viewport: { width: Number(taille) * 2, height: Number(taille) * 2 } });
p.on('pageerror', (e) => console.error('page:', e.message));
await p.goto(`http://127.0.0.1:${port}/`);
await p.waitForFunction('window.__fini', null, { timeout: 120000 });
await p.screenshot({ path: sortie, type: 'jpeg', quality: 88 });
console.log(JSON.stringify(await p.evaluate('window.__fini')));
await nav.close(); srv.close();
