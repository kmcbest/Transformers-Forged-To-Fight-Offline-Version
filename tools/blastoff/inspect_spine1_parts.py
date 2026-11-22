import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

fbx_path = r"O:\agent\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

BLASTOFF_MESH_NAMES = [
    "RB_Blastoff_CHARSKEL_Head.001.dmx",
    "RB_Blastoff_CHARSKEL_ArmLoL.001.dmx",
    "RB_Blastoff_CHARSKEL_ArmLoR.001.dmx",
    "RB_BlastoffWing_STAT.001.dmx",
    "RB_BlastoffWing_STAT.dmx",
]

for name in BLASTOFF_MESH_NAMES:
    o = bpy.data.objects.get(name)
    if o:
        print(f"\nObject: {name}")
        for vg in o.vertex_groups:
            # Check Z range of vertices in this VG
            v_zs = [v.co.z for v in o.data.vertices for g in v.groups if g.group == vg.index and g.weight > 0.4]
            if v_zs:
                print(f"  VG '{vg.name:25s}': count={len(v_zs):5d}, raw Z=[{min(v_zs):.3f}, {max(v_zs):.3f}]")
