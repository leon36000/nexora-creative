"""Run inside a fresh background Blender; convert only the requested OBJ."""
import pathlib
import sys
import bpy

args = sys.argv[sys.argv.index('--') + 1:]
if len(args) != 2:
    raise ValueError('expected OBJ and new GLB paths')
source, target = map(pathlib.Path, args)
if not source.is_file() or target.exists():
    raise ValueError('source missing or output already exists')
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
bpy.ops.wm.obj_import(filepath=str(source))
meshes = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
if not meshes:
    raise ValueError('OBJ has no mesh')
for obj in meshes:
    obj.select_set(True)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
result = bpy.ops.export_scene.gltf(filepath=str(target), export_format='GLB')
if 'FINISHED' not in result or not target.is_file():
    raise RuntimeError('GLB export failed')
