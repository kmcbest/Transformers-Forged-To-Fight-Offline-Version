# -*- coding: utf-8 -*-
import bpy
import sys

sys.stdout.reconfigure(encoding='utf-8')

bpy.ops.wm.read_factory_settings(use_empty=True)
fbx_path = r"d:\Agent\tftf\3rd-party-models\transformers-fall-of-cybertron-demolishor\source\transformers fall of cybertron Demolishor.fbx"
bpy.ops.import_scene.fbx(filepath=fbx_path)

mesh = bpy.data.objects.get("RB_DemolishorWeaponArm_SKEL.mo.dmx")
vgs = [vg.name for vg in mesh.vertex_groups]
print(f"Total vertex groups in Demolishor: {len(vgs)}")
print("Vertex groups list:")
for i, name in enumerate(sorted(vgs)):
    print(f"  {name}")
