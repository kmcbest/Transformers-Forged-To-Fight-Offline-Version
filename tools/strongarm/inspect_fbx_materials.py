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

mesh_objs = [o for o in bpy.data.objects if o.type == 'MESH']
print(f"Total mesh objects: {len(mesh_objs)}")

mat_usage = {}
for m in mesh_objs:
    mats = [slot.material.name if slot.material else "None" for slot in m.material_slots]
    for mat in mats:
        mat_usage.setdefault(mat, []).append(m.name)

print("\n--- Material Usage ---")
for mat, objs in sorted(mat_usage.items()):
    print(f"Material '{mat}': {len(objs)} objects (e.g. {objs[:3]})")
