import bpy
import mathutils

blend_path = r"E:\Agent\TFTF-blender\tools\elita_one\elita_one_arcee_side_by_side.blend"
bpy.ops.wm.open_mainfile(filepath=blend_path)

elita_mesh = bpy.data.objects.get("Elita_One_Mesh")
bpy.context.scene.frame_set(0)
bpy.context.view_layer.update()

depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = elita_mesh.evaluated_get(depsgraph)
eval_mesh = eval_obj.to_mesh()

print("Analyzing isolated floating components in Elita One...")
# Separate loose parts of eval_mesh to find disconnected components
temp_mesh = eval_mesh.copy()
temp_obj = bpy.data.objects.new("TempEval", temp_mesh)
temp_obj.matrix_world = eval_obj.matrix_world
bpy.context.scene.collection.objects.link(temp_obj)

bpy.ops.object.select_all(action='DESELECT')
temp_obj.select_set(True)
bpy.context.view_layer.objects.active = temp_obj
bpy.ops.mesh.separate(type='LOOSE')
parts = [p for p in bpy.context.selected_objects if p.type == 'MESH']

floating_parts = []
for p in parts:
    coords = [p.matrix_world @ v.co for v in p.data.vertices]
    centroid = sum(coords, mathutils.Vector()) / len(coords)
    # Check if this part's center is floating in the air:
    # (e.g. Z > 8.0, or X > -1.5, or Y < -1.0)
    if centroid.z > 8.0 or centroid.x > -1.5 or centroid.y < -1.0:
        # Check original vertex index on elita_mesh
        # sample first vertex
        v_co = p.data.vertices[0].co
        # find matching vertex in elita_mesh
        floating_parts.append((len(p.data.vertices), centroid))

print(f"Found {len(floating_parts)} floating loose components in Elita One:")
for count, c in floating_parts[:20]:
    print(f"  verts={count}, center=({c.x:.2f}, {c.y:.2f}, {c.z:.2f})")

# Clean up temp parts
bpy.ops.object.delete()
