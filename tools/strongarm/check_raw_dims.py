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
print(f"RAW Armature: {arm.name}, rot={arm.rotation_euler}, scale={arm.scale}")
mesh_objs = [o for o in bpy.data.objects if o.type == 'MESH']
all_zs = [v.co.z for m in mesh_objs for v in m.data.vertices]
all_ys = [v.co.y for m in mesh_objs for v in m.data.vertices]
all_xs = [v.co.x for m in mesh_objs for v in m.data.vertices]
print(f"RAW Meshes count: {len(mesh_objs)}")
print(f"RAW X range: [{min(all_xs):.4f}, {max(all_xs):.4f}], span={max(all_xs)-min(all_xs):.4f}")
print(f"RAW Y range: [{min(all_ys):.4f}, {max(all_ys):.4f}], span={max(all_ys)-min(all_ys):.4f}")
print(f"RAW Z range: [{min(all_zs):.4f}, {max(all_zs):.4f}], span={max(all_zs)-min(all_zs):.4f}")

# Check first mesh parent and transform
m0 = mesh_objs[0]
print(f"m0 ({m0.name}) loc={m0.location}, rot={m0.rotation_euler}, scale={m0.scale}, parent={m0.parent}")
