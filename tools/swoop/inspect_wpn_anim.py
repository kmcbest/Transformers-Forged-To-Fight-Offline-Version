import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath="3rd-party-models/swoop/01_master/Swoop_pbr.fbx")

arm = bpy.data.objects.get("Bip001")
wpn = bpy.data.objects.get("Swoop_Weapon")

print("Actions in file:")
for act in bpy.data.actions:
    if "attack" in act.name or "idle" in act.name:
        print(f"  {act.name}")

# Let's inspect where Swoop_Weapon vertices are in rest pose vs where Bone_R_Hand is
pts_wpn = [wpn.matrix_world @ v.co for v in wpn.data.vertices]
min_w = [min(p[i] for p in pts_wpn) for i in range(3)]
max_w = [max(p[i] for p in pts_wpn) for i in range(3)]
print(f"Swoop_Weapon world bounds: X=[{min_w[0]:.4f}, {max_w[0]:.4f}], Y=[{min_w[1]:.4f}, {max_w[1]:.4f}], Z=[{min_w[2]:.4f}, {max_w[2]:.4f}]")
