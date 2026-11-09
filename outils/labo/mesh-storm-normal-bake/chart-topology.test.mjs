import {test} from 'node:test';
import assert from 'node:assert/strict';
import {validateChartTopology} from './chart-topology.mjs';
const corners=[{uv:[0,0],p:[0,0,0]},{uv:[.7,0],p:[1,0,0]},{uv:[0,.7],p:[0,1,0]},{uv:[.7,.7],p:[1,1,0]}];
function make(ids,id=1){return {chartId:id,targetUv:ids.map(i=>[...corners[i].uv]),sourceUv:ids.map(i=>[...corners[i].uv]),positions:ids.map(i=>[...corners[i].p]),normals:ids.map(()=>[0,0,1]),tangents:ids.map(()=>[1,0,0,1])};}
test('accepts connected compatible triangles',()=>assert.deepEqual(validateChartTopology([make([0,1,2]),make([1,3,2])]),{triangles:2,charts:1}));
test('rejects a shared edge whose source normals differ',()=>{const a=make([0,1,2]),b=make([1,3,2]);b.normals[0]=[0,1,0];assert.throws(()=>validateChartTopology([a,b]),/discontinuous/)});
test('rejects inconsistent attributes at a UV vertex shared through another edge path',()=>{
 const tri=uv=>({chartId:1,targetUv:uv,sourceUv:uv.map(v=>[...v]),positions:uv.map(([u,v])=>[u,v,0]),normals:uv.map(()=>[0,0,1]),tangents:uv.map(()=>[1,0,0,1])});
 const ts=[tri([[0,0],[.5,0],[0,.5]]),tri([[.5,0],[.5,.5],[0,.5]]),tri([[.5,.5],[0,.5],[1,.5]]),tri([[.5,.5],[1,.5],[0,0]])];
 ts[3].normals[2]=[0,1,0];assert.throws(()=>validateChartTopology(ts),/discontinuous shared vertex/);
});
for(const [attribute,value] of [['positions',[2,0,0]],['tangents',[1,0,0,-1]],['sourceUv',[.3,.4]]])
 test(`rejects a shared edge with different ${attribute}`,()=>{const a=make([0,1,2]),b=make([1,3,2]);b[attribute][0]=value;assert.throws(()=>validateChartTopology([a,b]),/discontinuous/)});
test('accepts reversed vertex ordering for matching edge',()=>assert.equal(validateChartTopology([make([0,1,2]),make([2,3,1])]).charts,1));
test('rejects islands assigned to the same chart',()=>{const a=make([0,1,2]),b=make([1,3,2]);b.targetUv=b.targetUv.map(([u,v])=>[u+.2,v+.2]);assert.throws(()=>validateChartTopology([a,b]),/disconnected/)});
test('rejects three faces on the same edge',()=>{const a=make([0,1,2]),b=make([1,3,2]),c=make([1,3,2]);assert.throws(()=>validateChartTopology([a,b,c]),/non-manifold/)});
test('different chart ids require no connectivity',()=>assert.equal(validateChartTopology([make([0,1,2],1),make([1,3,2],2)]).charts,2));
test('chart IDs must fit the nonzero Uint16 owner range',()=>{
 for(const id of [0,-1,65536,1.5,NaN,null])assert.throws(()=>validateChartTopology([make([0,1,2],id)]),/chartId/);
 assert.equal(validateChartTopology([make([0,1,2],65535)]).charts,1);
});
test('rejects one-ULP departure in affine mapping',()=>{const a=make([0,1,2]),b=make([1,3,2]);b.positions[1][0]=1+Number.EPSILON;assert.throws(()=>validateChartTopology([a,b]),/incompatible affine/)});
