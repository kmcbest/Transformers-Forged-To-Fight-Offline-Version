import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\ElitaOne\elita_one_prepared.fbx")

arm = None
mesh = None
for o in bpy.context.scene.objects:
    if o.type == 'ARMATURE':
        arm = o
    elif o.type == 'MESH':
        mesh = o

print("Armature:", arm.name if arm else None)
if arm:
    print(f"Bone count: {len(arm.data.bones)}")
    print("First 10 bones:", [b.name for b in arm.data.bones[:10]])

print("Mesh:", mesh.name if mesh else None)
if mesh:
    print(f"Vertex group count: {len(mesh.vertex_groups)}")
    print("First 10 vertex groups:", [vg.name for vg in mesh.vertex_groups[:10]])
