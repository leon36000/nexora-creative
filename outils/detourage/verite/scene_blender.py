"""
Scènes Blender à vérité terrain exacte pour noter le détourage (alpha connu au pixel près, rendu Cycles, fond transparent).

  blender -b -P scene_blender.py -- <fourrure|verre|fumee> <dossier_sortie> [images=49] [echantillons=96] [derniere_image_rendue]

Écrit <dossier>/rgba_%04d.png (RGBA 16 bits, alpha droit). Le fond réel est ajouté ensuite par composer.py :
la vérité est alors l'alpha du rendu, sans aucune estimation. Catégories que nos clips Big Buck Bunny ne couvrent pas :
cheveux fins (fourrure longue, mèches folles), verre (transmission, film_transparent_glass), fumée (volume).
"""
import math
import os
import sys

import bpy

args = sys.argv[sys.argv.index('--') + 1:]
CAT, SORTIE = args[0], args[1]
N = int(args[2]) if len(args) > 2 else 49
ECH = int(args[3]) if len(args) > 3 else 96
FIN = int(args[4]) if len(args) > 4 else N  # aperçu : ne rendre que les premières images d'une scène de N images

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = 'CYCLES'
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 1280, 720, 100
sc.render.fps = 24
sc.frame_start, sc.frame_end = 1, N
sc.render.film_transparent = True
sc.cycles.film_transparent_glass = True
sc.cycles.samples = ECH
sc.cycles.use_denoising = True
sc.render.use_motion_blur = True
sc.render.motion_blur_shutter = 0.5
sc.view_settings.view_transform = 'Standard'
sc.render.image_settings.file_format = 'PNG'
sc.render.image_settings.color_mode = 'RGBA'
sc.render.image_settings.color_depth = '16'
sc.render.filepath = os.path.join(os.path.abspath(SORTIE), 'rgba_')

# GPU (OptiX puis CUDA), sinon CPU
prefs = bpy.context.preferences.addons['cycles'].preferences
for typ in ('OPTIX', 'CUDA'):
    try:
        prefs.compute_device_type = typ
        prefs.get_devices()
        if any(d.type == typ for d in prefs.devices):
            for d in prefs.devices:
                d.use = d.type == typ
            sc.cycles.device = 'GPU'
            break
    except TypeError:
        continue

monde = bpy.data.worlds.new('monde')
sc.world = monde
monde.use_nodes = True
monde.node_tree.nodes['Background'].inputs['Color'].default_value = (0.35, 0.37, 0.4, 1)
monde.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.8

cam_d = bpy.data.cameras.new('cam')
cam_d.lens = 50
cam = bpy.data.objects.new('cam', cam_d)
sc.collection.objects.link(cam)
cam.location = (0, -7.5, 0.3)
cam.rotation_euler = (math.radians(88), 0, 0)
sc.camera = cam

soleil_d = bpy.data.lights.new('soleil', 'SUN')
soleil_d.energy = 3.5
soleil = bpy.data.objects.new('soleil', soleil_d)
soleil.rotation_euler = (math.radians(50), math.radians(15), math.radians(30))
sc.collection.objects.link(soleil)


def materiau(nom):
    m = bpy.data.materials.new(nom)
    m.use_nodes = True
    return m, m.node_tree.nodes, m.node_tree.links


def trajectoire(ob, depart, arrivee, tours=0.0, axe=2):
    for f, p in ((1, depart), (N, arrivee)):
        sc.frame_set(f)
        ob.location = p
        r = list(ob.rotation_euler)
        r[axe] = math.radians(360 * tours * (f - 1) / max(1, N - 1))
        ob.rotation_euler = r
        ob.keyframe_insert('location')
        ob.keyframe_insert('rotation_euler')


if CAT == 'fourrure':
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.75, segments=48, ring_count=24)
    ob = bpy.context.object
    bpy.ops.object.shade_smooth()
    peau, n, l = materiau('peau')
    n['Principled BSDF'].inputs['Base Color'].default_value = (0.25, 0.14, 0.07, 1)
    ob.data.materials.append(peau)
    poil, n, l = materiau('poil')
    for x in list(n):
        n.remove(x)
    hb = n.new('ShaderNodeBsdfHairPrincipled')
    hb.parametrization = 'MELANIN'
    hb.inputs[1].default_value = 0.55  # Melanin (accès par position : le nom n'est pas indexable en 5.2)
    hb.inputs['Roughness'].default_value = 0.3
    out = n.new('ShaderNodeOutputMaterial')
    l.new(hb.outputs[0], out.inputs['Surface'])
    ob.data.materials.append(poil)
    ps = ob.modifiers.new('poils', 'PARTICLE_SYSTEM').particle_system
    s = ps.settings
    s.type = 'HAIR'
    s.count = 6000
    s.hair_length = 0.55
    s.material = 2
    s.child_type = 'INTERPOLATED'
    s.rendered_child_count = 12
    s.child_length = 1.0
    s.roughness_1, s.roughness_2, s.roughness_endpoint = 0.06, 0.25, 0.08  # mèches folles
    s.kink = 'CURL'
    s.kink_amplitude, s.kink_frequency = 0.02, 3.0
    s.root_radius, s.tip_radius, s.radius_scale = 1.0, 0.0, 0.008
    s.use_advanced_hair = True
    trajectoire(ob, (-2.6, 0, -0.1), (2.4, 0.4, 0.2), tours=0.35)
elif CAT == 'verre':
    bpy.ops.mesh.primitive_ico_sphere_add(radius=0.9, subdivisions=5)
    ob = bpy.context.object
    bpy.ops.object.shade_smooth()
    verre, n, l = materiau('verre')
    for x in list(n):
        n.remove(x)
    g = n.new('ShaderNodeBsdfGlass')
    g.inputs['IOR'].default_value = 1.45
    g.inputs['Roughness'].default_value = 0.02
    g.inputs['Color'].default_value = (0.92, 0.96, 1.0, 1)
    out = n.new('ShaderNodeOutputMaterial')
    l.new(g.outputs[0], out.inputs['Surface'])
    ob.data.materials.append(verre)
    # une anse opaque : un objet en partie opaque, en partie transparent, comme une vraie verrerie
    bpy.ops.mesh.primitive_torus_add(major_radius=0.55, minor_radius=0.09, location=(0.95, 0, 0), rotation=(0, math.radians(90), 0))
    anse = bpy.context.object
    m2, n2, _ = materiau('anse')
    n2['Principled BSDF'].inputs['Base Color'].default_value = (0.7, 0.2, 0.1, 1)
    anse.data.materials.append(m2)
    anse.parent = ob
    trajectoire(ob, (-2.3, 0.3, 0.0), (2.0, -0.2, 0.15), tours=0.25)
elif CAT == 'fumee':
    bpy.ops.mesh.primitive_cube_add(size=2.6)
    ob = bpy.context.object
    fum, n, l = materiau('fumee')
    for x in list(n):
        n.remove(x)
    vol = n.new('ShaderNodeVolumePrincipled')
    vol.inputs['Color'].default_value = (0.82, 0.82, 0.85, 1)
    tex = n.new('ShaderNodeTexCoord')
    bruit = n.new('ShaderNodeTexNoise')
    bruit.noise_dimensions = '4D'
    bruit.inputs['Scale'].default_value = 1.6
    bruit.inputs['Detail'].default_value = 8
    l.new(tex.outputs['Object'], bruit.inputs['Vector'])
    grad = n.new('ShaderNodeTexGradient')
    grad.gradient_type = 'SPHERICAL'
    l.new(tex.outputs['Object'], grad.inputs['Vector'])
    mul = n.new('ShaderNodeMath')
    mul.operation = 'MULTIPLY'
    l.new(bruit.outputs['Fac'], mul.inputs[0])
    l.new(grad.outputs['Fac'], mul.inputs[1])
    rampe = n.new('ShaderNodeMapRange')
    rampe.inputs['From Min'].default_value = 0.12
    rampe.inputs['From Max'].default_value = 0.45
    rampe.inputs['To Max'].default_value = 9.0
    l.new(mul.outputs[0], rampe.inputs['Value'])
    l.new(rampe.outputs[0], vol.inputs['Density'])
    out = n.new('ShaderNodeOutputMaterial')
    l.new(vol.outputs[0], out.inputs['Volume'])
    ob.data.materials.append(fum)
    for f, w in ((1, 0.0), (N, 1.4)):  # la fumée bouille en dérivant
        bruit.inputs['W'].default_value = w
        bruit.inputs['W'].keyframe_insert('default_value', frame=f)
    trajectoire(ob, (-1.8, 0, -0.2), (1.6, 0, 0.3), tours=0.1)
else:
    raise SystemExit(f'catégorie inconnue : {CAT}')

# interpolation linéaire : mouvement continu, sans arrêt aux extrémités
for a in bpy.data.actions:
    for c in getattr(a, 'fcurves', []):
        for k in c.keyframe_points:
            k.interpolation = 'LINEAR'
sc.frame_end = FIN
os.makedirs(SORTIE, exist_ok=True)
bpy.ops.render.render(animation=True)
