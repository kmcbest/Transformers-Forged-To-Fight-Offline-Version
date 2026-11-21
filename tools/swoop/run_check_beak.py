import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import subprocess

blender_script = """
import bpy
import sys

bpy.ops.import_scene.fbx(filepath=r"E:/Agent/TFTF-blender/toolchain/unity_build_project/Assets/Swoop/swoop_prepared.fbx")

mesh_objs = [o for o in bpy.data.objects if o.type == 'MESH']
for o in mesh_objs:
    print(f"Mesh {o.name}")
    # find forwardmost vertices in world space
    beak_verts = []
    for v in o.data.vertices:
        w_co = o.matrix_world @ v.co
        # In Unity: Y is up, Z is forward.
        # In Blender after FBX import with default settings: Z is up, Y is back or forward.
        # Let's inspect coordinates
        beak_verts.append(w_co)
    if beak_verts:
        # sort by Z (height)
        chest = [v for v in beak_verts if 5.0 <= v.z <= 9.0 and abs(v.x) < 0.5]
        if chest:
            chest.sort(key=lambda c: c.y)
            print("  Chest min Y:", chest[0])
            print("  Chest max Y:", chest[-1])

arm = [o for o in bpy.data.objects if o.type == 'ARMATURE'][0]
for b in arm.data.bones:
    if b.name in ["Hips", "Spine", "Spine1"]:
        print(f"Bone {b.name}: head = {arm.matrix_world @ b.head}")
"""

with open("tools/swoop/check_beak_blender.py", "w", encoding="utf-8") as f:
    f.write(blender_script)

res = subprocess.run([r"e:\Agent\TFTF-blender\toolchain\blender\blender.exe", "--background", "--python", "tools/swoop/check_beak_blender.py"], capture_output=True, text=True)
print(res.stdout[-1500:])
