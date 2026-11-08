import {test} from 'node:test';
import assert from 'node:assert/strict';
import {bakeStormNormalMap} from './bake.mjs';
import {padNormalCharts} from './pad.mjs';
const sampler={magFilter:9729,minFilter:9729,wrapS:33071,wrapT:33071};
const image={width:1,height:1,channels:3,data:new Uint8Array([192,64,240])};
const make=(uv,id=4)=>({chartId:id,targetUv:uv.map(v=>[...v]),sourceUv:uv.map(v=>[...v]),positions:uv.map(([u,v])=>[u,v,0]),normals:uv.map(()=>[0,0,1]),tangents:uv.map(()=>[1,0,0,1])});
const run=triangles=>bakeStormNormalMap({triangles,image,width:8,height:8,sampler});
test('continuous chart of two triangles shares one owner through padding',()=>{
 const a=make([[0,0],[.5,0],[.5,.5]]),b=make([[.5,0],[1,0],[.5,.5]]);
 const result=run([a,b]);assert.equal(new Set(result.owners.filter(Boolean)).size,1);
 const padded=padNormalCharts({...result,radius:1});assert.ok(padded.padded>0);assert.equal(new Set(padded.owners.filter(Boolean)).size,1);
});
test('same chart rejects an inconsistent shared source UV',()=>{
 const a=make([[0,0],[.5,0],[.5,.5]]),b=make([[.5,0],[1,0],[.5,.5]]);b.sourceUv[0][0]+=.01;
 assert.throws(()=>run([a,b]),/discontinuous shared (edge|vertex)/);
});
test('same chart still rejects shared edge passing through centers',()=>{
 const a=make([[0,0],[.5,0],[0,.5]]),b=make([[.5,0],[.5,.5],[0,.5]]);
 assert.throws(()=>run([a,b]),/rasterization collision/);
});
test('explicit ownership cannot be mixed with omitted chart IDs',()=>{
 const a=make([[0,0],[.5,0],[.5,.5]]),b=make([[.5,0],[1,0],[.5,.5]]);delete b.chartId;
 assert.throws(()=>run([a,b]),/chartId/);
});
test('a chart ID inherited from a prototype is not explicit',()=>{
 const a=make([[0,0],[.5,0],[.5,.5]]),b=make([[.5,0],[1,0],[.5,.5]]);delete b.chartId;Object.setPrototypeOf(b,{chartId:4});
 assert.throws(()=>run([a,b]),/chartId/);
});
test('the sheared counterexample is rejected even when shared attributes match',()=>{
 const a=make([[0,0],[.5,0],[.5,.5]]),b=make([[.5,0],[1,0],[.5,.5]]);b.positions[1][1]=.3;
 assert.throws(()=>run([a,b]),/incompatible affine/);
});
test('rejects an exact T-junction even when the chart is connected by other edges',()=>{
 const ts=[make([[.2,.5],[.8,.5],[.2,.8]]),make([[.2,.5],[.2,.8],[.1,.5]]),make([[.2,.5],[.1,.5],[.5,.2]]),make([[.2,.5],[.5,.2],[.5,.5]]),make([[.5,.5],[.5,.2],[.8,.5]])];
 ts[3].normals[2]=[0,1,0];ts[4].normals[0]=[0,1,0];ts[3].sourceUv[2]=[.9,.9];ts[4].sourceUv[0]=[.9,.9];
 assert.throws(()=>bakeStormNormalMap({triangles:ts,image,width:18,height:18,sampler}),/T-junction/);
});
