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

face = next(o for o in bpy.data.objects if "face_geo" in o.name)
chest = next(o for o in bpy.data.objects if "chestCenter" in o.name or "chest" in o.name)
print(f"Face obj: {face.name}")
f_zs = [v.co.z for v in face.data.vertices]
f_ys = [v.co.y for v in face.data.vertices]
f_xs = [v.co.x for v in face.data.vertices]
print(f"Face center: X={sum(f_xs)/len(f_xs):.4f}, Y={sum(f_ys)/len(f_ys):.4f}, Z={sum(f_zs)/len(f_zs):.4f}")

back = next(o for o in bpy.data.objects if "door" in o.name.lower() or "wing" in o.name.lower())
b_zs = [v.co.z for v in back.data.vertices]
b_ys = [v.co.y for v in back.data.vertices]
print(f"Back ({back.name}) center: Y={sum(b_ys)/len(b_ys):.4f}, Z={sum(b_zs)/len(b_zs):.4f}")
