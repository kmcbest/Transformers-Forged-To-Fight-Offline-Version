# -*- coding: utf-8 -*-
"""
Export Demolishor from demolishor_phase2_inspect.blend to Unity project:
toolchain/unity_build_project/Assets/Demolishor/demolishor_prepared.fbx
"""
import sys
import bpy
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parent.parent.parent
INSPECT_BLEND = ROOT / "tools" / "demolishor" / "demolishor_phase2_inspect.blend"
OUT_FBX = ROOT / "toolchain" / "unity_build_project" / "Assets" / "Demolishor" / "demolishor_prepared.fbx"

print(f"=== Exporting Prepared FBX from {INSPECT_BLEND.name} ===")
bpy.ops.wm.open_mainfile(filepath=str(INSPECT_BLEND))

# 1. Remove ghost reference and any extra cameras/lights
to_remove = ["Ironhide_Ghost_Reference", "Camera", "Light", "Bone_Visuals"]
for name in to_remove:
    obj = bpy.data.objects.get(name)
    if obj:
        bpy.data.objects.remove(obj, do_unlink=True)

mesh = bpy.data.objects.get("cha_demolishor_gs_01") or bpy.data.objects.get("cha_demolishor_gs_00")
arm = bpy.data.objects.get("Ironhide_Reference_Armature") or bpy.data.objects.get("character_model")

if not mesh or not arm:
    print(f"[!] Error: mesh or arm not found!")
    sys.exit(1)

# 2. Reset armature to pristine rest pose
if arm.animation_data:
    arm.animation_data.action = None
for pb in arm.pose.bones:
    pb.rotation_euler = (0, 0, 0)
    pb.rotation_quaternion = (1, 0, 0, 0)
    pb.location = (0, 0, 0)
    pb.scale = (1, 1, 1)

bpy.context.view_layer.update()

# 3. Rename according to pipeline convention
mesh.name = "cha_demolishor_gs_00"
arm.name = "character_model"

# Ensure weights are normalized and limited to 4 per vertex (Unity standard)
bpy.context.view_layer.objects.active = mesh
bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL', limit=4)
bpy.ops.object.vertex_group_normalize_all(group_select_mode='ALL', lock_active=False)
bpy.ops.object.mode_set(mode='OBJECT')
print("[✓] Weights normalized and limited to 4 influences per vertex.")

# 4. Select only mesh and armature
bpy.ops.object.select_all(action='DESELECT')
mesh.select_set(True)
arm.select_set(True)
bpy.context.view_layer.objects.active = arm

OUT_FBX.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.fbx(
    filepath=str(OUT_FBX),
    use_selection=True,
    bake_anim=False,
    add_leaf_bones=False
)

print(f"[✓] Successfully exported FBX: {OUT_FBX} ({OUT_FBX.stat().st_size / 1024:.1f} KB)")
