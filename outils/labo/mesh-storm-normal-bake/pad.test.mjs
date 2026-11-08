import test from 'node:test';
import assert from 'node:assert/strict';
import {padNormalCharts} from './pad.mjs';
const make=(width,height)=>({width,height,pixels:new Uint8Array(width*height*3),owners:new Uint16Array(width*height),radius:1});
test('pads an isolated chart without modifying inputs',()=>{
 const a=make(5,5),i=2*5+2;a.owners[i]=7;a.pixels.set([42,128,233],i*3);const p=padNormalCharts(a);
 assert.equal(p.padded,8);assert.equal(p.owners.filter(Boolean).length,9);assert.deepEqual([...p.pixels.slice((i-1)*3,(i-1)*3+3)],[42,128,233]);assert.equal(a.owners.filter(Boolean).length,1);
});
test('refuses overlap of padding domains without mutating either chart',()=>{
 const a=make(5,3);a.owners[5]=1;a.owners[7]=2;const before=a.owners.slice();assert.throws(()=>padNormalCharts(a),/mix distinct charts/);assert.deepEqual(a.owners,before);
});
test('allows disjoint domains and copies each chart separately',()=>{
 const a=make(9,3);a.owners[9]=1;a.owners[17]=2;a.pixels.set([1,2,3],27);a.pixels.set([9,8,7],51);const p=padNormalCharts(a);
 assert.equal(p.owners[10],1);assert.equal(p.owners[16],2);assert.deepEqual([...p.pixels.slice(30,33)],[1,2,3]);assert.deepEqual([...p.pixels.slice(48,51)],[9,8,7]);
});
test('rejects invalid input and unsupported limits',()=>{
 assert.throws(()=>padNormalCharts(make(3,3)),/no owned/);const a=make(3,3);a.owners[0]=1;
 assert.throws(()=>padNormalCharts({...a,radius:9}),/radius/);assert.throws(()=>padNormalCharts({...a,pixels:new Uint8Array(1)}),/invalid RGB/);
});

test('rejects directly adjacent distinct chart owners',()=>{
 const a=make(4,3);a.owners[5]=1;a.owners[6]=2;assert.throws(()=>padNormalCharts(a),/mix distinct charts/);
});
test('rejects padding domains that become adjacent after expansion',()=>{
 const a=make(4,3);a.owners[4]=1;a.owners[7]=2;assert.throws(()=>padNormalCharts(a),/mix distinct charts/);
});
