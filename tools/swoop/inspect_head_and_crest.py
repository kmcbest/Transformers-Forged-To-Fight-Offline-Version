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

# Check in Static Pose (Rest Pose) what vertices belong to Bone_Head, bird_Head_02, bird_Head, beak, beak_the bottom, bird_neck
for vgn in ["Bone_Head", "bird_Head_02", "bird_Head", "beak", "beak_the bottom", "bird_neck", "bird_chest"]:
    vg = mesh.vertex_groups.get(vgn)
    pts = [v.co for v in mesh.data.vertices if any(g.group == vg.index and g.weight > 0.4 for g in v.groups)]
    print(f"Rest Pose {vgn:16s} (n={len(pts):4d}): X=[{min(p.x for p in pts):+.3f},{max(p.x for p in pts):+.3f}], Y=[{min(p.y for p in pts):+.3f},{max(p.y for p in pts):+.3f}], Z=[{min(p.z for p in pts):+.3f},{max(p.z for p in pts):+.3f}]")

for bname in ["Bip001 Neck", "Bip001 Head", "Bone_Head", "bird_Head_02", "bird_Head", "beak", "beak_the bottom", "bird_neck"]:
    b = arm.data.bones.get(bname)
    print(f"Bone {bname:16s} head_local={tuple(round(x,4) for x in b.head_local)} matrix_local=\n{b.matrix_local}")
