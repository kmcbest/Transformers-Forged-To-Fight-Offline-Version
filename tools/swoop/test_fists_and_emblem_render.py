import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import math
from pathlib import Path
import bpy
from mathutils import Euler, Matrix, Quaternion, Vector

ROOT = Path("e:/Agent/TFTF-blender")
FBX_SRC = ROOT / "3rd-party-models/swoop/01_master/Swoop_pbr.fbx"
OUT_IMG = ROOT / "renders/swoop/debug_blender_fists.png"
OUT_IMG.parent.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_SRC))

arm = bpy.data.objects.get("Bip001")
mesh = bpy.data.objects.get("Swoop.001")
sym = bpy.data.objects.get("Symbol_AB")

# Clear anim and reset pose to pure Static Pose
arm.animation_data_clear()
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='POSE')
bpy.ops.pose.select_all(action='SELECT')
bpy.ops.pose.transforms_clear()

# Symmetric tight combat fist curls (taken from Left fist idle01/attack01 + full right index/thumb curl)
# Also extend wrists slightly down arm axis so fists emerge clearly from forearm cuffs!
finger_quats = {
    # Left fist (tight combat fist from attack01)
    'Bone_L_Finger0': (0.996808, 0.001097, -0.078611, -0.013909),
    'Bone_L_Finger01': (0.985, 0.0, 0.0, 0.174),    # ~20 deg curl
    'Bone_L_Finger02': (0.924, 0.0, 0.0, 0.383),    # ~45 deg lock across index/middle
    'Bone_L_Finger1': (0.906, 0.0, 0.0, 0.423),     # ~50 deg curl
    'Bone_L_Finger11': (0.887, 0.0, 0.0, 0.462),    # ~55 deg curl
    'Bone_L_Finger12': (0.906, 0.0, 0.0, 0.423),    # ~50 deg curl
    'Bone_L_Finger2': (0.906, 0.0, 0.0, 0.423),     # ~50 deg curl
    'Bone_L_Finger21': (0.887, 0.0, 0.0, 0.462),    # ~55 deg curl
    'Bone_L_Finger22': (0.887, 0.0, 0.0, 0.462),    # ~55 deg curl

    # Right fist (matching tight curl; note Bone_R_Finger* local Z curls identically)
    'Bone_R_Finger0': (0.997871, 0.053770, -0.036849, 0.001986),
    'Bone_R_Finger01': (0.985, 0.0, 0.0, 0.174),
    'Bone_R_Finger02': (0.924, 0.0, 0.0, 0.383),
    'Bone_R_Finger1': (0.906, 0.0, 0.0, 0.423),
    'Bone_R_Finger11': (0.887, 0.0, 0.0, 0.462),
    'Bone_R_Finger12': (0.906, 0.0, 0.0, 0.423),
    'Bone_R_Finger2': (0.906, 0.0, 0.0, 0.423),
    'Bone_R_Finger21': (0.887, 0.0, 0.0, 0.462),
    'Bone_R_Finger22': (0.887, 0.0, 0.0, 0.462),
}

for bname, q in finger_quats.items():
    pb = arm.pose.bones.get(bname)
    if pb:
        pb.rotation_mode = 'QUATERNION'
        pb.rotation_quaternion = Quaternion(q).normalized()

bpy.ops.object.mode_set(mode='OBJECT')

# Check where forearm & fist sit
deps = bpy.context.evaluated_depsgraph_get()
ev_obj = mesh.evaluated_get(deps)
ev_mesh = bpy.data.meshes.new_from_object(ev_obj)

# Notice ev_mesh.vertices are in mesh local coords (unscaled raw Static Pose space!)
def bounds_vg(vgn):
    vg = mesh.vertex_groups[vgn]
    pts = [ev_mesh.vertices[v.index].co for v in mesh.data.vertices if any(g.group == vg.index and g.weight > 0.4 for g in v.groups)]
    return min(p.z for p in pts), max(p.z for p in pts)

print("After Finger Curl (local mesh coords):")
for s in ["L", "R"]:
    print(f"  {s} Forearm Z: {bounds_vg(f'Bone_{s}_Forearm')}")
    print(f"  {s} Hand    Z: {bounds_vg(f'Bone_{s}_Hand')}")
    print(f"  {s} Fing12  Z: {bounds_vg(f'Bone_{s}_Finger12')}")
    print(f"  {s} Fing22  Z: {bounds_vg(f'Bone_{s}_Finger22')}")
    print(f"  {s} Fing02  Z: {bounds_vg(f'Bone_{s}_Finger02')}")

# Transform baked mesh and Symbol_AB to clean camera view (in world coords where mesh was scaled 0.01)
# Instead put baked mesh at Identity scale 1.0 so Z is [-1.78, 1.71]
baked_obj = bpy.data.objects.new("BakedPreview", ev_mesh)
bpy.context.scene.collection.objects.link(baked_obj)
baked_obj.matrix_world = Matrix.Identity(4)

# Hide originals
mesh.hide_render = True
if sym:
    # Check Symbol_AB transform relative to mesh.matrix_world
    rel_mat = mesh.matrix_world.inverted() @ sym.matrix_world
    print("Symbol_AB relative transform to Swoop.001:")
    print(rel_mat)
    sym_pts_in_mesh = [rel_mat @ v.co for v in sym.data.vertices]
    print(f"Symbol_AB in Swoop.001 space: X=[{min(p.x for p in sym_pts_in_mesh):.3f},{max(p.x for p in sym_pts_in_mesh):.3f}], Y=[{min(p.y for p in sym_pts_in_mesh):.3f},{max(p.y for p in sym_pts_in_mesh):.3f}], Z=[{min(p.z for p in sym_pts_in_mesh):.3f},{max(p.z for p in sym_pts_in_mesh):.3f}]")
    sym.hide_render = True

# Add camera & sun focusing on Right+Left hands at Z=-0.35, Y=-1.6
cam_d = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_d)
bpy.context.scene.collection.objects.link(cam)
bpy.context.scene.camera = cam
cam.location = Vector((0.35, -1.65, -0.25))
direction = Vector((0.0, 0.0, -0.28)) - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

ld = bpy.data.lights.new("Sun", 'SUN')
l = bpy.data.objects.new("Sun", ld)
bpy.context.scene.collection.objects.link(l)
l.rotation_euler = Euler((math.radians(55), 0, math.radians(-25)), 'XYZ')
ld.energy = 3.5

bpy.context.scene.render.engine = 'BLENDER_EEVEE'
bpy.context.scene.render.resolution_x = 1280
bpy.context.scene.render.resolution_y = 720
bpy.context.scene.render.filepath = str(OUT_IMG)
bpy.ops.render.render(write_still=True)
print(f"Saved preview render to {OUT_IMG}")
