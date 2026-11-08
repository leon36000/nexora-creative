"""Construct all Paint model components on CPU, offline, before any GPU run."""
import os, pathlib, sys, time, types
P=pathlib.Path(os.environ['MESH_PAINT_ROOT']).resolve(strict=True)
assert os.environ.get('TORCH_FORCE_WEIGHTS_ONLY_LOAD')=='1'
os.chdir(P/'source');sys.path.insert(0,str(P/'source/hy3dpaint'))
from utils.torchvision_fix import apply_fix
apply_fix()
import huggingface_hub
def local_snapshot(repo_id,**kwargs):
    if repo_id!='tencent/Hunyuan3D-2.1':raise RuntimeError('unexpected repo')
    return str(P/'model-source')
huggingface_hub.snapshot_download=local_snapshot
sys.modules['bpy']=types.ModuleType('bpy')
import custom_rasterizer, custom_rasterizer_kernel, xatlas
from DifferentiableRenderer import mesh_inpaint_processor
from textureGenPipeline import Hunyuan3DPaintConfig
from utils.image_super_utils import imageSuperNet
from utils.multiview_utils import multiviewDiffusionNet
c=Hunyuan3DPaintConfig(max_num_view=6,resolution=512);c.device='cpu'
c.dino_ckpt_path=str(P/'dinov2-giant')
c.realesrgan_ckpt_path=str(P/'source/hy3dpaint/ckpt/RealESRGAN_x4plus.pth')
t=time.monotonic();sr=imageSuperNet(c);print('SUPER_INIT_OK',flush=True)
model=multiviewDiffusionNet(c);print('MULTIVIEW_AND_DINO_INIT_OK',flush=True)
import torch
assert not torch.cuda.is_available()
print('FULL_MODEL_COMPONENTS_CPU_OK',round(time.monotonic()-t,2),flush=True)
