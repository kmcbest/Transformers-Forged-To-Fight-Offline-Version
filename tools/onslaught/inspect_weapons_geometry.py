import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

fbx_path = r"E:\Agent\TFTF-blender\3rd-party-models\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

arm = bpy.data.objects.get("Onslaught_ARM")

# Inspect bone locations for Onslaught_ARM
print("=== ONSLAUGHT_ARM KEY BONE POSITIONS ===")
for bname in ['bip_spine_1', 'bip_head', 'bip_hand_L', 'bip_hand_R', 'L_CloudA_ElbowRobo03_XT', 'L_CloudA_ShoulderRobo01_XT']:
    b = arm.data.bones.get(bname)
    if b:
        print(f"Bone {bname}: head={b.head_local}, tail={b.tail_local}")

# Check HeavyMG vs RocketLauncher meshes
hmg_l = bpy.data.objects.get("RB_HeavyMGL_SKEL.mo.dmx")
hmg_r = bpy.data.objects.get("RB_HeavyMGR_SKEL.mo.dmx")
rl_l = bpy.data.objects.get("RB_RocketLauncherL_SKEL.mo.dmx")
rl_r = bpy.data.objects.get("RB_RocketLauncherR_SKEL.mo.dmx")

def get_mesh_bounds(obj):
    verts = [v.co for v in obj.data.vertices]
    min_x = min(v.x for v in verts)
    max_x = max(v.x for v in verts)
    min_y = min(v.y for v in verts)
    max_y = max(v.y for v in verts)
    min_z = min(v.z for v in verts)
    max_z = max(v.z for v in verts)
    return (min_x, max_x), (min_y, max_y), (min_z, max_z)

print("\n=== MESH LOCAL BOUNDS ===")
for obj in [hmg_l, hmg_r, rl_l, rl_r]:
    if obj:
        (x1, x2), (y1, y2), (z1, z2) = get_mesh_bounds(obj)
        print(f"{obj.name}:")
        print(f"   X: [{x1:.2f}, {x2:.2f}], Y: [{y1:.2f}, {y2:.2f}], Z: [{z1:.2f}, {z2:.2f}]")
        print(f"   World Matrix Translation: {obj.matrix_world.translation}")
