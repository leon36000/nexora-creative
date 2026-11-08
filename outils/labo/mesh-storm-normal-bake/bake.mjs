import {reprojectNormal} from '../mesh-storm-frame/reproject.mjs';
import {createRequire} from 'node:module';
import {pathToFileURL} from 'node:url';
import {validateChartTopology} from './chart-topology.mjs';

const appRequire = createRequire(new URL('../../../app/package.json', import.meta.url));
const {orient2d} = await import(pathToFileURL(appRequire.resolve('robust-predicates')).href);

const fail = message => { throw new Error(`UNSUPPORTED: ${message}`); };
const finite2 = p => Array.isArray(p) && p.length===2 && p.every(Number.isFinite);
const sub = (a,b) => [a[0]-b[0],a[1]-b[1]];
const cross = (a,b) => a[0]*b[1]-a[1]*b[0];
function barycentric(p, tri) {
  const e1=sub(tri[1],tri[0]), e2=sub(tri[2],tri[0]), rel=sub(p,tri[0]), det=cross(e1,e2);
  if (!Number.isFinite(det)||Math.abs(det)<1e-10) fail('degenerate UV triangle');
  const b=cross(rel,e2)/det, c=cross(e1,rel)/det;
  return [1-b-c,b,c];
}
// Adaptive orientation tests keep winding and Y-axis convention irrelevant to separation.
function interiorsOverlap(a,b) {
  for (const t of [a,b]) for (let i=0;i<3;i++) {
    const p=t[i],q=t[(i+1)%3], opposite=t[(i+2)%3], other=t===a?b:a;
    const orientation=r=>orient2d(...p,...q,...r);
    const side=Math.sign(orientation(opposite));
    if (!side) fail('degenerate robust UV triangle');
    if (other.every(r=>Math.sign(orientation(r))*side<=0)) return false;
  }
  return true;
}
function sampleLinearClamp(image,u,v) {
  const {width,height,data,channels}=image, x=u*width-.5, y=v*height-.5;
  const x0=Math.floor(x), y0=Math.floor(y), tx=x-x0, ty=y-y0;
  const at=(ix,iy,c)=>data[(Math.max(0,Math.min(height-1,iy))*width+Math.max(0,Math.min(width-1,ix)))*channels+c]/255;
  return [0,1,2].map(c=>(at(x0,y0,c)*(1-tx)+at(x0+1,y0,c)*tx)*(1-ty)+(at(x0,y0+1,c)*(1-tx)+at(x0+1,y0+1,c)*tx)*ty);
}
/** CPU laboratory proof for bounded in-range, non-overlapping UVs and already decoded raw RGB(A).
 * No GPU, scene transforms, mipmaps, padding, image encoding, filesystem or product integration.
 * UV image origin is top-left glTF convention. Returns new raw RGB bytes and coverage mask.
 */
export function bakeStormNormalMap({triangles,image,width,height,normalScale=1,sampler}) {
  if (!Array.isArray(triangles)||triangles.length===0||triangles.length>512) fail('triangle count outside laboratory limit');
  const explicitCharts=triangles.some(t=>Object.hasOwn(t??{},'chartId'));
  if (explicitCharts) validateChartTopology(triangles);
  if (!Number.isInteger(width)||!Number.isInteger(height)||width<1||height<1||width>2048||height>2048) fail('output dimensions outside laboratory limit');
  if (!image||!Number.isInteger(image.width)||!Number.isInteger(image.height)||image.width<1||image.height<1||![3,4].includes(image.channels)||!(image.data instanceof Uint8Array)||image.data.length!==image.width*image.height*image.channels) fail('invalid source image');
  if (!sampler||sampler.magFilter!==9729||sampler.minFilter!==9729||sampler.wrapS!==33071||sampler.wrapT!==33071) fail('only LINEAR/CLAMP_TO_EDGE is supported');
  let rasterCandidates=0;
  for (const [i,t] of triangles.entries()) {
    for (const [label, uv] of [['source',t?.sourceUv],['target',t?.targetUv]]) {
      if (!Array.isArray(uv)||uv.length!==3||uv.some(p=>!finite2(p)||p.some(x=>x<0||x>1))) fail(`triangle ${i} ${label} UV outside [0,1]`);
      if (uv.some(p=>p.some(x=>x!==0 && x<2**-400))) fail(`triangle ${i} ${label} UV below numerical range`);
      barycentric(uv[0],uv);
    }
    const center=t.sourceUv.reduce((a,p)=>[a[0]+p[0]/3,a[1]+p[1]/3],[0,0]);
    reprojectNormal({...t,uv:t.targetUv,barycentric:[1/3,1/3,1/3],rawNormal:sampleLinearClamp(image,...center),normalScale});
    const us=t.targetUv.map(p=>p[0]),vs=t.targetUv.map(p=>p[1]);
    const x0=Math.max(0,Math.ceil(Math.min(...us)*width-.5)),x1=Math.min(width-1,Math.floor(Math.max(...us)*width-.5));
    const y0=Math.max(0,Math.ceil(Math.min(...vs)*height-.5)),y1=Math.min(height-1,Math.floor(Math.max(...vs)*height-.5));
    rasterCandidates+=Math.max(0,x1-x0+1)*Math.max(0,y1-y0+1);
    if (rasterCandidates>16_777_216) fail('raster candidate budget exceeded');
    for (let j=0;j<i;j++) if (interiorsOverlap(t.targetUv,triangles[j].targetUv)) fail(`target UV interiors overlap: triangles ${j} and ${i}`);
  }
  const pixels=new Uint8Array(width*height*3), mask=new Uint8Array(width*height), owners=new Uint16Array(width*height);
  for(let i=0;i<width*height;i++) pixels.set([128,128,255],i*3);
  let covered=0;
  for (const [chartIndex,t] of triangles.entries()) {
    const us=t.targetUv.map(p=>p[0]),vs=t.targetUv.map(p=>p[1]);
    const x0=Math.max(0,Math.ceil(Math.min(...us)*width-.5)), x1=Math.min(width-1,Math.floor(Math.max(...us)*width-.5));
    const y0=Math.max(0,Math.ceil(Math.min(...vs)*height-.5)), y1=Math.min(height-1,Math.floor(Math.max(...vs)*height-.5));
    for(let y=y0;y<=y1;y++)for(let x=x0;x<=x1;x++) {
      const u=(x+.5)/width,v=(y+.5)/height,bary=barycentric([u,v],t.targetUv);
      if (bary.some(w=>w < -1e-12)) continue;
      const index=y*width+x;
      // Shared edges can hit pixel centers; never overwrite an already encoded texel.
      if(mask[index]) fail('UV rasterization collision on shared boundary');
      const weights=bary.map(w=>Math.max(0,w)),sum=weights.reduce((a,b)=>a+b,0), normalized=weights.map(w=>w/sum);
      const sourceUv=t.sourceUv.reduce((a,p,i)=>[a[0]+p[0]*normalized[i],a[1]+p[1]*normalized[i]],[0,0]);
      const target=reprojectNormal({...t,uv:t.targetUv,barycentric:normalized,rawNormal:sampleLinearClamp(image,...sourceUv),normalScale}).targetNormal;
      pixels.set(target.map(c=>Math.round(Math.max(0,Math.min(1,c*.5+.5))*255)),index*3);mask[index]=1;owners[index]=explicitCharts?t.chartId:chartIndex+1;covered++;
    }
  }
  if (!covered) fail('no output texels covered');
  return {pixels,mask,owners,width,height,covered};
}
