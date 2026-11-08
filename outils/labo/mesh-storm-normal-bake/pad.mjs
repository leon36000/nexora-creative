/** Experimental iterative chart padding. Ownership must be supplied and validated by the caller. */
export function padNormalCharts({pixels, owners, width, height, radius}) {
  const fail = reason => { throw new Error(`UNSUPPORTED: ${reason}`); };
  if (!Number.isInteger(width)||!Number.isInteger(height)||width<1||height<1||width*height>1048576) fail('invalid dimensions');
  if (!Number.isInteger(radius)||radius<1||radius>8) fail('radius must be between 1 and 8');
  if (!(pixels instanceof Uint8Array)||pixels.length!==width*height*3||!(owners instanceof Uint16Array)||owners.length!==width*height) fail('invalid RGB or chart ownership data');
  if (!owners.some(x=>x!==0)) fail('no owned pixels');
  const output=pixels.slice(), labels=owners.slice();
  const assertSeparated = () => {
    for(let y=0;y<height;y++) for(let x=0;x<width;x++) {
      const label=labels[y*width+x];if(!label)continue;
      for(let dy=-1;dy<=1;dy++)for(let dx=-1;dx<=1;dx++) {
        if(!dx&&!dy)continue;const nx=x+dx,ny=y+dy;
        if(nx<0||nx>=width||ny<0||ny>=height)continue;
        const other=labels[ny*width+nx];if(other&&other!==label)fail('padding would mix distinct charts');
      }
    }
  };
  let padded=0;
  for(let step=0;step<radius;step++) {
    assertSeparated();
    const pending=[];
    for(let y=0;y<height;y++)for(let x=0;x<width;x++) {
      const i=y*width+x;
      if(labels[i]!==0) continue;
      let found=0, source=-1;
      for(let dy=-1;dy<=1;dy++)for(let dx=-1;dx<=1;dx++) {
        if(!dx&&!dy) continue;
        const nx=x+dx,ny=y+dy;if(nx<0||nx>=width||ny<0||ny>=height) continue;
        const j=ny*width+nx, label=labels[j];if(!label)continue;
        if(found&&found!==label) fail('padding would mix distinct charts');
        if(!found){found=label;source=j;}
      }
      if(found) pending.push([i,found,source]);
    }
    for(const [i,label,source] of pending) {labels[i]=label;output.set(output.subarray(source*3,source*3+3),i*3);padded++;}
  }
  assertSeparated();
  return {pixels:output,owners:labels,padded};
}
