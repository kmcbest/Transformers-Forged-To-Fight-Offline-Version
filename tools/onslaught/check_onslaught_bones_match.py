import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

fbx_path = r"E:\Agent\TFTF-blender\3rd-party-models\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

onslaught_arm = bpy.data.objects.get("Onslaught_ARM")
bone_names = set(b.name for b in onslaught_arm.data.bones)

rl_l = bpy.data.objects.get("RB_RocketLauncherL_SKEL.mo.dmx")
if rl_l:
    vg_names = [vg.name for vg in rl_l.vertex_groups]
    matched = [name for name in vg_names if name in bone_names]
    print(f"RB_RocketLauncherL vertex groups: {len(vg_names)}")
    print(f"Matched with Onslaught_ARM bones: {len(matched)} / {len(vg_names)}")
    print(f"Matched names: {matched}")

hmg_l = bpy.data.objects.get("RB_HeavyMGL_SKEL.mo.dmx")
if hmg_l:
    vg_names = [vg.name for vg in hmg_l.vertex_groups]
    matched = [name for name in vg_names if name in bone_names]
    print(f"\nRB_HeavyMGL vertex groups: {len(vg_names)}")
    print(f"Matched with Onslaught_ARM bones: {len(matched)} / {len(vg_names)}")
    print(f"Sample matched names: {matched[:10]}")

vh_obj = bpy.data.objects.get("VH.dmx")
vh_arm = bpy.data.objects.get("Onslaught_VH_ARM")
vh_bones = set(b.name for b in vh_arm.data.bones)
if vh_obj:
    vg_names = [vg.name for vg in vh_obj.vertex_groups]
    matched = [name for name in vg_names if name in vh_bones]
    print(f"\nVH.dmx vertex groups: {len(vg_names)}")
    print(f"Matched with Onslaught_VH_ARM bones: {len(matched)} / {len(vg_names)}")
    print(f"First 10 matched: {matched[:10]}")
