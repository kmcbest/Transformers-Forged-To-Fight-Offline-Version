import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

fbx_path = Path(r"E:\Agent\RID_game\strongarm_zip_extracted\source\Strongarm.fbx")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(fbx_path))

arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
print(f"Armature: {arm.name}")
print(f"Pose position: {arm.data.pose_position}")

# Check action list
print(f"Actions in blend: {[a.name for a in bpy.data.actions]}")
if arm.animation_data and arm.animation_data.action:
    print(f"Active action: {arm.animation_data.action.name}")

# Check bone transforms in rest vs pose
for pb in arm.pose.bones[:10]:
    b = arm.data.bones[pb.name]
    print(f"Bone {pb.name}:")
    print(f"  Rest head: {b.head_local}, tail: {b.tail_local}")
    print(f"  Pose loc: {pb.location}, rot: {pb.rotation_quaternion or pb.rotation_euler}, scale: {pb.scale}")

# Check meshes: are their transforms (0,0,0) or do they have matrix offsets?
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
for m in meshes[:5]:
    print(f"Mesh {m.name}: loc={m.location}, rot={m.rotation_euler}, scale={m.scale}, parent={m.parent.name if m.parent else None}")
