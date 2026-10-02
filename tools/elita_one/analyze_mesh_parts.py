import bpy
import mathutils

blend_path = r"E:\Agent\TFTF-blender\tools\elita_one\elita_one_arcee_side_by_side.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)

print("Listing all mesh objects in scene:")
for o in bpy.data.objects:
    if o.type == 'MESH':
        print(f"Mesh Object: {o.name}, vertices: {len(o.data.vertices)}")
        # Check if this mesh has separate loose parts
        bpy.ops.object.select_all(action='DESELECT')
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        bpy.ops.mesh.separate(type='LOOSE')
        parts = [p for p in bpy.context.selected_objects if p.type == 'MESH']
        print(f"  Loose parts in {o.name}: {len(parts)}")
        small_parts = []
        for p in parts:
            coords = [p.matrix_world @ v.co for v in p.data.vertices]
            xs = [c.x for c in coords]; ys = [c.y for c in coords]; zs = [c.z for c in coords]
            dx, dy, dz = max(xs)-min(xs), max(ys)-min(ys), max(zs)-min(zs)
            centroid = sum(coords, mathutils.Vector()) / len(coords)
            if len(p.data.vertices) < 100:
                small_parts.append((len(p.data.vertices), centroid, (dx, dy, dz)))
        print(f"  Small parts (<100 verts) in {o.name}: {len(small_parts)}")
        for count, c, size in small_parts[:10]:
            print(f"    verts={count}, center=({c.x:.2f}, {c.y:.2f}, {c.z:.2f}), size=({size[0]:.2f}, {size[1]:.2f}, {size[2]:.2f})")
        # Undo separate by joining back
        bpy.ops.object.join()
