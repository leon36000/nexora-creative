/** Métriques descriptives sur pixels RGBA octets et masques silhouette binaires. */
export function comparePixels(maskA,maskB,rgbA,rgbB,width,height){
 if(!Number.isSafeInteger(width)||width<=0||!Number.isSafeInteger(height)||height<=0||width*height>16777216)throw new Error('dimensions invalides');
 const n=width*height;
 for(const v of [maskA,maskB,rgbA,rgbB])if(!(v instanceof Uint8Array)||v.length!==4*n)throw new Error('pixels RGBA invalides');
 let intersection=0,union=0,sum=0,max=0,aCount=0,bCount=0;
 for(let i=0;i<n;i++){
  const offset=i*4,a=maskA[offset]>127,b=maskB[offset]>127;
  if(a)aCount++;if(b)bCount++;if(a||b)union++;
  if(a&&b){intersection++;for(let c=0;c<3;c++){const d=Math.abs(rgbA[offset+c]-rgbB[offset+c]);sum+=d;max=Math.max(max,d)}}
 }
 return {width,height,silhouette_a_pixels:aCount,silhouette_b_pixels:bCount,intersection_pixels:intersection,union_pixels:union,iou:union?intersection/union:null,rgb_mae_0_255:intersection?sum/(3*intersection):null,rgb_max_0_255:intersection?max:null};
}
