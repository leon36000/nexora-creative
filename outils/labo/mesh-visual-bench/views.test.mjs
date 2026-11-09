import test from 'node:test';import assert from 'node:assert/strict';import {cameras} from './views.mjs';
test('quatre vues historiques inchangées et dessus non colinéaire',()=>{assert.deepEqual(Object.entries(cameras),[['front',[0,0,1]],['perspective',[1.4,.9,1.8]],['back',[0,0,-1]],['side',[1,0,0]],['top',[0,1,.001]]]);for(const v of Object.values(cameras))assert.ok(v[0]**2+v[2]**2>0)});
