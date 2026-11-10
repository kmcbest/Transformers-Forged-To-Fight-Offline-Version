import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r"E:\Agent\RID_game\strongarm_zip_extracted\source\Strongarm.fbx")

face = bpy.data.objects.get("bot:face_geo")
back = bpy.data.objects.get("bot:chestBackTop_geo")
face_z = sum(v.co.z for v in face.data.vertices) / len(face.data.vertices)
back_z = sum(v.co.z for v in back.data.vertices) / len(back.data.vertices)
print(f"Face Z in raw FBX: {face_z:.4f}")
print(f"Back Z in raw FBX: {back_z:.4f}")
