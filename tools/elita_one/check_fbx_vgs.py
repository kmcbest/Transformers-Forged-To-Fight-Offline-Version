import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import bpy
from pathlib import Path

FBX = Path(r"E:\Agent\TFTF-blender\3rd-party-models\transformers-galatic-trials-elita-one\source\Elita_One.fbx")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX))

mesh_obj = bpy.data.objects.get("SK_CH_11.001")
for vg in mesh_obj.vertex_groups:
    if 'index' in vg.name or 'thumb' in vg.name or 'hand' in vg.name:
        cnt = sum(1 for v in mesh_obj.data.vertices for g in v.groups if g.group == vg.index and g.weight > 0.01)
        print(f"VG {vg.name}: {cnt} vertices")
