import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import math
from pathlib import Path
import bpy
from mathutils import Vector, Euler

ROOT = Path(r"E:\Agent\TFTF-blender")
EW_FBX = ROOT / "3rd-party-models" / "Blitzwing_EW" / "01_source" / "H_shandian_G1_M_LOD.fbx"
ROBOT_FBX = ROOT / "3rd-party-models" / "Blitzwing_EW" / "03_fbx_exports" / "cha_blitzwing_gs_00_robot.fbx"
TEX_WPNS_DIFF = ROOT / "tools" / "blitzwing" / "atlased_textures" / "cha_blitzwing_wpns_Diffuse.png"
RENDER_DIR = ROOT / "tools" / "blitzwing" / "renders"

# 1. Inspect W2 (Gun) raw side silhouette (+X right, -X left, +Z up)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(EW_FBX))
bpy.context.view_layer.update()

w2 = bpy.data.objects["H_shandian_G1_W2_Lod"]
for o in list(bpy.data.objects):
    if o != w2:
        bpy.data.objects.remove(o, do_unlink=True)
mw = w2.matrix_world.copy()
w2.parent = None
w2.matrix_world = mw
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
from mathutils import Matrix
w2.data.transform(Matrix.Scale(149.1728, 4))
w2.data.update()

# Print Z-slice X intervals so we know where barrel, receiver, grip, scope are!
pts = [v.co for v in w2.data.vertices]
print("=== W2 Scaled Z-slices (+X right, -X left, +Z up) ===")
for z0 in [0.95, 1.3, 1.7, 2.1, 2.5, 2.9, 3.3]:
    sl = [p for p in pts if z0 - 0.2 <= p.z < z0 + 0.2]
    if sl:
        print(f"  Z~{z0:.2f} (n={len(sl):3d}): X=[{min(p.x for p in sl):6.3f}, {max(p.x for p in sl):6.3f}] Y=[{min(p.y for p in sl):6.3f}, {max(p.y for p in sl):6.3f}]")

mat = bpy.data.materials.new("Wpn")
mat.use_nodes = True
tex = mat.node_tree.nodes.new("ShaderNodeTexImage")
tex.image = bpy.data.images.load(str(TEX_WPNS_DIFF))
mat.node_tree.links.new(tex.outputs["Color"], mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"])
w2.data.materials.clear()
w2.data.materials.append(mat)

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 1280
scene.render.resolution_y = 640
world = bpy.data.worlds.new("W")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.15, 0.17, 0.22, 1.0)
ld = bpy.data.lights.new("S", type='SUN')
ld.energy = 3.0
lo = bpy.data.objects.new("S", ld)
lo.rotation_euler = Euler((0.6, 0.2, 0.4))
bpy.context.collection.objects.link(lo)

cam = bpy.data.objects.new("C", bpy.data.cameras.new("C"))
cam.data.type = 'ORTHO'
cam.data.ortho_scale = 7.5
cam.location = (0.0, -10.0, 2.2)
cam.rotation_euler = Euler((math.pi / 2, 0, 0))
bpy.context.collection.objects.link(cam)
scene.camera = cam
scene.render.filepath = str(RENDER_DIR / "13_w2_gun_ortho_side.png")
bpy.ops.render.render(write_still=True)

# 2. Measure exact inner palm cavity of RightHand and LeftHand in Blitzwing Robot!
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(ROBOT_FBX))
mesh = next(o for o in bpy.data.objects if o.type == 'MESH')
bpy.context.view_layer.update()

# Convert LeftHand & RightHand verts to UNITY Hand Space and print cross-sections along X (wrist->fingers) and Y (knuckles->tips)
lh_origin_u = Vector((-2.4734, 5.5272, -0.0470))
rh_origin_u = Vector((+2.4734, 5.5272, -0.0470))
for bn, orig_u in [("LeftHand", lh_origin_u), ("RightHand", rh_origin_u)]:
    vg_idx = mesh.vertex_groups[bn].index
    hpts = []
    for v in mesh.data.vertices:
        if sum(g.weight for g in v.groups if g.group == vg_idx) > 0.5:
            vb = mesh.matrix_world @ v.co
            u = Vector((-vb.x, vb.z, -vb.y)) - orig_u
            hpts.append(Vector((u.y, -u.x, u.z)))
    print(f"\n=== {bn} X-slices in UNITY {bn} space ===")
    for x0 in [-0.2, -0.45, -0.65, -0.80, -0.95]:
        sl = [p for p in hpts if x0 - 0.12 <= p.x < x0 + 0.12]
        if sl:
            print(f"  X~{x0:5.2f} (n={len(sl):3d}): Y=[{min(p.y for p in sl):6.3f}, {max(p.y for p in sl):6.3f}], Z=[{min(p.z for p in sl):6.3f}, {max(p.z for p in sl):6.3f}]")
