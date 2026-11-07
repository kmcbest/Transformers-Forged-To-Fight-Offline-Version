import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import math
from pathlib import Path
import bpy
import mathutils

ROOT = Path(r"E:\Agent\TFTF-blender")
IH_OBJ = ROOT / "tools" / "demolishor" / "ironhide_extracted" / "ironhide.obj"
IH_TEX = ROOT / "toolchain" / "unity_build_project" / "Assets" / "Onslaught" / "Ironhide" / "cha_ironhide_cin_rotf_main_a.png"
OUT_DIR = Path(r"C:\Users\Xiangli496\.gemini\antigravity\brain\b1cc49d0-d381-4e8e-a8aa-42f4453e608d\scratch")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.obj(filepath=str(IH_OBJ))

ih_objs = [o for o in bpy.data.objects if o.type == 'MESH']
for o in ih_objs:
    pts = [o.matrix_world @ v.co for v in o.data.vertices]
    xs = [p.x for p in pts]; ys = [p.y for p in pts]; zs = [p.z for p in pts]
    print(f"Ironhide OBJ '{o.name}': verts={len(pts)} | X[{min(xs):.3f}, {max(xs):.3f}] Y[{min(ys):.3f}, {max(ys):.3f}] Z[{min(zs):.3f}, {max(zs):.3f}]")

    mat = bpy.data.materials.new("IH_Mat")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if IH_TEX.exists() and bsdf:
        ti = mat.node_tree.nodes.new("ShaderNodeTexImage")
        ti.image = bpy.data.images.load(str(IH_TEX))
        mat.node_tree.links.new(ti.outputs["Color"], bsdf.inputs["Base Color"])
    o.data.materials.clear()
    o.data.materials.append(mat)

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1200
scene.render.resolution_y = 1200
if not scene.world:
    scene.world = bpy.data.worlds.new("W")
scene.world.use_nodes = True
scene.world.node_tree.nodes["Background"].inputs[0].default_value = (0.18, 0.19, 0.22, 1.0)

def look_at(obj, pos, target):
    obj.location = mathutils.Vector(pos)
    rot_quat = (mathutils.Vector(target) - obj.location).to_track_quat('-Z', 'Y')
    obj.rotation_euler = rot_quat.to_euler()

cam = bpy.data.objects.new("Cam", bpy.data.cameras.new("Cam"))
scene.collection.objects.link(cam)
scene.camera = cam

# Note: OBJ import converts Y-up to Z-up automatically in Blender (-Z forward, Y up -> Blender -Y forward or +Y forward)
# Let's render front (-Y and +Y) so we see exact rest pose of Movie Ironhide!
for nm, pos in [("Key", (5, -12, 10)), ("Fill", (-6, 12, 8))]:
    lo = bpy.data.objects.new(nm, bpy.data.lights.new(nm, 'SUN'))
    lo.data.energy = 3.5
    scene.collection.objects.link(lo)
    look_at(lo, pos, (0, 0, 5.2))

look_at(cam, (3.5, -14.5, 5.5), (0, 0, 5.2))
scene.render.filepath = str(OUT_DIR / "diag_ironhide_rest_pose_1.png")
bpy.ops.render.render(write_still=True)

look_at(cam, (3.5, 14.5, 5.5), (0, 0, 5.2))
scene.render.filepath = str(OUT_DIR / "diag_ironhide_rest_pose_2.png")
bpy.ops.render.render(write_still=True)
