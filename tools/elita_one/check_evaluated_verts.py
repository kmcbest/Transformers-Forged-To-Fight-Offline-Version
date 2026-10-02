import bpy
import bmesh
from pathlib import Path

BLEND = Path(r"E:\Agent\TFTF-blender\tools\elita_one\elita_one_arcee_side_by_side.blend")

bpy.ops.wm.open_mainfile(filepath=str(BLEND))

scene = bpy.context.scene
scene.frame_set(0)
bpy.context.view_layer.update()

elita = bpy.data.objects.get("Elita_One_Mesh")
arcee = bpy.data.objects.get("Arcee_Mesh")

depsgraph = bpy.context.evaluated_depsgraph_get()
elita_eval = elita.evaluated_get(depsgraph)
mesh_eval = elita_eval.to_mesh()

print(f"Evaluated Elita verts: {len(mesh_eval.vertices)}")

# Find vertices that are far from the main body or unusually high/wide
# The Elita Armature is at location (-2.6, 0, 0)
# In world space:
world_coords = [elita.matrix_world @ v.co for v in mesh_eval.vertices]
# Let's inspect vertices with Z > 8.0 or X < -4.0 or X > -1.0 or Y > 2.0 or Y < -2.0
outliers = []
for i, wc in enumerate(world_coords):
    # If Z > 8.5 (above head) or Z < -0.5
    if wc.z > 8.5 or wc.y > 2.5 or wc.y < -2.5:
        outliers.append((i, wc, elita.data.vertices[i].co))

print(f"Number of outlier verts: {len(outliers)}")
if outliers:
    for i, wc, orig_co in outliers[:20]:
        # check original vertex groups
        vgs = [(elita.vertex_groups[g.group].name, g.weight) for g in elita.data.vertices[i].groups if g.weight > 0.01]
        print(f"Vert {i}: world={wc}, orig={orig_co}, vgs={vgs}")

elita_eval.to_mesh_clear()
