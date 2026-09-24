# -*- coding: utf-8 -*-
import bpy
import sys

sys.stdout.reconfigure(encoding='utf-8')

bpy.ops.wm.read_factory_settings(use_empty=True)
fbx_path = r"d:\Agent\tftf\3rd-party-models\transformers-fall-of-cybertron-demolishor\source\transformers fall of cybertron Demolishor.fbx"
bpy.ops.import_scene.fbx(filepath=fbx_path)

mesh = bpy.data.objects.get("RB_DemolishorWeaponArm_SKEL.mo.dmx")
arm = bpy.data.objects.get("Demolishor_ARM")

# Find vertices that have finger weights
finger_vgs = [vg.index for vg in mesh.vertex_groups if "finger" in vg.name.lower()]
print(f"Total finger vertex groups: {len(finger_vgs)}")

finger_verts_count = 0
for v in mesh.data.vertices:
    has_finger = any(g.group in finger_vgs and g.weight > 0.1 for g in v.groups)
    if has_finger:
        finger_verts_count += 1

print(f"Vertices with finger weights: {finger_verts_count} / {len(mesh.data.vertices)}")

# Also check lumbar/shoulder robo vertex groups
robo_vgs = [vg.name for vg in mesh.vertex_groups if "robo" in vg.name.lower()]
print(f"Total 'robo' vertex groups: {len(robo_vgs)}")
for name in sorted(robo_vgs):
    print(" ", name)
