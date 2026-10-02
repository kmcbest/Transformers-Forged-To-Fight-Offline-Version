import bpy
from pathlib import Path

BLEND = Path(r"E:\Agent\TFTF-blender\tools\elita_one\elita_one_arcee_side_by_side.blend")

bpy.ops.wm.open_mainfile(filepath=str(BLEND))

print("=== ALL DATA COLLECTIONS ===")
print(f"Objects: {[o.name for o in bpy.data.objects]}")
print(f"Meshes: {[m.name for m in bpy.data.meshes]}")
print(f"Armatures: {[a.name for a in bpy.data.armatures]}")
print(f"Curves: {[c.name for c in bpy.data.curves]}")
print(f"Particles: {[p.name for p in bpy.data.particles]}")
print(f"Grease Pencils: {[gp.name for gp in bpy.data.grease_pencils]}")

# Check Elita_One_Mesh viewport overlay / display settings
elita = bpy.data.objects.get("Elita_One_Mesh")
print(f"\nElita display_type: {elita.display_type}")
print(f"Elita show_wire: {elita.show_wire}")

# Check mesh geometry details
m = elita.data
print(f"Vertices: {len(m.vertices)}")
print(f"Edges: {len(m.edges)}")
print(f"Polygons: {len(m.polygons)}")

# Are there loose edges (edges not belonging to any polygon)?
poly_edges = set()
for p in m.polygons:
    for e_idx in p.edge_keys:
        poly_edges.add(tuple(sorted(e_idx)))

loose_edges = [e for e in m.edges if tuple(sorted(e.vertices)) not in poly_edges]
print(f"Loose edges (not in any poly): {len(loose_edges)}")

# In Frame 7, where are vertices?
scene = bpy.context.scene
scene.frame_set(7)
bpy.context.view_layer.update()

depsgraph = bpy.context.evaluated_depsgraph_get()
elita_eval = elita.evaluated_get(depsgraph)
m_eval = elita_eval.to_mesh()

# Let's inspect where the vertices in the bottom-left red box, mid-right red box, top-right red box are!
# In the user's viewport perspective:
# Look at the ground grid lines:
# The green axis line is Y axis!
# The red axis line is X axis!
# Center (0, 0) is at the 3D cursor (red/white circle)!
# Arcee is at +X (viewer's left).
# Elita is at -X (viewer's right).
# BUT the user has rotated their 3D view:
# Notice in user perspective:
# The green line (Y axis) goes from bottom-left to top-right!
# The red line (X axis) goes to the left!
# Look at the bottom-left red box:
# It is located along the green axis line on the ground plane (negative Y or positive Y)!
# Look at the right red boxes:
# They are located on the ground grid or in the air in positive X or negative X!
# Let's find vertices of m_eval that are scattered in those regions!
for i, v in enumerate(m_eval.vertices):
    w_co = elita.matrix_world @ v.co
    # Find vertices that are very isolated or far from Elita's main mesh
    pass

elita_eval.to_mesh_clear()
