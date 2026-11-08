import test from 'node:test';
import assert from 'node:assert/strict';
import {bakeStormNormalMap} from './bake.mjs';
const sampler={magFilter:9729,minFilter:9729,wrapS:33071,wrapT:33071};
const image={width:1,height:1,channels:3,data:new Uint8Array([192,64,240])};
const uv=[[0,0],[1,0],[0,1]];
const tri=()=>({positions:[[0,0,0],[1,0,0],[0,1,0]],normals:[[0,0,1],[0,0,1],[0,0,1]],tangents:[[1,0,0,1],[1,0,0,1],[1,0,0,1]],sourceUv:uv.map(x=>[...x]),targetUv:uv.map(x=>[...x])});
const bake=(overrides={})=>bakeStormNormalMap({triangles:[tri()],image,width:4,height:4,normalScale:1,sampler,...overrides});
const pixel=(out,x,y)=>[...out.pixels.slice((y*out.width+x)*3,(y*out.width+x)*3+3)];
const normalized=v=>{const n=Math.hypot(...v);return v.map(x=>x/n)};
const encode=v=>v.map(x=>Math.round((x*.5+.5)*255));
test('aligned chart reconstructs expected Storm tangent-space direction',()=>{
 const out=bake(),[x,y,z]=normalized([192/255*2-1,64/255*2-1,240/255*2-1]);
 assert.equal(out.mask[0],1);assert.deepEqual(pixel(out,0,0),encode([x,-y,z]));
});
test('rotated target chart uses source UV sampling and target Storm basis separately',()=>{
 const t=tri();t.targetUv=[[1,0],[1,1],[0,0]];const out=bake({triangles:[t]});
 const [x,y,z]=normalized([192/255*2-1,64/255*2-1,240/255*2-1]);
 assert.equal(out.mask[3],1);assert.deepEqual(pixel(out,3,0),encode([-y,-x,z]));
});
test('source UV drives filtered raw image independently of target rotation',()=>{
 const t=tri();t.targetUv=[[1,0],[1,1],[0,0]];
 const img={width:2,height:2,channels:3,data:new Uint8Array([190,80,240,210,80,240,190,100,240,210,100,240])};
 const original=bake({image:img}),rotated=bake({triangles:[t],image:img});
 const a=pixel(original,0,0),b=pixel(rotated,3,0);
 // Both output centers map to source UV (.125,.125), clamped to the same source texel.
 const d1=normalized([(190/255)*2-1,(80/255)*2-1,(240/255)*2-1]);
 assert.deepEqual(a,encode([d1[0],-d1[1],d1[2]]));assert.deepEqual(b,encode([-d1[1],-d1[0],d1[2]]));
});
test('rejects subpixel overlap even when no output pixel center intersects it',()=>{
 const a=tri(),b=tri();a.targetUv=[[.01,.01],[.04,.01],[.01,.04]];b.targetUv=[[.02,.02],[.05,.02],[.02,.05]];
 assert.throws(()=>bake({triangles:[a,b],width:2,height:2}),/overlap/);
});
test('rejects unsupported sampler, w and UVs',()=>{
 assert.throws(()=>bake({sampler:{...sampler,wrapS:10497}}),/LINEAR/);
 const t=tri();t.tangents[0][3]=-1;assert.throws(()=>bake({triangles:[t]}),/handedness/);
 const u=tri();u.sourceUv[0]=[-.1,0];assert.throws(()=>bake({triangles:[u]}),/source UV/);
});
test('accepts disjoint target charts',()=>{
 const a=tri(),b=tri();a.targetUv=[[0,0],[.4,0],[0,.4]];b.targetUv=[[.6,.6],[1,.6],[.6,1]];
 assert.ok(bake({triangles:[a,b],width:10,height:10}).covered>0);
});
test('normalScale zero yields a neutral map at covered texels',()=>{
 const out=bake({normalScale:0});assert.deepEqual(pixel(out,0,0),[128,128,255]);
});
test('rejects a source or target UV triangle with zero area',()=>{
 const a=tri();a.sourceUv=[[0,0],[.5,.5],[1,1]];assert.throws(()=>bake({triangles:[a]}),/degenerate UV/);
 const b=tri();b.targetUv=[[0,0],[.5,.5],[1,1]];assert.throws(()=>bake({triangles:[b]}),/degenerate UV/);
});
test('LINEAR sampling averages four raw RGB texels at source center',()=>{
 const img={width:2,height:2,channels:3,data:new Uint8Array([190,80,240,210,80,240,190,100,240,210,100,240])};
 const out=bake({image:img,width:1,height:1});const [x,y,z]=normalized([200/255*2-1,90/255*2-1,240/255*2-1]);
 assert.deepEqual(pixel(out,0,0),encode([x,-y,z]));
});
