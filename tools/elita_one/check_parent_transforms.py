import bpy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
FBX_PATH = ROOT / "3rd-party-models" / "transformers-galatic-trials-elita-one" / "source" / "Elita_One.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_PATH))

obj = bpy.data.objects.get("SK_CH_11.001")
arm = bpy.data.objects.get("SK_CH_11")

print(f"Mesh obj.matrix_world:\n{obj.matrix_world}")
print(f"Mesh obj.matrix_local:\n{obj.matrix_local}")
print(f"Mesh obj.parent: {obj.parent}")
print(f"Mesh obj.matrix_parent_inverse:\n{obj.matrix_parent_inverse}")
print(f"Arm obj.matrix_world:\n{arm.matrix_world}")

# Check vert 13000 in raw mesh data vs world matrix
v_raw = obj.data.vertices[13000].co
v_world = obj.matrix_world @ v_raw
print(f"Vert 13000 data: {v_raw}")
print(f"Vert 13000 world (with parent): {v_world}")

# Now unlink parent
bpy.ops.object.select_all(action='DESELECT')
obj.select_set(True)
bpy.context.view_layer.objects.active = obj
bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
print(f"After parent_clear KEEP_TRANSFORM, data vert 13000: {obj.data.vertices[13000].co}")
print(f"After parent_clear, obj.matrix_world:\n{obj.matrix_world}")
print(f"World coord: {obj.matrix_world @ obj.data.vertices[13000].co}")

# Now apply transform
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
print(f"After transform_apply, data vert 13000: {obj.data.vertices[13000].co}")
