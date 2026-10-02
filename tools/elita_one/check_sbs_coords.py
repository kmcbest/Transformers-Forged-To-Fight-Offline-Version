import bpy
import mathutils

blend_path = r"E:\Agent\TFTF-blender\tools\elita_one\elita_one_arcee_side_by_side.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)

for o in bpy.data.objects:
    if o.type in ['MESH', 'ARMATURE', 'CAMERA']:
        print(f"Object: {o.name} (type: {o.type})")
        print(f"  location: {o.location}")
        print(f"  matrix_world translation: {o.matrix_world.translation}")
        if o.type == 'MESH':
            # world coords bounding box
            bb = [o.matrix_world @ mathutils.Vector(corner) for corner in o.bound_box]
            xs = [v.x for v in bb]
            ys = [v.y for v in bb]
            zs = [v.z for v in bb]
            print(f"  bbox X: [{min(xs):.2f}, {max(xs):.2f}], Y: [{min(ys):.2f}, {max(ys):.2f}], Z: [{min(zs):.2f}, {max(zs):.2f}]")
