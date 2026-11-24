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

mesh = bpy.data.objects.get("H_shandian_G1_M_Lod")
arm = bpy.data.objects.get("floor")
if arm:
    arm.animation_data_clear()
    arm.data.pose_position = 'REST'
bpy.context.view_layer.update()

verts_world = [mesh.matrix_world @ v.co for v in mesh.data.vertices]
xs = [v.x for v in verts_world]
ys = [v.y for v in verts_world]
zs = [v.z for v in verts_world]

print(f"Mesh World Bounds:")
print(f"  X: [{min(xs):.4f}, {max(xs):.4f}] (span={max(xs)-min(xs):.4f})")
print(f"  Y: [{min(ys):.4f}, {max(ys):.4f}] (span={max(ys)-min(ys):.4f})")
print(f"  Z: [{min(zs):.4f}, {max(zs):.4f}] (span={max(zs)-min(zs):.4f})")

# Check bone heads in world space
for bname in ['Bip001 Head', 'Bip001 Pelvis', 'Bip001 L UpperArm', 'Bip001 R UpperArm', 'Bip001 L Hand', 'Bip001 R Hand', 'Bip001 L Foot', 'Bip001 R Foot']:
    b = arm.data.bones.get(bname)
    if b:
        w_head = arm.matrix_world @ b.head_local
        print(f"  Bone {bname:20s}: {w_head}")
