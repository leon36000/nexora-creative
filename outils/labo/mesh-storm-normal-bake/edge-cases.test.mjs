import test from 'node:test';
import assert from 'node:assert/strict';
import {bakeStormNormalMap} from './bake.mjs';
import {padNormalCharts} from './pad.mjs';
const sampler={magFilter:9729,minFilter:9729,wrapS:33071,wrapT:33071};
const image={width:1,height:1,channels:3,data:new Uint8Array([192,64,240])};
const uv=[[0,0],[1,0],[0,1]];
const tri=()=>({positions:[[0,0,0],[1,0,0],[0,1,0]],normals:[[0,0,1],[0,0,1],[0,0,1]],tangents:[[1,0,0,1],[1,0,0,1],[1,0,0,1]],sourceUv:uv.map(x=>[...x]),targetUv:uv.map(x=>[...x])});
const bake=(triangles,extra={})=>bakeStormNormalMap({triangles,image,width:4,height:4,normalScale:1,sampler,...extra});
test('same source UV footprint is allowed when target charts are disjoint',()=>{
 const a=tri(),b=tri();a.targetUv=[[0,0],[.4,0],[0,.4]];b.targetUv=[[.6,.6],[1,.6],[.6,1]];
 assert.ok(bake([a,b]).covered>0);
});
test('rejects the binary64 one-ULP subpixel overlap even when a third chart is covered',()=>{
 const a=tri(),b=tri(),c=tri();
 a.targetUv=[[.125,.125],[.125010000005,.125],[.125,.125010000005]];
 b.targetUv=[[.12501000000499998,.125],[.12502000001,.125],[.12501000000499998,.125010000005]];
 c.targetUv=[[.6,.6],[1,.6],[.6,1]];
 assert.throws(()=>bake([a,b,c],{width:16,height:16}),/target UV interiors overlap/);
});
test('rejects UV coordinates outside the laboratory numerical range',()=>{
 const a=tri();a.targetUv[0][0]=2**-401;
 assert.throws(()=>bake([a]),/UV below numerical range/);
});
test('constant negative handedness is accepted; mixed handedness is rejected before raster',()=>{
 const a=tri();a.tangents.forEach(t=>t[3]=-1);assert.ok(bake([a]).covered>0);
 const b=tri();b.tangents[1][3]=-1;assert.throws(()=>bake([b]),/handedness/);
});
test('shared UV edge not through a pixel center is accepted',()=>{
 const a=tri(),b=tri();a.targetUv=[[0,0],[.5,0],[.5,.5]];b.targetUv=[[.5,0],[1,0],[.5,.5]];
 assert.ok(bake([a,b]).covered>0);
});
test('shared UV edge through pixel centers fails closed at raster collision',()=>{
 const a=tri(),b=tri();a.targetUv=[[0,0],[.5,0],[0,.5]];b.targetUv=[[.5,0],[.5,.5],[0,.5]];
 assert.throws(()=>bake([a,b]),/rasterization collision/);
});
test('valid tiny target chart with no pixel center fails closed as no coverage',()=>{
 const a=tri();a.targetUv=[[.01,.01],[.02,.01],[.01,.02]];
 assert.throws(()=>bake([a]),/no output texels covered/);
});
test('bake preserves caller-owned triangles and image buffers',()=>{
 const a=tri(),copy=structuredClone(a),raw=image.data.slice();
 bake([a]);assert.deepEqual(a,copy);assert.deepEqual(image.data,raw);
});
test('rejects excessive raster bounding boxes before allocating the atlas',()=>{
 const triangles=Array.from({length:6},(_,i)=>{const t=tri(),v=i*.015;t.targetUv=[[0,v],[.9,.9+v],[0,v+.01]];return t;});
 assert.throws(()=>bake(triangles,{width:2048,height:2048}),/raster candidate budget/);
});
test('padding at canvas corner clips at edges without wrapping',()=>{
 const pixels=new Uint8Array(6*6*3),owners=new Uint16Array(6*6);owners[0]=17;pixels.set([21,22,23],0);
 const p=padNormalCharts({pixels,owners,width:6,height:6,radius:1});
 assert.equal(p.padded,3);assert.deepEqual([...p.owners.slice(0,6)],[17,17,0,0,0,0]);
 assert.equal(p.owners[6],17);assert.equal(p.owners[7],17);assert.equal(p.owners[35],0);
 assert.equal(owners.filter(Boolean).length,1);assert.equal(pixels.filter(x=>x!==0).length,3);
});
test('maximum radius fills bounded canvas from a central chart without changing inputs',()=>{
 const pixels=new Uint8Array(10*10*3),owners=new Uint16Array(100);owners[4*10+4]=65535;pixels.set([1,2,3],(4*10+4)*3);
 const p=padNormalCharts({pixels,owners,width:10,height:10,radius:8});
 assert.equal(p.padded,99);assert.equal(p.owners.filter(Boolean).length,100);assert.equal(p.owners[0],65535);
 assert.equal(owners.filter(Boolean).length,1);assert.equal(pixels.filter(x=>x!==0).length,3);
});
test('each 8-connected padding step includes diagonal pixels',()=>{
 const pixels=new Uint8Array(5*5*3),owners=new Uint16Array(25);owners[2*5+2]=1;
 const p=padNormalCharts({pixels,owners,width:5,height:5,radius:1});
 assert.equal(p.owners[1*5+1],1);assert.equal(p.owners[1*5+2],1);assert.equal(p.owners[2*5+1],1);assert.equal(p.padded,8);
});
test('bake ownership connects directly to conservative padding',()=>{
 const a=tri(),b=tri();a.targetUv=[[0,0],[.2,0],[0,.2]];b.targetUv=[[.8,.8],[1,.8],[.8,1]];
 const out=bake([a,b],{width:16,height:16});assert.equal(out.owners.filter(v=>v===1).length>0,true);assert.equal(out.owners.filter(v=>v===2).length>0,true);
 for(let i=0;i<out.mask.length;i++)assert.equal(out.mask[i]!==0,out.owners[i]!==0);
 const padded=padNormalCharts({...out,radius:1});assert.ok(padded.padded>0);assert.equal(out.owners.filter(Boolean).length,out.covered);
});
test('adjacent triangles with distinct bake owners are conservatively refused by padding',()=>{
 const a=tri(),b=tri();a.targetUv=[[0,0],[.5,0],[.5,.5]];b.targetUv=[[.5,0],[1,0],[.5,.5]];
 const out=bake([a,b],{width:8,height:8});
 assert.throws(()=>padNormalCharts({...out,radius:1}),/padding would mix distinct charts/);
});
