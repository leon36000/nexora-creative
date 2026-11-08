// Experiment only: validate caller-supplied chart membership before any raster output.
// Every finite binary64 value is an integer multiple of 2^-1074. Integer arithmetic
// therefore compares the UV-to-position affine Jacobians with no numeric tolerance.
import {createRequire} from 'node:module';
import {pathToFileURL} from 'node:url';
const appRequire=createRequire(new URL('../../../app/package.json',import.meta.url));
const {orient2d}=await import(pathToFileURL(appRequire.resolve('robust-predicates')).href);
const bytes=new DataView(new ArrayBuffer(8));

// Attributes that must agree on every shared vertex/edge of a chart.
const ATTRIBUTES=['positions','normals','tangents','sourceUv'];
// Attribute name -> expected components per vertex.
const ATTRIBUTE_SIZES=[['targetUv',2],['sourceUv',2],['positions',3],['normals',3],['tangents',4]];

function exactInteger(x){
 bytes.setFloat64(0,x,false);const bits=bytes.getBigUint64(0,false),negative=(bits>>63n)!==0n;
 const exponent=Number((bits>>52n)&0x7ffn),fraction=bits&((1n<<52n)-1n);
 const value=exponent===0?fraction:((1n<<52n)|fraction)<<BigInt(exponent-1);
 return negative?-value:value;
}
function jacobian(t){
 const uv=t.targetUv.map(p=>p.map(exactInteger)),pos=t.positions.map(p=>p.map(exactInteger));
 const du1=uv[1][0]-uv[0][0],dv1=uv[1][1]-uv[0][1],du2=uv[2][0]-uv[0][0],dv2=uv[2][1]-uv[0][1];
 const determinant=du1*dv2-dv1*du2;
 if(determinant===0n)throw new Error('UNSUPPORTED: degenerate chart UV');
 return {determinant,axis:pos[0].flatMap((_,j)=>{
   const p1=pos[1][j]-pos[0][j],p2=pos[2][j]-pos[0][j];
   return [p1*dv2-p2*dv1,p2*du1-p1*du2];
 })};
}
function sameJacobian(a,b){const A=jacobian(a),B=jacobian(b);return A.axis.every((x,i)=>x*B.determinant===B.axis[i]*A.determinant)}

// Exact equality of two coordinate/normal vectors (same length, all components ===).
const same=(a,b)=>a.length===b.length&&a.every((v,i)=>v===b[i]);
const key=v=>JSON.stringify(v);
const edgeKey=(a,b)=>[key(a),key(b)].sort().join('|');

function validateTriangleCount(triangles,fail){
 if(!Array.isArray(triangles)||triangles.length===0||triangles.length>512)fail('triangle count');
}
function validateChartId(t, fail){
 if(!t||!Object.hasOwn(t,'chartId')||!Number.isInteger(t.chartId)||t.chartId<1||t.chartId>65535)fail('chartId');
}
function validateAttributes(t, fail){
 for(const [name,size] of ATTRIBUTE_SIZES)
  if(!Array.isArray(t[name])||t[name].length!==3||t[name].some(v=>!Array.isArray(v)||v.length!==size||v.some(x=>!Number.isFinite(x))))fail(`invalid ${name}`);
}
function validateUvRange(t, fail){
 for(const uv of [t.targetUv,t.sourceUv])if(uv.some(p=>p.some(x=>x<0||x>1||(x!==0&&x<2**-400))))fail('UV outside numerical range');
}
function addToGroup(groups, chartId, i){
 if(!groups.has(chartId))groups.set(chartId,[]);groups.get(chartId).push(i);
}

// Per-chart accumulator: vertex/edge maps plus triangle adjacency.
function createChartState(indices){
 return {
  indices,
  adjacency:new Map(indices.map(i=>[i,new Set()])),
  edgeCount:new Map(),
  vertices:new Map(),
 };
}

// Registers vertex `a` (at triangle i, corner k) and edge a->b of one triangle corner.
function registerCorner(triangles, state, id, i, k, fail){
 const a=triangles[i].targetUv[k],b=triangles[i].targetUv[(k+1)%3];
 if(same(a,b))fail('degenerate chart edge');
 const previous=state.vertices.get(key(a));
 if(previous&&ATTRIBUTES.some(name=>!same(triangles[previous.i][name][previous.k],triangles[i][name][k])))fail(`chart ${id} discontinuous shared vertex`);
 if(!previous)state.vertices.set(key(a),{i,k,point:a});
 const e=edgeKey(a,b),entries=state.edgeCount.get(e)||[];entries.push({i,k});state.edgeCount.set(e,entries);
 if(entries.length>2)fail(`chart ${id} non-manifold edge`);
}

// Is p inside the inclusive bounding box of a-b, excluding the endpoints?
function isCandidateOnEdge(p,a,b){
 return !same(p,a)&&!same(p,b)&&p[0]>=Math.min(a[0],b[0])&&p[0]<=Math.max(a[0],b[0])&&p[1]>=Math.min(a[1],b[1])&&p[1]<=Math.max(a[1],b[1]);
}

// Any vertex lying exactly on an edge it does not belong to is a T-junction.
function checkTJunctions(triangles, state, id, fail){
 for(const entries of state.edgeCount.values()) {
  const {i,k}=entries[0],a=triangles[i].targetUv[k],b=triangles[i].targetUv[(k+1)%3];
  for(const {point:p} of state.vertices.values()) {
   if(!isCandidateOnEdge(p,a,b))continue;
   if(orient2d(...a,...b,...p)===0)fail(`chart ${id} T-junction`);
  }
 }
}

// Shared-edge check between the two triangles of a manifold edge; records adjacency.
function checkSharedEdge(triangles, state, id, a, b, fail){
 const ta=triangles[a.i],tb=triangles[b.i];
 for(const ai of [a.k,(a.k+1)%3]) {
  const bi=[b.k,(b.k+1)%3].find(j=>same(ta.targetUv[ai],tb.targetUv[j]));
  if(bi===undefined||ATTRIBUTES.some(name=>!same(ta[name][ai],tb[name][bi])))fail(`chart ${id} discontinuous shared edge`);
 }
 if(!sameJacobian(ta,tb))fail(`chart ${id} incompatible affine UV-to-position mapping`);
 state.adjacency.get(a.i).add(b.i);state.adjacency.get(b.i).add(a.i);
}

// Breadth-first walk over adjacency; every chart triangle must be reached.
function checkConnected(state, id, fail){
 const {indices,adjacency}=state;
 const visited=new Set([indices[0]]),queue=[indices[0]];
 for(let k=0;k<queue.length;k++)for(const j of adjacency.get(queue[k]))if(!visited.has(j)){visited.add(j);queue.push(j)}
 if(visited.size!==indices.length)fail(`chart ${id} disconnected`);
}

function validateChart(triangles, id, indices, fail){
 const state=createChartState(indices);
 for(const i of indices)for(let k=0;k<3;k++)registerCorner(triangles,state,id,i,k,fail);
 checkTJunctions(triangles,state,id,fail);
 for(const entries of state.edgeCount.values())if(entries.length===2)checkSharedEdge(triangles,state,id,entries[0],entries[1],fail);
 checkConnected(state,id,fail);
}

export function validateChartTopology(triangles) {
  const fail=message=>{throw new Error(`UNSUPPORTED: ${message}`)};
  validateTriangleCount(triangles,fail);
  const groups=new Map();
  for(const [i,t] of triangles.entries()) {
    validateChartId(t,fail);
    validateAttributes(t,fail);
    validateUvRange(t,fail);
    addToGroup(groups,t.chartId,i);
  }
  for(const [id,indices] of groups)validateChart(triangles,id,indices,fail);
  return {triangles:triangles.length,charts:groups.size};
}
