/* Research helper: match oriented triangles in world space and transfer source normals. */
'use strict';
const {createRequire}=require('node:module');
const {resolve}=require('node:path');
const requireApp=createRequire(resolve(__dirname,'../../../app/package.json'));
const {Matrix3,Matrix4,Vector3}=requireApp('three');

function transfer(src,dst,epsilon=1e-6,conflictTolerance=1e-4){
  if(!Number.isFinite(epsilon)||epsilon<=0||!Number.isFinite(conflictTolerance)||conflictTolerance<=0)throw new Error('invalid tolerance');
  for(const g of [src,dst]){
    if(g.positions.length%3||g.normals.length!==g.positions.length||g.matrix.length!==16)throw new Error('invalid attribute sizes');
    if(!Array.from(g.positions).every(Number.isFinite)||!Array.from(g.matrix).every(Number.isFinite))throw new Error('nonfinite geometry');
    if(!Array.from(g.indices).every(i=>Number.isInteger(i)&&i>=0&&i<g.positions.length/3))throw new Error('invalid index');
  }
  if(src.indices.length!==dst.indices.length||src.indices.length%3!==0)throw new Error('triangle count mismatch');
  const srcM=new Matrix4().fromArray(src.matrix), dstM=new Matrix4().fromArray(dst.matrix);
  if(Math.abs(srcM.determinant())<1e-15||Math.abs(dstM.determinant())<1e-15)throw new Error('singular transform');
  const srcNormalMatrix=new Matrix3().getNormalMatrix(srcM), dstWorldToLocal=new Matrix3().setFromMatrix4(dstM).transpose();
  const point=(arr,i,m)=>new Vector3(arr[3*i],arr[3*i+1],arr[3*i+2]).applyMatrix4(m).toArray();
  const getTriangle=(g,at,m)=>[0,1,2].map(k=>point(g.positions,g.indices[at+k],m));
  const centroid=tri=>[0,1,2].map(i=>(tri[0][i]+tri[1][i]+tri[2][i])/3);
  const cell=tri=>centroid(tri).map(v=>Math.floor(v/epsilon));
  const key=a=>a.join(',');
  const buckets=new Map();
  for(let at=0;at<src.indices.length;at+=3){
    const points=getTriangle(src,at,srcM), c=cell(points);
    if(c.some(v=>!Number.isSafeInteger(v)))throw new Error('numeric range unsupported');
    const k=key(c);if(!buckets.has(k))buckets.set(k,[]);buckets.get(k).push({at,points,used:false});
  }
  const result=Float32Array.from(dst.normals),assigned=new Map(), undefinedVertices=new Set();
  let maxPositionError=0,undefinedCorners=0,matched=0;
  for(let at=0;at<dst.indices.length;at+=3){
    const points=getTriangle(dst,at,dstM), c=cell(points), candidates=[];
    if(c.some(v=>!Number.isSafeInteger(v)))throw new Error('numeric range unsupported');
    for(let x=-1;x<=1;x++)for(let y=-1;y<=1;y++)for(let z=-1;z<=1;z++){
      const list=buckets.get(key([c[0]+x,c[1]+y,c[2]+z]))||[];
      for(const item of list){if(item.used)continue;
        for(let rotation=0;rotation<3;rotation++){
          const errors=points.map((p,i)=>Math.hypot(...p.map((v,j)=>v-item.points[(i+rotation)%3][j])));
          const err=Math.max(...errors);if(err<=epsilon)candidates.push({item,rotation,err});
        }
      }
    }
    if(candidates.length!==1)throw new Error(`triangle ${at/3}: ${candidates.length} oriented matches`);
    const {item,rotation,err}=candidates[0];item.used=true;matched++;maxPositionError=Math.max(maxPositionError,err);
    for(let i=0;i<3;i++){
      const si=src.indices[item.at+(i+rotation)%3],di=dst.indices[at+i];
      const n=new Vector3(src.normals[3*si],src.normals[3*si+1],src.normals[3*si+2]);
      if(!Number.isFinite(n.x)||!Number.isFinite(n.y)||!Number.isFinite(n.z))throw new Error('nonfinite source normal');
      if(n.lengthSq()===0){undefinedCorners++;undefinedVertices.add(di);continue;}
      n.applyNormalMatrix(srcNormalMatrix).applyMatrix3(dstWorldToLocal).normalize();
      if(!Number.isFinite(n.x)||!Number.isFinite(n.y)||!Number.isFinite(n.z)||n.lengthSq()===0)throw new Error('invalid transformed normal');
      const old=assigned.get(di);
      if(old&&new Vector3(...old).distanceTo(n)>conflictTolerance)throw new Error(`conflicting source normals at destination vertex ${di}`);
      if(!old)assigned.set(di,n.toArray());
    }
  }
  for(const di of undefinedVertices)if(assigned.has(di))throw new Error(`mixed defined and undefined source normals at vertex ${di}`);
  for(const [i,n] of assigned)result.set(n,3*i);
  for(const i of undefinedVertices){const n=new Vector3(result[3*i],result[3*i+1],result[3*i+2]);if(!Number.isFinite(n.x)||!Number.isFinite(n.y)||!Number.isFinite(n.z)||n.lengthSq()===0)throw new Error('undefined source fallback normal invalid');}
  return {normals:result,stats:{triangles:matched,maxPositionError,assignedVertices:assigned.size,undefinedCorners,undefinedVertices:undefinedVertices.size,undefinedPolicy:'retain destination normals for wholly undefined source vertices',epsilon,conflictTolerance}};
}
module.exports={transfer};
