import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)

fbx_path = r"O:\agent\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"
bpy.ops.import_scene.fbx(filepath=fbx_path)

arm = bpy.data.objects.get("brawl_ARM")
hand_mesh = bpy.data.objects.get("RB_Brawl_CHARSKEL_ArmLoL.mo.dmx")
if hand_mesh:
    print(f"Hand mesh world translation: {hand_mesh.matrix_world.translation}")
    vg_thumb = hand_mesh.vertex_groups.get("bip_thumb_0_L")
    if vg_thumb:
        thumb_vs = [v.co for v in hand_mesh.data.vertices if any(g.group == vg_thumb.index for g in v.groups)]
        print(f"Thumb 0 L verts count: {len(thumb_vs)}")
        if thumb_vs:
            print(f"Thumb local sample: {thumb_vs[0]}")
            world_v0 = hand_mesh.matrix_world @ thumb_vs[0]
            print(f"Thumb world sample: {world_v0}")
