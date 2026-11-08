/** Experimental per-sample GLTF-to-Storm tangent-frame conversion; object-space triangle only. */
const EPS = 1e-10;
const dot = (a, b) => a[0]*b[0] + a[1]*b[1] + a[2]*b[2];
const add = (a, b) => a.map((v, i) => v+b[i]);
const mul = (a, s) => a.map(v => v*s);
const cross = (a,b) => [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]];
function unit(a, label) {
  const n = Math.hypot(...a);
  if (!Number.isFinite(n) || n < EPS) throw new Error(`UNSUPPORTED: ${label} is degenerate`);
  return mul(a,1/n);
}
function vectors(v, count, size, label) {
  if (!Array.isArray(v) || v.length !== count || v.some(x => !Array.isArray(x) || x.length !== size || x.some(n => !Number.isFinite(n))))
    throw new Error(`UNSUPPORTED: invalid ${label}`);
}
function interp(v, weights) { return v.reduce((a,x,i)=>add(a,mul(x,weights[i])),[0,0,0]); }
function solve(cols, world) {
  const [a,b,c] = cols, bc = cross(b,c), ca = cross(c,a), ab = cross(a,b);
  const det = dot(a,bc);
  if (!Number.isFinite(det) || Math.abs(det) < 1e-6) throw new Error('UNSUPPORTED: singular target frame');
  return unit([dot(world,bc)/det, dot(world,ca)/det, dot(world,ab)/det], 'target normal');
}
/**
 * Input attributes are triangle-corner arrays in the same object space. uv is the GLTF normal
 * map UV before USD conversion; USD st=(u,1-v). rawNormal is one already-sampled LINEAR texel.
 * No skinning, scene transform, texture sampling, filtering, atlas or whole-mesh validation here.
 */
export function reprojectNormal({positions, normals, tangents, uv, barycentric, rawNormal, normalScale=1}) {
  vectors(positions,3,3,'positions'); vectors(normals,3,3,'normals'); vectors(tangents,3,4,'tangents'); vectors(uv,3,2,'UV');
  if (!Array.isArray(barycentric) || barycentric.length!==3 || barycentric.some(v=>!Number.isFinite(v)||v<0||v>1) || Math.abs(barycentric.reduce((a,b)=>a+b,0)-1)>1e-7) throw new Error('UNSUPPORTED: invalid barycentric coordinates');
  if (!Array.isArray(rawNormal) || rawNormal.length!==3 || rawNormal.some(v=>!Number.isFinite(v)||v<0||v>1) || !Number.isFinite(normalScale) || normalScale<0) throw new Error('UNSUPPORTED: invalid normal texture sample');
  const w=tangents.map(t=>t[3]);
  if (!w.every(x=>x===1||x===-1) || !w.every(x=>x===w[0])) throw new Error('UNSUPPORTED: mixed or invalid tangent handedness');
  const ns=normals.map(n=>unit(n,'normal'));
  const ts=tangents.map((t,i)=>{ const q=unit(t.slice(0,3),'tangent'); if(Math.abs(dot(q,ns[i]))>1e-4) throw new Error('UNSUPPORTED: non-orthogonal input tangent'); return q; });
  // Three r186 interpolates per-vertex normalized T, B and N separately, then normalizes each.
  const bs=ts.map((t,i)=>unit(mul(cross(ns[i],t),w[i]),'bitangent'));
  const N=unit(interp(ns,barycentric),'interpolated normal');
  const T=unit(interp(ts,barycentric),'interpolated tangent');
  const B=unit(interp(bs,barycentric),'interpolated bitangent');
  const sampled=unit([(rawNormal[0]*2-1)*normalScale,(rawNormal[1]*2-1)*normalScale,rawNormal[2]*2-1],'texture normal');
  const world=unit(add(add(mul(T,sampled[0]),mul(B,sampled[1])),mul(N,sampled[2])),'source world normal');
  // Same local derivatives as OpenUSD 26.03 ComputeTBNMatrix; affine barycentric screen basis.
  const dx=add(positions[1],mul(positions[0],-1)), dy=add(positions[2],mul(positions[0],-1));
  if (Math.hypot(...cross(dx,dy)) < EPS) throw new Error('UNSUPPORTED: degenerate geometry');
  const sx=add(dx,mul(N,-dot(dx,N))), sy=add(dy,mul(N,-dot(dy,N)));
  const st=uv.map(([u,v])=>[u,1-v]);
  const dxst=[st[1][0]-st[0][0],st[1][1]-st[0][1]], dyst=[st[2][0]-st[0][0],st[2][1]-st[0][1]];
  const det=dxst[0]*dyst[1]-dxst[1]*dyst[0];
  if (!Number.isFinite(det)||Math.abs(det)<1e-10) throw new Error('UNSUPPORTED: degenerate UV');
  const orientation=dot(dy,cross(N,dx));
  if (Math.abs(orientation) < EPS*Math.hypot(...cross(dx,dy))) throw new Error('UNSUPPORTED: unstable normal orientation');
  const handed=det<0?-1:1, flip=orientation<0?-1:1;
  const stormT=unit(add(mul(sx,handed*dyst[1]),mul(sy,-handed*dxst[1])),'Storm tangent');
  const stormB=mul(cross(N,stormT),handed*flip);
  const target=solve([stormT,stormB,N],world);
  return {targetNormal:target, sourceWorldNormal:world, stormTangent:stormT, stormBitangent:stormB, stormNormal:N};
}
