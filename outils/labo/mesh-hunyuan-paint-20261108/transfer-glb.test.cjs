'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),path=require('node:path'),os=require('node:os'),fs=require('node:fs/promises'),{spawnSync}=require('node:child_process'),{createRequire}=require('node:module');
const app=createRequire(path.resolve(__dirname,'../../../app/package.json'));
const {Document,NodeIO}=app('@gltf-transform/core'),{ALL_EXTENSIONS,KHRMaterialsSpecular,KHRMeshQuantization,EXTMeshGPUInstancing}=app('@gltf-transform/extensions');
const png=Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=','base64');
const io=new NodeIO().registerExtensions(ALL_EXTENSIONS);
function fixture(normal,mode='float'){
 const d=new Document(),buffer=d.createBuffer(),position=d.createAccessor().setType('VEC3').setArray(mode==='position' ? new Uint16Array([0,0,0,1,0,0,0,1,0]) : new Float32Array([0,0,0,1,0,0,0,1,0])).setBuffer(buffer),normals=d.createAccessor().setType('VEC3').setArray(mode==='normal' ? new Int8Array(normal) : new Float32Array(normal)).setBuffer(buffer),indices=d.createAccessor().setType('SCALAR').setArray(new Uint16Array([0,1,2])).setBuffer(buffer);
 if(mode==='position'||mode==='normal'){d.createExtension(KHRMeshQuantization).setRequired(true);(mode==='position'?position:normals).setNormalized(true)}
 const tex=d.createTexture().setMimeType('image/png').setImage(png),mat=d.createMaterial().setBaseColorTexture(tex),ext=d.createExtension(KHRMaterialsSpecular).createSpecular().setSpecularColorFactor([2,2,2]);mat.setExtension('KHR_materials_specular',ext);
 const prim=d.createPrimitive().setAttribute('POSITION',position).setAttribute('NORMAL',normals).setIndices(indices).setMaterial(mat),node=d.createNode().setMesh(d.createMesh().addPrimitive(prim));
 if(mode==='instance'){const trans=d.createAccessor().setType('VEC3').setArray(new Float32Array([0,0,0])).setBuffer(buffer);node.setExtension('EXT_mesh_gpu_instancing',d.createExtension(EXTMeshGPUInstancing).createInstancedMesh().setAttribute('TRANSLATION',trans))}
 d.createScene().addChild(node);return d;
}
test('CLI transfers normals and preserves image and specular material without overwriting',async()=>{
 const dir=await fs.mkdtemp(path.join(os.tmpdir(),'nexora-paint-test-')),src=path.join(dir,'src.glb'),dst=path.join(dir,'dst.glb'),out=path.join(dir,'out.glb'),report=path.join(dir,'report.json');
 await fs.writeFile(src,await io.writeBinary(fixture([0,0,1,0,0,1,0,0,1])));await fs.writeFile(dst,await io.writeBinary(fixture([1,0,0,1,0,0,1,0,0])));
 const run=()=>spawnSync(process.execPath,[path.join(__dirname,'transfer-glb.cjs'),src,dst,out,report],{encoding:'utf8'});
 const first=run();assert.equal(first.status,0,first.stderr);const bytes=await fs.readFile(out),doc=await io.readBinary(bytes),root=doc.getRoot();
 assert.deepEqual(Array.from(root.listMeshes()[0].listPrimitives()[0].getAttribute('NORMAL').getArray()),[0,0,1,0,0,1,0,0,1]);
 assert.deepEqual(Buffer.from(root.listTextures()[0].getImage()),png);assert.deepEqual(root.listMaterials()[0].getExtension('KHR_materials_specular').getSpecularColorFactor(),[2,2,2]);
 assert.equal(JSON.parse(await fs.readFile(report,'utf8')).stats.undefinedCorners,0);assert.notEqual(run().status,0);assert.deepEqual(await fs.readFile(out),bytes);
});
test('CLI rejects GPU instancing before creating outputs',async()=>{
 const dir=await fs.mkdtemp(path.join(os.tmpdir(),'nexora-paint-instance-')),src=path.join(dir,'src.glb'),dst=path.join(dir,'dst.glb'),out=path.join(dir,'out.glb'),report=path.join(dir,'report.json');
 await fs.writeFile(src,await io.writeBinary(fixture([0,0,1,0,0,1,0,0,1])));await fs.writeFile(dst,await io.writeBinary(fixture([0,0,1,0,0,1,0,0,1],'instance')));
 const result=spawnSync(process.execPath,[path.join(__dirname,'transfer-glb.cjs'),src,dst,out,report],{encoding:'utf8'});assert.notEqual(result.status,0);assert.match(result.stderr,/EXT_mesh_gpu_instancing unsupported/);await assert.rejects(fs.access(out));
});
test('CLI rejects normalized integer positions and normals before creating outputs',async()=>{
 for(const mode of ['position','normal']){
  const dir=await fs.mkdtemp(path.join(os.tmpdir(),'nexora-paint-quantized-')),src=path.join(dir,'src.glb'),dst=path.join(dir,'dst.glb'),out=path.join(dir,'out.glb'),report=path.join(dir,'report.json');
  await fs.writeFile(src,await io.writeBinary(fixture([0,0,1,0,0,1,0,0,1],mode)));await fs.writeFile(dst,await io.writeBinary(fixture([0,0,1,0,0,1,0,0,1])));
  const result=spawnSync(process.execPath,[path.join(__dirname,'transfer-glb.cjs'),src,dst,out,report],{encoding:'utf8'});assert.notEqual(result.status,0);assert.match(result.stderr,/non-normalized Float32/);await assert.rejects(fs.access(out));
 }
});
