import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\ElitaOne\elita_one_vehicle.fbx")

for o in bpy.context.scene.objects:
    if o.type == 'MESH':
        xs = [v.co.x for v in o.data.vertices]
        ys = [v.co.y for v in o.data.vertices]
        zs = [v.co.z for v in o.data.vertices]
        print(f"Object: {o.name}")
        print(f"  X: [{min(xs):.2f}, {max(xs):.2f}]")
        print(f"  Y: [{min(ys):.2f}, {max(ys):.2f}]")
        print(f"  Z: [{min(zs):.2f}, {max(zs):.2f}]")
