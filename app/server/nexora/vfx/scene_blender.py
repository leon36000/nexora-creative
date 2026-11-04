"""Scène d'effets visuels sans interface (Blender 5.2, bpy) pour Nexora Creative.

Place un modèle Relief (GLB) dans une scène, anime l'objet et une caméra, éclaire, puis rend les passes utiles :
couleur (RGBA, fond transparent pour la composition), profondeur (PNG 16 bits, 1 = proche), normales (espace caméra),
masque (alpha de l'objet). Les passes de données sont rendues par substitution de matériau : aucune dépendance au
compositeur, dont l'API change d'une version de Blender à l'autre.

    blender -b --factory-startup -P scene_blender.py -- spec.json

Spec (JSON) : voir SPEC_EXEMPLE en bas du fichier. Sortie : <sortie>/<passe>/####.png et <sortie>/rapport.json.
"""
import json
import math
import os
import sys
import time

import bpy
from mathutils import Vector


def lire_spec():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    with open(argv[0], encoding="utf-8") as f:
        return json.load(f)


def vider_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def importer_glb(chemin, taille, rotation_deg):
    avant = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=chemin)
    nouveaux = [o for o in bpy.data.objects if o not in avant]
    racine = bpy.data.objects.new("relief", None)
    bpy.context.scene.collection.objects.link(racine)
    for o in nouveaux:
        if o.parent is None:
            o.parent = racine
    bpy.context.view_layer.update()
    # Boîte englobante de tous les maillages : centre à l'origine, plus grande dimension = taille.
    coins = [o.matrix_world @ Vector(c) for o in nouveaux if o.type == "MESH" for c in o.bound_box]
    mini = Vector((min(c.x for c in coins), min(c.y for c in coins), min(c.z for c in coins)))
    maxi = Vector((max(c.x for c in coins), max(c.y for c in coins), max(c.z for c in coins)))
    centre, dims = (mini + maxi) / 2, maxi - mini
    echelle = taille / max(dims)
    for o in nouveaux:
        if o.parent is racine:
            o.location -= centre
    racine.scale = (echelle, echelle, echelle)
    racine.rotation_euler = [math.radians(a) for a in rotation_deg]
    for o in nouveaux:
        if o.type == "MESH":
            o.pass_index = 1
    return racine, [o for o in nouveaux if o.type == "MESH"], {"dimensions": list(dims * echelle), "faces": sum(len(o.data.polygons) for o in nouveaux if o.type == "MESH")}


def cles(obj, chemin, trajet, conv=lambda v: v):
    """trajet : [[image, x, y, z], ...] ; interpolation de Bézier (départ et arrivée en douceur)."""
    for t, *v in trajet:
        setattr(obj, chemin, conv(v))
        obj.keyframe_insert(data_path=chemin, frame=int(t))


def courbes(obj):
    """Courbes d'animation d'un objet ; Blender 5 range les courbes dans des « channelbags » (actions en couches)."""
    ad = obj.animation_data
    if not ad or not ad.action:
        return []
    act = ad.action
    if getattr(act, "fcurves", None):
        return list(act.fcurves)
    try:
        from bpy_extras import anim_utils
        sac = anim_utils.action_get_channelbag_for_slot(act, ad.action_slot)
        return list(sac.fcurves) if sac else []
    except Exception:
        return []


def camera(spec_cam):
    cam_data = bpy.data.cameras.new("camera")
    cam_data.lens = spec_cam.get("objectif_mm", 35)
    cam_data.clip_start, cam_data.clip_end = 0.05, 5000
    cam = bpy.data.objects.new("camera", cam_data)
    bpy.context.scene.collection.objects.link(cam)
    cible = bpy.data.objects.new("cible", None)
    bpy.context.scene.collection.objects.link(cible)
    c = cam.constraints.new("TRACK_TO")
    c.target, c.track_axis, c.up_axis = cible, "TRACK_NEGATIVE_Z", "UP_Y"
    cles(cam, "location", spec_cam["trajet"])
    cles(cible, "location", spec_cam.get("cible", [[1, 0, 0, 0]]))
    if spec_cam.get("secousse"):
        # Secousse caméra (impact) : bruit sur la rotation, amplitude en degrés.
        cam.rotation_mode = "XYZ"
        cam.keyframe_insert("rotation_euler", frame=1)
        for courbe in courbes(cam):
            if courbe.data_path == "rotation_euler":
                m = courbe.modifiers.new("NOISE")
                m.strength, m.scale = math.radians(spec_cam["secousse"]), 3
    bpy.context.scene.camera = cam
    return cam


def lumieres(spec_l):
    soleil = bpy.data.lights.new("soleil", "SUN")
    soleil.energy = spec_l.get("soleil_force", 4)
    soleil.color = spec_l.get("soleil_couleur", [1, 0.95, 0.88])
    soleil.angle = math.radians(1.5)
    o = bpy.data.objects.new("soleil", soleil)
    bpy.context.scene.collection.objects.link(o)
    d = Vector(spec_l.get("soleil_dir", [-1, -0.6, -0.5])).normalized()
    o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    if spec_l.get("contre", True):
        contre = bpy.data.lights.new("contre", "SUN")
        contre.energy = spec_l.get("contre_force", 2.5)
        contre.color = spec_l.get("contre_couleur", [0.55, 0.7, 1.0])
        oc = bpy.data.objects.new("contre", contre)
        bpy.context.scene.collection.objects.link(oc)
        oc.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    monde = bpy.data.worlds.new("monde")
    monde.use_nodes = True
    fond = monde.node_tree.nodes["Background"]
    fond.inputs[0].default_value = (*spec_l.get("ambiance_couleur", [0.02, 0.025, 0.035]), 1)
    fond.inputs[1].default_value = spec_l.get("ambiance_force", 1.0)
    bpy.context.scene.world = monde


def moteur(scene, nom, echantillons):
    if nom == "CYCLES":
        scene.render.engine = "CYCLES"
        prefs = bpy.context.preferences.addons["cycles"].preferences
        for t in ("OPTIX", "CUDA"):
            try:
                prefs.compute_device_type = t
                prefs.get_devices()
                if any(d.type == t for d in prefs.devices):
                    for d in prefs.devices:
                        d.use = d.type == t
                    scene.cycles.device = "GPU"
                    break
            except TypeError:
                continue
        scene.cycles.samples = echantillons
        scene.cycles.use_denoising = True
        return f"CYCLES/{scene.cycles.device}"
    for n in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try:
            scene.render.engine = n
            break
        except TypeError:
            continue
    scene.eevee.taa_render_samples = echantillons
    return scene.render.engine


def materiau_donnees(nom, proche, loin):
    """Matériau émissif de substitution : profondeur (1 = proche), normales (espace caméra) ou masque (blanc)."""
    m = bpy.data.materials.new(f"passe_{nom}")
    m.use_nodes = True
    n, l = m.node_tree.nodes, m.node_tree.links
    n.clear()
    sortie, em = n.new("ShaderNodeOutputMaterial"), n.new("ShaderNodeEmission")
    l.new(em.outputs[0], sortie.inputs[0])
    if nom == "profondeur":
        cam, plage = n.new("ShaderNodeCameraData"), n.new("ShaderNodeMapRange")
        plage.inputs["From Min"].default_value, plage.inputs["From Max"].default_value = proche, loin
        plage.inputs["To Min"].default_value, plage.inputs["To Max"].default_value = 1.0, 0.0
        l.new(cam.outputs["View Z Depth"], plage.inputs["Value"])
        l.new(plage.outputs["Result"], em.inputs["Color"])
    elif nom == "normales":
        geo, tr, mul, add = n.new("ShaderNodeNewGeometry"), n.new("ShaderNodeVectorTransform"), n.new("ShaderNodeVectorMath"), n.new("ShaderNodeVectorMath")
        tr.vector_type, tr.convert_from, tr.convert_to = "NORMAL", "WORLD", "CAMERA"
        mul.operation, add.operation = "MULTIPLY", "ADD"
        mul.inputs[1].default_value, add.inputs[1].default_value = (0.5, 0.5, -0.5), (0.5, 0.5, 0.5)
        l.new(geo.outputs["Normal"], tr.inputs[0])
        l.new(tr.outputs[0], mul.inputs[0])
        l.new(mul.outputs[0], add.inputs[0])
        l.new(add.outputs[0], em.inputs["Color"])
    else:
        em.inputs["Color"].default_value = (1, 1, 1, 1)
    return m


def rendre_passe(scene, passe, dossier, images, spec):
    os.makedirs(dossier, exist_ok=True)
    r = scene.render
    donnees = passe != "couleur"
    scene.view_settings.view_transform = "Standard" if donnees else spec.get("transformee", "AgX")
    r.film_transparent = True
    r.image_settings.file_format = "PNG"
    r.image_settings.color_mode = "BW" if passe in ("profondeur", "masque") else "RGBA" if passe == "couleur" else "RGB"
    r.image_settings.color_depth = "16" if passe == "profondeur" else "8"
    vl = bpy.context.view_layer
    vl.material_override = materiau_donnees(passe, *spec.get("profondeur_plage", [2, 60])) if donnees else None
    monde = scene.world.node_tree.nodes["Background"]
    force = monde.inputs[1].default_value
    if donnees:
        monde.inputs[1].default_value = 0
    t0 = time.time()
    for i in images:
        scene.frame_set(i)
        r.filepath = os.path.join(dossier, f"{i:04d}.png")
        bpy.ops.render.render(write_still=True)
    monde.inputs[1].default_value = force
    vl.material_override = None
    return round(time.time() - t0, 2)


def main():
    spec = lire_spec()
    t0 = time.time()
    vider_scene()
    scene = bpy.context.scene
    scene.render.resolution_x, scene.render.resolution_y = spec.get("largeur", 832), spec.get("hauteur", 480)
    scene.render.resolution_percentage = 100
    scene.render.fps = 24
    n = spec.get("images", 121)
    scene.frame_start, scene.frame_end = 1, n
    # Flou de mouvement (obturateur à 180° par défaut) : un objet rapide rendu net trahit l'image de synthèse.
    scene.render.use_motion_blur = bool(spec.get("flou_mouvement", True))
    scene.render.motion_blur_shutter = spec.get("obturateur", 0.5)
    racine, maillages, infos = importer_glb(spec["glb"], spec["objet"].get("taille", 10), spec["objet"].get("rotation_deg", [0, 0, 0]))
    if spec["objet"].get("trajet"):
        cles(racine, "location", spec["objet"]["trajet"])
    if spec["objet"].get("rotation_trajet"):
        cles(racine, "rotation_euler", spec["objet"]["rotation_trajet"], conv=lambda v: [math.radians(a) for a in v])
    if spec["objet"].get("lineaire"):
        for courbe in courbes(racine):
            for k in courbe.keyframe_points:
                k.interpolation = "LINEAR"
    camera(spec["camera"])
    lumieres(spec.get("lumiere", {}))
    nom_moteur = moteur(scene, spec.get("moteur", "EEVEE"), spec.get("echantillons", 32))
    images = spec.get("images_seules") or list(range(1, n + 1))
    temps = {}
    for passe in spec.get("passes", ["couleur", "profondeur", "normales", "masque"]):
        if passe != "couleur" and spec.get("moteur_donnees"):
            moteur(scene, spec["moteur_donnees"], 1)
        temps[passe] = rendre_passe(scene, passe, os.path.join(spec["sortie"], passe), images, spec)
        moteur(scene, spec.get("moteur", "EEVEE"), spec.get("echantillons", 32))
    rapport = {"moteur": nom_moteur, "images": len(images), "temps_passes_s": temps, "total_s": round(time.time() - t0, 2), "objet": infos, "blender": bpy.app.version_string}
    with open(os.path.join(spec["sortie"], "rapport.json"), "w", encoding="utf-8") as f:
        json.dump(rapport, f, indent=1)
    print("RAPPORT", json.dumps(rapport))


SPEC_EXEMPLE = {
    "glb": "vaisseau.glb", "sortie": "rendu", "largeur": 832, "hauteur": 480, "images": 121, "moteur": "EEVEE", "echantillons": 32,
    "objet": {"taille": 10, "rotation_deg": [0, 0, 90], "trajet": [[1, 0, 40, 0], [121, 0, -30, 2]]},
    "camera": {"objectif_mm": 28, "trajet": [[1, 6, -12, -1.5], [121, 4, -14, -1]], "cible": [[1, 0, 30, 0], [121, 0, -25, 2]], "secousse": 0.4},
    "lumiere": {"soleil_dir": [-1, 0.4, -0.3], "soleil_force": 5, "contre": True},
    "passes": ["couleur", "profondeur", "normales", "masque"], "profondeur_plage": [3, 80],
}

if __name__ == "__main__":
    main()
