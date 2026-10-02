import bpy
from pathlib import Path

fbx_path = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\ElitaOne\elita_one_prepared.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

mesh_obj = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]
arm_obj = [o for o in bpy.context.scene.objects if o.type == 'ARMATURE'][0]

print(f"Mesh object: {mesh_obj.name}, scale={mesh_obj.scale}, dimensions={mesh_obj.dimensions}")
print(f"Armature object: {arm_obj.name}, scale={arm_obj.scale}, dimensions={arm_obj.dimensions}")

# Check min and max Z (or Y depending on up axis)
verts = [v.co for v in mesh_obj.data.vertices]
min_z = min(v.z for v in verts)
max_z = max(v.z for v in verts)
min_y = min(v.y for v in verts)
max_y = max(v.y for v in verts)
print(f"Mesh vert bounds local: Y=[{min_y:.2f}, {max_y:.2f}], Z=[{min_z:.2f}, {max_z:.2f}]")
