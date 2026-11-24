import sys
from pathlib import Path
import bpy
from mathutils import Vector

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

ROOT = Path(r"E:\Agent\TFTF-blender")
SRC_DIR = ROOT / "3rd-party-models" / "Blitzwing_EW" / "01_source"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(SRC_DIR / "H_shandian_G1_M_LOD.fbx"))

# Apply parent transform to world
mesh = bpy.data.objects.get("H_shandian_G1_M_Lod")
arm = bpy.data.objects.get("floor")

bpy.ops.object.select_all(action='DESELECT')
for o in [mesh, arm]:
    o.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')

# Now check world transforms
print(f"Mesh world loc={mesh.location}, scale={mesh.scale}, matrix_scale={mesh.matrix_world.to_scale()}")
print(f"Arm world loc={arm.location}, scale={arm.scale}, matrix_scale={arm.matrix_world.to_scale()}")

bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# Now check bone head vs vertex
print(f"After apply transform:")
print(f"Arm matrix_scale={arm.matrix_world.to_scale()}")
b = arm.data.bones.get("Bip001 Head")
print(f"Bip001 Head head_local: {b.head_local}")
zs = [(mesh.matrix_world @ v.co).z for v in mesh.data.vertices]
print(f"Mesh Z range: [{min(zs):.4f}, {max(zs):.4f}]")
