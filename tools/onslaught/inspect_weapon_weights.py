import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

fbx_path = r"E:\Agent\TFTF-blender\3rd-party-models\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

arm = bpy.data.objects.get("Onslaught_ARM")

for oname in ["RB_HeavyMGL_SKEL.mo.dmx", "RB_HeavyMGR_SKEL.mo.dmx", "RB_RocketLauncherL_SKEL.mo.dmx", "RB_RocketLauncherR_SKEL.mo.dmx"]:
    obj = bpy.data.objects.get(oname)
    if obj:
        print(f"\n--- {obj.name} ---")
        print(f"Parent: {obj.parent.name if obj.parent else 'None'}")
        print(f"Location: {obj.location}")
        print(f"Modifiers: {[m.name + ' (' + m.type + ')' for m in obj.modifiers]}")
        # Check if vertex group weights exist
        non_empty_vgs = 0
        for v in obj.data.vertices:
            if len(v.groups) > 0:
                non_empty_vgs += 1
        print(f"Vertices with groups: {non_empty_vgs} / {len(obj.data.vertices)}")
