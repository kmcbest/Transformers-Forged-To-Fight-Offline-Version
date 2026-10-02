import bpy
from pathlib import Path

BLEND = Path(r"E:\Agent\TFTF-blender\tools\elita_one\elita_one_arcee_side_by_side.blend")

bpy.ops.wm.open_mainfile(filepath=str(BLEND))

for o in bpy.data.objects:
    if o.type == 'ARMATURE':
        print(f"Armature: {o.name}")
        print(f"  hide_viewport: {o.hide_viewport}")
        print(f"  hide_get(): {o.hide_get()}")
        print(f"  display_type: {o.data.display_type}")
        print(f"  show_axes: {o.data.show_axes}")
        print(f"  show_names: {o.data.show_names}")
        print(f"  show_in_front: {o.show_in_front}")
