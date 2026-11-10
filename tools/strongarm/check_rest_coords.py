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
arm.data.pose_position = 'REST'
bpy.context.view_layer.update()

for m in bpy.data.objects:
    if m.type == 'MESH':
        for mod in list(m.modifiers):
            if mod.type == 'ARMATURE':
                bpy.ops.object.select_all(action='DESELECT')
                m.select_set(True)
                bpy.context.view_layer.objects.active = m
                bpy.ops.object.modifier_apply(modifier=mod.name)
        m.parent = None

arm_l = bpy.data.objects["bot:arm_geo_L"]
arm_r = bpy.data.objects["bot:arm_geo_R"]
face = bpy.data.objects["bot:face_geo"]

# Rotate 90 deg around X so Y becomes Z (Blender native height)
for m in [arm_l, arm_r, face]:
    m.rotation_euler = (1.5707963, 0, 0)
    bpy.ops.object.select_all(action='DESELECT')
    m.select_set(True)
    bpy.context.view_layer.objects.active = m
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

print("In Blender coordinates (Z-up, -Y forward):")
print(f"Face center: X={sum(v.co.x for v in face.data.vertices)/len(face.data.vertices):.4f}, Y={sum(v.co.y for v in face.data.vertices)/len(face.data.vertices):.4f}, Z={sum(v.co.z for v in face.data.vertices)/len(face.data.vertices):.4f}")
print(f"Arm L (Blue Siren) center: X={sum(v.co.x for v in arm_l.data.vertices)/len(arm_l.data.vertices):.4f}, Y={sum(v.co.y for v in arm_l.data.vertices)/len(arm_l.data.vertices):.4f}, Z={sum(v.co.z for v in arm_l.data.vertices)/len(arm_l.data.vertices):.4f}")
print(f"Arm R (Red Siren) center:  X={sum(v.co.x for v in arm_r.data.vertices)/len(arm_r.data.vertices):.4f}, Y={sum(v.co.y for v in arm_r.data.vertices)/len(arm_r.data.vertices):.4f}, Z={sum(v.co.z for v in arm_r.data.vertices)/len(arm_r.data.vertices):.4f}")
