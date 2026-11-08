#!/usr/bin/env node
'use strict';
const fs=require('node:fs/promises'),crypto=require('node:crypto'),path=require('node:path'),{createRequire}=require('node:module');
const app=createRequire(path.resolve(__dirname,'../../../app/package.json'));
const {NodeIO}=app('@gltf-transform/core'),{ALL_EXTENSIONS}=app('@gltf-transform/extensions');
const {transfer}=require('./transfer-core.cjs');
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
function glbJSON(bytes){
 if(bytes.length<20||bytes.toString('ascii',0,4)!=='glTF'||bytes.readUInt32LE(4)!==2||bytes.readUInt32LE(8)!==bytes.length||bytes.toString('ascii',16,20)!=='JSON')throw new Error('invalid GLB');
 const length=bytes.readUInt32LE(12);if(20+length>bytes.length)throw new Error('invalid JSON chunk');
 return JSON.parse(bytes.toString('utf8',20,20+length));
}
function compareKeys(a,b){if(a<b){return -1;}if(a>b){return 1;}return 0;}
function canonical(x){
 if(Array.isArray(x)){return x.map(canonical);}
 if(x&&typeof x==='object'){return Object.fromEntries(Object.keys(x).sort(compareKeys).map(k=>[k,canonical(x[k])]));}
 return x;
}
function primitive(doc){
 const root=doc.getRoot();if(root.listAnimations().length||root.listSkins().length||root.listScenes().length!==1)throw new Error('one static scene required');
 const nodes=root.listNodes().filter(n=>n.getMesh());if(nodes.length!==1)throw new Error('one mesh node required');
 const ps=nodes[0].getMesh().listPrimitives();if(ps.length!==1||ps[0].getMode()!==4||ps[0].listTargets().length)throw new Error('one static triangle primitive required');
 const p=ps[0],position=p.getAttribute('POSITION'),normal=p.getAttribute('NORMAL'),indices=p.getIndices();if(!position||!normal||!indices)throw new Error('POSITION, NORMAL and indices required');
 if(position.getComponentType()!==5126||normal.getComponentType()!==5126||position.getNormalized()||normal.getNormalized())throw new Error('POSITION and NORMAL must be non-normalized Float32');
 const attrs={};for(const semantic of p.listSemantics()){if(semantic!=='NORMAL'){attrs[semantic]=Array.from(p.getAttribute(semantic).getArray());}}
 return {positions:position.getArray(),normals:normal.getArray(),indices:indices.getArray(),matrix:nodes[0].getWorldMatrix(),accessor:normal,attrs};
}
function imageHashes(doc){return doc.getRoot().listTextures().map(t=>{const b=t.getImage();if(!b)throw new Error('external or missing image unsupported');return hash(b)});}
async function absent(file){try{await fs.lstat(file);throw new Error('output exists: '+file)}catch(e){if(e.code!=='ENOENT')throw e}}
async function main(){
 const [sourcePath,targetPath,outputPath,reportPath,...extra]=process.argv.slice(2);
 if(!sourcePath||!targetPath||!outputPath||!reportPath||extra.length||path.resolve(outputPath)===path.resolve(reportPath))throw new Error('usage: node transfer-glb.cjs source.glb paint.glb output.glb report.json');
 await absent(outputPath);await absent(reportPath);
 const [a,b]=await Promise.all([fs.readFile(sourcePath),fs.readFile(targetPath)]),sourceJSON=glbJSON(a),targetJSON=glbJSON(b);
 for(const doc of [sourceJSON,targetJSON]){if((doc.extensionsUsed||[]).includes('EXT_mesh_gpu_instancing')||(doc.nodes||[]).some(n=>n.extensions?.EXT_mesh_gpu_instancing)){throw new Error('EXT_mesh_gpu_instancing unsupported');}}
 const supported=new Set(ALL_EXTENSIONS.map(e=>e.EXTENSION_NAME));
 for(const name of targetJSON.extensionsUsed||[]){if(!supported.has(name)){throw new Error('unsupported target extension: '+name);}}
 const io=new NodeIO().registerExtensions(ALL_EXTENSIONS),source=await io.readBinary(a),target=await io.readBinary(b);
 const originalTextures=imageHashes(target),s=primitive(source),t=primitive(target),r=transfer(s,t);t.accessor.setArray(r.normals);
 const bytes=await io.writeBinary(target),roundtrip=await io.readBinary(bytes),rprim=primitive(roundtrip),outJSON=glbJSON(Buffer.from(bytes));
 if(JSON.stringify(originalTextures)!==JSON.stringify(imageHashes(roundtrip)))throw new Error('texture bytes changed');
 if(JSON.stringify(canonical(targetJSON.materials||[]))!==JSON.stringify(canonical(outJSON.materials||[])))throw new Error('material serialization changed');
 if(JSON.stringify(canonical(t.attrs))!==JSON.stringify(canonical(rprim.attrs))||JSON.stringify(Array.from(t.indices))!==JSON.stringify(Array.from(rprim.indices))||JSON.stringify(Array.from(t.matrix))!==JSON.stringify(Array.from(rprim.matrix)))throw new Error('geometry or non-normal attributes changed');
 const report={sourceSha256:hash(a),targetSha256:hash(b),outputSha256:hash(bytes),textureSha256:originalTextures,stats:r.stats,scope:'one static triangle primitive; source zero-normal vertices retain destination normal; no GPU'};
 await fs.writeFile(outputPath,bytes,{flag:'wx'});await fs.writeFile(reportPath,JSON.stringify(report,null,2)+'\n',{flag:'wx'});console.log(JSON.stringify(report));
}
main().catch(e=>{console.error(e.message);process.exitCode=1});
