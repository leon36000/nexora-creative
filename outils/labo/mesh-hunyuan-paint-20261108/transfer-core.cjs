/* Research helper: match oriented triangles in world space and transfer source normals. */
'use strict';
const {createRequire}=require('node:module');
const {resolve}=require('node:path');
const requireApp=createRequire(resolve(__dirname,'../../../app/package.json'));
const {Matrix3,Matrix4,Vector3}=requireApp('three');

function validate(src,dst,epsilon,conflictTolerance){
  if(!Number.isFinite(epsilon)||epsilon<=0||!Number.isFinite(conflictTolerance)||conflictTolerance<=0){throw new Error('invalid tolerance');}
  for(const g of [src,dst]){
    if(g.positions.length%3||g.normals.length!==g.positions.length||g.matrix.length!==16){throw new Error('invalid attribute sizes');}
    if(!Array.from(g.positions).every(Number.isFinite)||!Array.from(g.matrix).every(Number.isFinite)){throw new Error('nonfinite geometry');}
    if(!Array.from(g.indices).every(i=>Number.isInteger(i)&&i>=0&&i<g.positions.length/3)){throw new Error('invalid index');}
  }
  if(src.indices.length!==dst.indices.length||src.indices.length%3!==0){throw new Error('triangle count mismatch');}
}
function triangle(g,at,m){
  return [0,1,2].map(k=>{const i=g.indices[at+k];return new Vector3(g.positions[3*i],g.positions[3*i+1],g.positions[3*i+2]).applyMatrix4(m).toArray();});
}
function cell(points,epsilon){
  const result=[0,1,2].map(i=>Math.floor(((points[0][i]+points[1][i]+points[2][i])/3)/epsilon));
  if(result.some(v=>!Number.isSafeInteger(v))){throw new Error('numeric range unsupported');}
  return result;
}
function buildBuckets(src,m,epsilon){
  const buckets=new Map();
  for(let at=0;at<src.indices.length;at+=3){
    const points=triangle(src,at,m),k=cell(points,epsilon).join(',');
    if(!buckets.has(k)){buckets.set(k,[]);}
    buckets.get(k).push({at,points,used:false});
  }
  return buckets;
}
function neighbourCells(c){
  const cells=[];
  for(let x=-1;x<=1;x++){
    for(let y=-1;y<=1;y++){
      for(let z=-1;z<=1;z++){
        cells.push([c[0]+x,c[1]+y,c[2]+z].join(','));
      }
    }
  }
  return cells;
}
function addBucketMatches(candidates,points,list,epsilon){
  for(const item of list){
    if(item.used){continue;}
    for(let rotation=0;rotation<3;rotation++){
      const errors=points.map((p,i)=>Math.hypot(...p.map((v,j)=>v-item.points[(i+rotation)%3][j])));
      const err=Math.max(...errors);if(err<=epsilon){candidates.push({item,rotation,err});}
    }
  }
}
function orientedMatches(points,c,buckets,epsilon){
  const candidates=[];
  for(const key of neighbourCells(c)){addBucketMatches(candidates,points,buckets.get(key)??[],epsilon);}
  return candidates;
}
function assignCorner(state,si,di){
  const n=new Vector3(state.src.normals[3*si],state.src.normals[3*si+1],state.src.normals[3*si+2]);
  if(!Number.isFinite(n.x)||!Number.isFinite(n.y)||!Number.isFinite(n.z)){throw new Error('nonfinite source normal');}
  if(n.lengthSq()===0){state.undefinedCorners++;state.undefinedVertices.add(di);return;}
  n.applyNormalMatrix(state.srcNormalMatrix).applyMatrix3(state.dstWorldToLocal).normalize();
  if(!Number.isFinite(n.x)||!Number.isFinite(n.y)||!Number.isFinite(n.z)||n.lengthSq()===0){throw new Error('invalid transformed normal');}
  const old=state.assigned.get(di);
  if(old&&new Vector3(...old).distanceTo(n)>state.conflictTolerance){throw new Error(`conflicting source normals at destination vertex ${di}`);}
  if(!old){state.assigned.set(di,n.toArray());}
}
function finish(state,result){
  for(const di of state.undefinedVertices){if(state.assigned.has(di)){throw new Error(`mixed defined and undefined source normals at vertex ${di}`);}}
  for(const [i,n] of state.assigned){result.set(n,3*i);}
  for(const i of state.undefinedVertices){
    const n=new Vector3(result[3*i],result[3*i+1],result[3*i+2]);
    if(!Number.isFinite(n.x)||!Number.isFinite(n.y)||!Number.isFinite(n.z)||n.lengthSq()===0){throw new Error('undefined source fallback normal invalid');}
  }
}
function transfer(src,dst,epsilon=1e-6,conflictTolerance=1e-4){
  validate(src,dst,epsilon,conflictTolerance);
  const srcM=new Matrix4().fromArray(src.matrix),dstM=new Matrix4().fromArray(dst.matrix);
  if(Math.abs(srcM.determinant())<1e-15||Math.abs(dstM.determinant())<1e-15){throw new Error('singular transform');}
  const state={src,conflictTolerance,srcNormalMatrix:new Matrix3().getNormalMatrix(srcM),dstWorldToLocal:new Matrix3().setFromMatrix4(dstM).transpose(),assigned:new Map(),undefinedVertices:new Set(),undefinedCorners:0};
  const buckets=buildBuckets(src,srcM,epsilon),result=Float32Array.from(dst.normals);
  let maxPositionError=0,matched=0;
  for(let at=0;at<dst.indices.length;at+=3){
    const points=triangle(dst,at,dstM),c=cell(points,epsilon),candidates=orientedMatches(points,c,buckets,epsilon);
    if(candidates.length!==1){throw new Error(`triangle ${at/3}: ${candidates.length} oriented matches`);}
    const {item,rotation,err}=candidates[0];item.used=true;matched++;maxPositionError=Math.max(maxPositionError,err);
    for(let i=0;i<3;i++){assignCorner(state,src.indices[item.at+(i+rotation)%3],dst.indices[at+i]);}
  }
  finish(state,result);
  return {normals:result,stats:{triangles:matched,maxPositionError,assignedVertices:state.assigned.size,undefinedCorners:state.undefinedCorners,undefinedVertices:state.undefinedVertices.size,undefinedPolicy:'retain destination normals for wholly undefined source vertices',epsilon,conflictTolerance}};
}
module.exports={transfer};
