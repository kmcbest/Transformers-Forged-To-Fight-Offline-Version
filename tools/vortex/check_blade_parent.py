import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

bpy.ops.wm.open_mainfile(filepath=r"E:\Agent\TFTF-blender\3rd-party-models\vortex\vortex_master.blend")
for bnm in ["WEP_IonBlade_SKEL.mo_L.dmx", "WEP_IonBlade_SKEL.mo_R.dmx"]:
    obj = bpy.data.objects.get(bnm)
    if obj:
        print(f"Obj {bnm}: parent={obj.parent.name if obj.parent else None}, parent_type={obj.parent_type}, parent_bone={obj.parent_bone}")
        print(f"   loc={obj.location}, rot={obj.rotation_euler}, scale={obj.scale}")
        print(f"   mods={[m.type for m in obj.modifiers]}")
        print(f"   vgs={[vg.name for vg in obj.vertex_groups[:5]]}")
