import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

SRC_FBX = r"E:\Agent\TFTF-blender\3rd-party-models\Blitzwing_EW\01_source\H_shandian_G1_M_LOD.fbx"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=SRC_FBX)

mesh = bpy.data.objects['H_shandian_G1_M_Lod']
arm = bpy.data.objects['floor']

print("=== Hand/Finger bones in original armature ===")
for b in arm.data.bones:
    if any(k in b.name.lower() for k in ["hand", "finger", "thumb", "wrist"]):
        print(f"  bone: {b.name}, parent: {b.parent.name if b.parent else None}")

print("\n=== Hand/Finger vertex groups in original mesh ===")
for vg in mesh.vertex_groups:
    if any(k in vg.name.lower() for k in ["hand", "finger", "thumb", "wrist"]):
        cnt = sum(1 for v in mesh.data.vertices for g in v.groups if g.group == vg.index and g.weight > 0.01)
        print(f"  vg: {vg.name}, verts: {cnt}")
