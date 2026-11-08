import ctypes
import ctypes.util
import hashlib
import json
import math
import os
import sys
from pathlib import Path
from ctypes import c_void_p, c_int, c_uint, c_char_p, POINTER, byref

# Reject unsafe CLI paths before loading EGL or creating any graphics context.
code_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(code_dir))
from verify_inputs import validate_renderer_paths, validate_stage_name
if not os.environ.get('MESH_ORACLE_OUTPUT_DIR') or not os.environ.get('MESH_ORACLE_STAGE_DIR') or not os.environ.get('MESH_ORACLE_RUN_DIR'):
    raise SystemExit('Set explicit separate MESH_ORACLE_RUN_DIR, MESH_ORACLE_STAGE_DIR and MESH_ORACLE_OUTPUT_DIR.')
try:
    run_dir, stages_dir, out_dir, storage = validate_renderer_paths(
        Path(os.environ['MESH_ORACLE_RUN_DIR']),
        Path(os.environ['MESH_ORACLE_STAGE_DIR']),
        Path(os.environ['MESH_ORACLE_OUTPUT_DIR']),
        code_dir,
        Path(os.environ.get('MESH_ORACLE_STORAGE_ROOT', '/media/pc6/Storage/Nexora/travail')),
    )
except ValueError as error:
    raise SystemExit(f'Refusing unsafe renderer paths before EGL: {error}') from error
try:
    separator = sys.argv.index('--')
except ValueError:
    raise SystemExit('Missing -- separator before the stage basename.')
args = [arg for arg in sys.argv[separator + 1:] if arg != '--']
if len(args) != 1:
    raise SystemExit('Pass exactly one stage basename after --; use a fresh process for every stage.')
stage_name = args[0]
try:
    stage_path = validate_stage_name(stage_name, stages_dir)
except ValueError as error:
    raise SystemExit(f'Refusing unsafe stage name before EGL: {error}') from error
stem = stage_name.removesuffix('.usda').removesuffix('.usdz')
for candidate in (out_dir / f'{stem}.rgba', out_dir / f'{stem}.json'):
    if candidate.exists() or candidate.is_symlink():
        raise SystemExit(f'Refusing existing renderer output before EGL: {candidate}')

EGL = ctypes.CDLL(ctypes.util.find_library('EGL'))
EGL.eglGetProcAddress.argtypes = [c_char_p]
EGL.eglGetProcAddress.restype = c_void_p
addr = EGL.eglGetProcAddress(b'eglGetPlatformDisplayEXT')
if not addr:
    raise RuntimeError('eglGetPlatformDisplayEXT absent')
getdisplay = ctypes.CFUNCTYPE(c_void_p, c_uint, c_void_p, POINTER(c_int))(addr)
display = getdisplay(0x31DD, None, None)  # EGL_PLATFORM_SURFACELESS_MESA
EGL.eglInitialize.argtypes = [c_void_p, POINTER(c_int), POINTER(c_int)]
EGL.eglInitialize.restype = c_uint
major, minor = c_int(), c_int()
if not EGL.eglInitialize(display, byref(major), byref(minor)):
    raise RuntimeError('eglInitialize failed')
EGL.eglBindAPI.argtypes = [c_uint]
EGL.eglBindAPI.restype = c_uint
if not EGL.eglBindAPI(0x30A2):
    raise RuntimeError('eglBindAPI(OpenGL) failed')
EGL.eglChooseConfig.argtypes = [c_void_p, POINTER(c_int), POINTER(c_void_p), c_int, POINTER(c_int)]
EGL.eglChooseConfig.restype = c_uint
attrs = (c_int * 11)(0x3024, 8, 0x3023, 8, 0x3022, 8, 0x3033, 1, 0x3040, 8, 0x3038)
config, count = c_void_p(), c_int()
if not EGL.eglChooseConfig(display, attrs, byref(config), 1, byref(count)) or not count.value:
    raise RuntimeError('eglChooseConfig failed')
EGL.eglCreatePbufferSurface.argtypes = [c_void_p, c_void_p, POINTER(c_int)]
EGL.eglCreatePbufferSurface.restype = c_void_p
surface = EGL.eglCreatePbufferSurface(display, config, (c_int * 5)(0x3057, 640, 0x3056, 480, 0x3038))
EGL.eglCreateContext.argtypes = [c_void_p, c_void_p, c_void_p, POINTER(c_int)]
EGL.eglCreateContext.restype = c_void_p
context = EGL.eglCreateContext(display, config, None, (c_int * 1)(0x3038))
EGL.eglMakeCurrent.argtypes = [c_void_p, c_void_p, c_void_p, c_void_p]
EGL.eglMakeCurrent.restype = c_uint
if not surface or not context or not EGL.eglMakeCurrent(display, surface, surface, context):
    raise RuntimeError('EGL pbuffer/context initialization failed')

GL = ctypes.CDLL(ctypes.util.find_library('GL'))
GL.glGetString.argtypes = [c_uint]
GL.glGetString.restype = c_char_p
renderer = GL.glGetString(0x1F01).decode()
version = GL.glGetString(0x1F02).decode()
if 'llvmpipe' not in renderer.lower():
    raise RuntimeError(f'Software renderer required; found {renderer!r}')
print('EGL', major.value, minor.value, 'GL_RENDERER', renderer, 'GL_VERSION', version, flush=True)

from pxr import Gf, Glf, Usd, UsdGeom, UsdImagingGL, UsdShade

engine = UsdImagingGL.Engine()
plugins = engine.GetRendererPlugins()
if 'HdStormRendererPlugin' not in plugins:
    raise RuntimeError(f'HdStormRendererPlugin unavailable: {plugins}')
engine.SetRendererPlugin('HdStormRendererPlugin')
width, height = 640, 480
engine.SetRenderViewport(Gf.Vec4d(0, 0, width, height))
engine.SetRenderBufferSize(Gf.Vec2i(width, height))
engine.SetRendererAov('color')

eye = Gf.Vec3d(-0.2253750697848067, 0.14749752603248137, 0.10593937803842146)
center = Gf.Vec3d(-0.23323673754930496, 0.09018429368786573, 0.1102924570441246)
up = Gf.Vec3d(0, 0, 1)  # match fixed Three camera's Z-up view
view = Gf.Matrix4d().SetLookAt(eye, center, up)
camera = Gf.Camera()
camera.projection = Gf.Camera.Perspective
camera.SetPerspectiveFromAspectRatioAndFieldOfView(width / height, 35.0, Gf.Camera.FOVVertical)
camera.clippingRange = Gf.Range1f(0.001, 100.0)
projection = camera.frustum.ComputeProjectionMatrix()
engine.SetCameraState(view, projection)

light = Glf.SimpleLight()
light.position = Gf.Vec4f(1, 2, 3, 0)
light.diffuse = Gf.Vec4f(1, 1, 1, 1)
light.specular = Gf.Vec4f(0.35, 0.35, 0.35, 1)
light.ambient = Gf.Vec4f(0.35, 0.35, 0.35, 1)
material = Glf.SimpleMaterial()
material.ambient = Gf.Vec4f(0.35, 0.35, 0.35, 1)
material.diffuse = Gf.Vec4f(1, 1, 1, 1)
material.specular = Gf.Vec4f(0.35, 0.35, 0.35, 1)
engine.SetLightingState([light], material, Gf.Vec4f(0.1, 0.1, 0.1, 1))
params = UsdImagingGL.RenderParams()
params.enableLighting = True
params.clearColor = Gf.Vec4f(0.05, 0.05, 0.05, 1)

GL.glViewport(0, 0, width, height)
GL.glPixelStorei(0x0D05, 1)  # GL_PACK_ALIGNMENT
GL.glReadPixels.argtypes = [c_int, c_int, c_int, c_int, c_uint, c_uint, c_void_p]
out_dir.mkdir(parents=True, exist_ok=True)

def mesh_info(stage):
    prim = stage.GetPrimAtPath('/Patch/mesh')
    if not prim or not prim.IsValid():
        raise RuntimeError(f'Expected /Patch/mesh in {stage.GetRootLayer().identifier}')
    mesh = UsdGeom.Mesh(prim)
    points = mesh.GetPointsAttr().Get()
    counts = mesh.GetFaceVertexCountsAttr().Get()
    indices = mesh.GetFaceVertexIndicesAttr().Get()
    normals = mesh.GetNormalsAttr().Get()
    if not points or not counts or not indices or not normals:
        raise RuntimeError('Mesh points/faces/normals missing')
    if len(indices) != len(counts) * 3 or any(int(c) != 3 for c in counts):
        raise RuntimeError('Stage mesh is not triangulated')
    if len(normals) != len(points):
        raise RuntimeError('Expected vertex normals with one entry per point')
    mins = [min(float(p[k]) for p in points) for k in range(3)]
    maxs = [max(float(p[k]) for p in points) for k in range(3)]
    normal_lengths = [math.sqrt(sum(float(v[k]) ** 2 for k in range(3))) for v in normals]
    primvar = UsdGeom.PrimvarsAPI(prim).GetPrimvar('st')
    uv_count = len(primvar.Get()) if primvar and primvar.Get() else 0
    normal_links = []
    for shader_prim in stage.Traverse():
        if shader_prim.GetTypeName() != 'Shader':
            continue
        shader = UsdShade.Shader(shader_prim)
        if shader.GetIdAttr().Get() != 'UsdPreviewSurface':
            continue
        normal = shader.GetInput('normal')
        if normal:
            normal_links = [str(x.source.GetPath()) for x in normal.GetConnectedSources()[0]]
    return {
        'mesh_path': str(prim.GetPath()), 'triangles': len(counts), 'points': len(points), 'vertex_normals': len(normals),
        'uvs': uv_count, 'bbox_min': mins, 'bbox_max': maxs,
        'normal_length_min': min(normal_lengths), 'normal_length_max': max(normal_lengths),
        'preview_surface_normal_links': normal_links,
    }

for stage_name in args:
    stage_path = validate_stage_name(stage_name, stages_dir)
    stage = Usd.Stage.Open(str(stage_path))
    if not stage:
        raise RuntimeError(f'Usd.Stage.Open failed: {stage_path}')
    info = mesh_info(stage)
    GL.glViewport(0, 0, width, height)
    for _ in range(10):
        engine.Render(stage.GetPseudoRoot(), params)
    GL.glFinish()
    buf = (ctypes.c_ubyte * (width * height * 4))()
    GL.glReadPixels(0, 0, width, height, 0x1908, 0x1401, buf)  # RGBA/UNSIGNED_BYTE
    raw = bytes(buf)
    stem = stage_name.removesuffix('.usda').removesuffix('.usdz')
    raw_path = out_dir / f'{stem}.rgba'
    report_path = out_dir / f'{stem}.json'
    with raw_path.open('xb') as f:
        f.write(raw)
    report = {
        'stage': stage_name, 'stage_opened': True, 'renderer': renderer, 'gl_version': version,
        'hydra_plugin': 'HdStormRendererPlugin', 'egl': [major.value, minor.value],
        'isolation': 'one USD stage per fresh Blender/Hydra process; no shared render index across variants',
        'cpu_thread_controls': {k: os.environ.get(k) for k in ['LP_NUM_THREADS', 'OMP_NUM_THREADS', 'GALLIUM_DRIVER', 'LIBGL_ALWAYS_SOFTWARE']},
        'viewport': [width, height], 'camera': {
            'eye': list(eye), 'target': list(center), 'up': list(up), 'fov_vertical_degrees': 35,
            'projection': 'perspective', 'clipping': [0.001, 100.0], 'view_matrix': str(view), 'projection_matrix': str(projection),
        },
        'lighting': { 'one_directional_glf_light': list(light.position), 'diffuse': list(light.diffuse), 'specular': list(light.specular), 'light_ambient': list(light.ambient), 'global_ambient': [0.1, 0.1, 0.1, 1], 'clear_color_linear_argument': [0.05, 0.05, 0.05, 1] },
        'mesh': info, 'raw_rgba': {'path': str(raw_path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(), 'min': min(raw), 'max': max(raw), 'unique_channel_values': len(set(raw))},
        'pixel_origin': 'OpenGL glReadPixels bottom row first; all stages use this same convention.',
    }
    with report_path.open('x', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
        f.write('\n')
    print('RENDERED', stage_name, json.dumps({'triangles': info['triangles'], 'points': info['points'], 'bbox_min': info['bbox_min'], 'bbox_max': info['bbox_max'], 'raw_sha256': report['raw_rgba']['sha256'], 'min': min(raw), 'max': max(raw), 'unique': len(set(raw))}), flush=True)
