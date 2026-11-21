import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import bpy

FBX_SRC = Path("e:/Agent/TFTF-blender/3rd-party-models/swoop/01_master/Swoop_pbr.fbx")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_SRC))

arm = bpy.data.objects.get("Bip001")
mesh = bpy.data.objects.get("Swoop.001")

# 1. In Rest Pose, what are the vertex bounds of Wing_01 and Wing_02 in mesh local space AND in arm local space?
mat_mesh_to_arm = arm.matrix_world.inverted() @ mesh.matrix_world
print("mat_mesh_to_arm:")
print(mat_mesh_to_arm)

for vgn in ["Bone_L_Wing_01(mirrored)", "Bone_L_Wing_02(mirrored)", "Bone_R_Wing_01", "Bone_R_Wing_02", "bird_Head", "beak", "beak_the bottom"]:
    vg = mesh.vertex_groups.get(vgn)
    pts_m = [v.co for v in mesh.data.vertices if any(g.group == vg.index and g.weight > 0.4 for g in v.groups)]
    pts_a = [mat_mesh_to_arm @ v.co for v in mesh.data.vertices if any(g.group == vg.index and g.weight > 0.4 for g in v.groups)]
    b = arm.data.bones.get(vgn)
    print(f"\nVG {vgn} (n={len(pts_m)}):")
    print(f"  mesh_space: X=[{min(p.x for p in pts_m):.3f}, {max(p.x for p in pts_m):.3f}], Y=[{min(p.y for p in pts_m):.3f}, {max(p.y for p in pts_m):.3f}], Z=[{min(p.z for p in pts_m):.3f}, {max(p.z for p in pts_m):.3f}]")
    print(f"  arm_space : X=[{min(p.x for p in pts_a):.3f}, {max(p.x for p in pts_a):.3f}], Y=[{min(p.y for p in pts_a):.3f}, {max(p.y for p in pts_a):.3f}], Z=[{min(p.z for p in pts_a):.3f}, {max(p.z for p in pts_a):.3f}]")
    if b:
        print(f"  bone head_local in arm_space: {tuple(round(x, 4) for x in b.head_local)}")
        print(f"  bone matrix_local:\n{b.matrix_local}")
