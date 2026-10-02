import bpy
import math
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
FBX_PATH = ROOT / "3rd-party-models" / "transformers-galatic-trials-elita-one" / "source" / "Elita_One.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_PATH))

elita_mesh = bpy.data.objects.get("SK_CH_11.001")
for o in list(bpy.context.scene.collection.objects):
    if o.name not in ["SK_CH_11.001"]:
        bpy.data.objects.remove(o, do_unlink=True)

print(f"Pivot point setting: {bpy.context.scene.tool_settings.transform_pivot_point}")
print(f"Cursor location: {bpy.context.scene.cursor.location}")

bpy.ops.object.select_all(action='DESELECT')
elita_mesh.select_set(True)
bpy.context.view_layer.objects.active = elita_mesh

print(f"Before: Vert 13000 co = {elita_mesh.data.vertices[13000].co}")

SCALE_FACTOR = 8.84 / 8.08
bpy.ops.transform.resize(value=(SCALE_FACTOR, SCALE_FACTOR, SCALE_FACTOR))
bpy.ops.transform.rotate(value=math.radians(90.0), orient_axis='Z')
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

print(f"After:  Vert 13000 co = {elita_mesh.data.vertices[13000].co}")
