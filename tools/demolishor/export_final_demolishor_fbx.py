import sys
import bpy
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
BLEND_FILE = ROOT / "tools" / "demolishor" / "demolishor_ironhide_side_by_side.blend"
OUT_FBX = ROOT / "toolchain" / "unity_build_project" / "Assets" / "Demolishor" / "demolishor_prepared.fbx"

print(f"=== Exporting Final Clean Demolishor FBX from {BLEND_FILE.name} ===")
bpy.ops.wm.open_mainfile(filepath=str(BLEND_FILE))

# Select only Demolishor mesh and Demolishor armature
demo_mesh = bpy.data.objects.get("Demolishor_Mesh")
demo_arm = bpy.data.objects.get("Demolishor_Armature")

if not demo_mesh or not demo_arm:
    raise RuntimeError("Missing Demolishor mesh or armature!")

# Temporarily reset Demolishor location to (0,0,0) for clean export centered at origin
demo_arm.location = (0.0, 0.0, 0.0)
demo_mesh.location = (0.0, 0.0, 0.0)

# Clear any active action / rest pose for FBX export
if demo_arm.animation_data:
    demo_arm.animation_data.action = None

for pb in demo_arm.pose.bones:
    pb.rotation_euler = (0, 0, 0)
    pb.rotation_quaternion = (1, 0, 0, 0)
    pb.location = (0, 0, 0)
    pb.scale = (1, 1, 1)

bpy.context.view_layer.update()

# Set names expected by Unity pipeline
demo_mesh.name = "cha_demolishor_gs_00"
demo_arm.name = "character_model"

# Normalize weights & limit to 4 influences
bpy.context.view_layer.objects.active = demo_mesh
bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL', limit=4)
bpy.ops.object.vertex_group_normalize_all(group_select_mode='ALL', lock_active=False)
bpy.ops.object.mode_set(mode='OBJECT')

bpy.ops.object.select_all(action='DESELECT')
demo_mesh.select_set(True)
demo_arm.select_set(True)
bpy.context.view_layer.objects.active = demo_arm

OUT_FBX.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.fbx(
    filepath=str(OUT_FBX),
    use_selection=True,
    bake_anim=False,
    add_leaf_bones=False
)

print(f"[✓] Successfully exported FBX: {OUT_FBX} ({OUT_FBX.stat().st_size / 1024:.1f} KB)")
