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
if arm.animation_data:
    arm.animation_data_clear()
arm.data.pose_position = 'REST'

meshes = [o for o in bpy.data.objects if o.type == 'MESH']
min_z, max_z = min(v.co.z for m in meshes for v in m.data.vertices), max(v.co.z for m in meshes for v in m.data.vertices)
raw_height = max_z - min_z
print(f"Strongarm raw mesh height: {raw_height} (min_z={min_z}, max_z={max_z})")

# In Blender, Z is Up, Y is Forward/Backward.
# Check key bones
for bname in ["bot:jt_pelvis", "bot:jt_spine1", "bot:jt_head", "bot:jt_shoulder_L", "bot:jt_elbow_L", "bot:jt_wrist_L", "bot:jt_hip_L", "bot:jt_knee_L", "bot:jt_ankle_L"]:
    b = arm.data.bones.get(bname)
    if b:
        print(f"  {bname:20s}: head = ({b.head_local.x:.4f}, {b.head_local.y:.4f}, {b.head_local.z:.4f})")
