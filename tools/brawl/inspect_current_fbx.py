import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
import json
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
fbx_r = ROOT / "toolchain/unity_build_project/Assets/Brawl/brawl_robot.fbx"
donor_json = ROOT / "3rd-party-models/Brawl/00_donor_reference/donor_summary.json"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(fbx_r))

print("=== IMPORTED brawl_robot.fbx OBJECTS ===")
for o in bpy.data.objects:
    print(f"  {o.type:8s} {o.name:25s} loc={tuple(round(x,3) for x in o.location)} rot={tuple(round(x,3) for x in o.rotation_euler)} scl={tuple(round(x,3) for x in o.scale)}")

mesh_obj = [o for o in bpy.data.objects if o.type == 'MESH'][0]
arm_obj = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]

# Check left vs right vertex groups vs X coordinates
vg_names = {vg.index: vg.name for vg in mesh_obj.vertex_groups}
for check_vg in ["LeftArm", "RightArm", "LeftForeArm", "RightForeArm", "LeftHand", "Hips", "Spine1"]:
    idx = mesh_obj.vertex_groups[check_vg].index if check_vg in mesh_obj.vertex_groups else -1
    if idx < 0:
        print(f"  VG {check_vg}: MISSING")
        continue
    pts = [mesh_obj.matrix_world @ v.co for v in mesh_obj.data.vertices if any(g.group == idx and g.weight > 0.5 for g in v.groups)]
    if pts:
        xs = [p.x for p in pts]; ys = [p.y for p in pts]; zs = [p.z for p in pts]
        b = arm_obj.data.bones.get(check_vg)
        bp = (arm_obj.matrix_world @ b.head_local) if b else None
        print(f"  VG {check_vg:14s}: n={len(pts):4d} X=[{min(xs):.2f},{max(xs):.2f}] Y=[{min(ys):.2f},{max(ys):.2f}] Z=[{min(zs):.2f},{max(zs):.2f}] | Bone={tuple(round(c,2) for c in bp) if bp else None}")
    else:
        print(f"  VG {check_vg:14s}: 0 verts")

# Check donor_summary.json hierarchy
donor = json.loads(donor_json.read_text(encoding='utf-8'))
print("\n=== DONOR MEGATRON SUMMARY KEYS ===")
print("meshes:", {k: (len(v['boneHashes']), len(v['bindposes'])) for k, v in donor['meshes'].items()})
print("avatars:", list(donor['avatars'].keys()))
avatar = donor['avatars']['cha_megatron_cin_rotf_00Avatar']['tos']
print("sample avatar paths:")
for k, v in list(avatar.items())[:20]:
    print(f"  {k}: {v}")
