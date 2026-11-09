#!/usr/bin/env python3
"""Smoke 7x7 utilisant réellement l'OpenCV déjà présent dans le job CI."""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile
import cv2
import numpy as np
import bench_inpaint as bench


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--opencv-version',required=True)
    args=parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='mesh-inpaint-smoke-') as tmp:
        root=Path(tmp)
        color=np.array([63,127,191],dtype=np.float32)/255
        texture=np.broadcast_to(color,(7,7,3)).copy()
        texture[3,3]=0
        mask=np.full((7,7),255,dtype=np.uint8)
        mask[3,3]=0
        np.save(root/'texture.npy',texture,allow_pickle=False)
        np.save(root/'mask.npy',mask,allow_pickle=False)
        receipt=bench.run(root/'texture.npy',root/'mask.npy',root/'result',args.opencv_version,Path(cv2.__file__).resolve().parent)
        result=np.load(root/'result/output.npy',allow_pickle=False)
        source=(texture*255).astype(np.uint8)
        if result.shape!=(7,7,3) or result.dtype!=np.uint8:
            raise AssertionError('unexpected smoke output shape or dtype')
        if not np.array_equal(result[mask!=0],source[mask!=0]):
            raise AssertionError('known pixels changed')
        if np.max(np.abs(result[3,3].astype(np.int16)-source[0,0].astype(np.int16)))>1:
            raise AssertionError('central hole was not filled with surrounding color')
        expected_source=hashlib.sha256(source.tobytes()).hexdigest()
        expected_mask=hashlib.sha256((255-mask).tobytes()).hexdigest()
        if receipt['arguments']['source_uint8_raw_sha256']!=expected_source or receipt['arguments']['inpaint_mask_raw_sha256']!=expected_mask:
            raise AssertionError('argument hashes do not match')
        stored=json.loads((root/'result/receipt.json').read_text(encoding='utf-8'))
        if stored!=receipt or stored['opencv']['version']!=args.opencv_version:
            raise AssertionError('receipt mismatch')
        print(json.dumps({'smoke':'passed','opencv':stored['opencv']['version'],'module':stored['opencv']['module_path'],'numpy':np.__version__}))


if __name__=='__main__':
    main()
