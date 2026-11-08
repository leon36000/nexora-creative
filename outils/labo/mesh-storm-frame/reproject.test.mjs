import test from 'node:test';
import assert from 'node:assert/strict';
import {reprojectNormal} from './reproject.mjs';
const unit=v=>{const n=Math.hypot(...v);return v.map(x=>x/n)};
const dot=(a,b)=>a.reduce((s,x,i)=>s+x*b[i],0);
const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
const angle=(a,b)=>Math.acos(Math.max(-1,Math.min(1,dot(unit(a),unit(b)))))*180/Math.PI;
function fixture(mirror=false,rotation=0){
  const normals=[[0,0,1],[.2,0,1],[0,.2,1]].map(unit);
  const tangents=normals.map(n=>{const p=unit([1-n[0]*n[0],-n[0]*n[1],-n[0]*n[2]]),q=cross(n,p),theta=rotation*Math.PI/180;
    const t=p.map((v,i)=>(mirror?-1:1)*(v*Math.cos(theta)+q[i]*Math.sin(theta)));return [...t,mirror?-1:1]});
  return {positions:[[0,0,0],[1,0,0],[0,1,0]],normals,tangents,uv:mirror?[[1,0],[0,0],[1,1]]:[[0,0],[1,0],[0,1]],barycentric:[.2,.3,.5],rawNormal:[.69,.365,.94],normalScale:1};
}
function worldFromTarget(o,normal){return unit(o.stormTangent.map((x,i)=>x*normal[0]+o.stormBitangent[i]*normal[1]+o.stormNormal[i]*normal[2]))}
for(const mirror of [false,true])for(const rotation of [0,30])test(`reconstructs world for mirror=${mirror}, tangent rotation=${rotation}`,()=>{
  const f=fixture(mirror,rotation),out=reprojectNormal(f);assert.ok(angle(worldFromTarget(out,out.targetNormal),out.sourceWorldNormal)<1e-5);
  const sampled=unit(f.rawNormal.map(x=>2*x-1)),flip=[sampled[0],-sampled[1],sampled[2]],err=angle(worldFromTarget(out,flip),out.sourceWorldNormal);
  if(rotation===30) assert.ok(err>10,`rotation must expose global Y flip error; got ${err}`); else assert.ok(err<.2,`aligned case ${err}`);
});
test('normalScale zero removes XY texture perturbation',()=>{const f=fixture();f.normalScale=0;const o=reprojectNormal(f);assert.ok(angle(o.sourceWorldNormal,o.stormNormal)<1e-5)});
test('rejects mixed w',()=>{const f=fixture();f.tangents[1][3]=-1;assert.throws(()=>reprojectNormal(f),/mixed/)});
test('rejects degenerate UV and geometry',()=>{const f=fixture();f.uv[2]=f.uv[1];assert.throws(()=>reprojectNormal(f),/degenerate UV/);const g=fixture();g.positions[2]=g.positions[1];assert.throws(()=>reprojectNormal(g),/degenerate geometry/)});
test('rejects invalid data and non-orthogonal tangents',()=>{const f=fixture();f.rawNormal[0]=NaN;assert.throws(()=>reprojectNormal(f),/invalid normal/);const g=fixture();g.tangents[0]=[0,0,1,1];assert.throws(()=>reprojectNormal(g),/non-orthogonal/)});
test('matches independent fixed-frame numerical oracle for rotated tangent and mirrored UV',()=>{
  const n=unit([.23,-.17,1]),base=unit([1-n[0]*n[0],-n[0]*n[1],-n[0]*n[2]]),side=cross(n,base),c=Math.cos(Math.PI/6),s=Math.sin(Math.PI/6);
  for(const mirror of [false,true]){
    const f=fixture(mirror);f.normals=[n,n,n];const t=base.map((x,i)=>(mirror?-1:1)*(x*c+side[i]*s));f.tangents=Array.from({length:3},()=>[...t,mirror?-1:1]);
    const expected=mirror?[.1949001744978095,.4255967658088335,.8836748920919868]:[.46602769820785084,.04400988058729373,.8836748920919868];
    assert.ok(angle(reprojectNormal(f).targetNormal,expected)<1e-5);
  }
});

test('rejects normals tangent to the face where Storm orientation is unstable',()=>{
  const f=fixture();f.normals=[[1,0,0],[1,0,0],[1,0,0]];f.tangents=[[0,1,0,1],[0,1,0,1],[0,1,0,1]];
  assert.throws(()=>reprojectNormal(f),/unstable normal orientation/);
});
test('accepts non-orthogonal interpolated N/T when each source vertex is orthogonal',()=>{
  const f=fixture(),interp=arr=>unit([0,1,2].map(j=>arr.reduce((sum,v,i)=>sum+v[j]*f.barycentric[i],0)));
  const ni=interp(f.normals),ti=interp(f.tangents.map(t=>t.slice(0,3)));
  assert.ok(Math.abs(dot(ni,ti))>1e-4,'fixture must exercise non-orthogonal interpolated frame');
  const o=reprojectNormal(f);assert.ok(angle(worldFromTarget(o,o.targetNormal),o.sourceWorldNormal)<1e-5);
});
test('rejects missing, out-of-range and zero-vector samples',()=>{
  for (const raw of [[.5,.5,.5],[1.01,.5,.5],[.5,.5,Infinity]]) { const f=fixture(); f.rawNormal=raw; assert.throws(()=>reprojectNormal(f),/UNSUPPORTED/); }
});
test('rejects invalid barycentrics and non-unit handedness',()=>{
  const f=fixture();f.barycentric=[.2,.3,.6];assert.throws(()=>reprojectNormal(f),/barycentric/);
  const g=fixture();g.tangents[0][3]=0;assert.throws(()=>reprojectNormal(g),/handedness/);
});
