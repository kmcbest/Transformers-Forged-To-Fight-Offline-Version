import bpy
import bmesh
from pathlib import Path

fbx_path = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\ElitaOne\elita_one_prepared.fbx"
out_fbx = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\ElitaOne\elita_one_prepared.fbx"

print("=== Flipping All 654 Inverted Mesh Islands ===")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

mesh_obj = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]
bm = bmesh.new()
bm.from_mesh(mesh_obj.data)
bm.faces.ensure_lookup_table()

# Find connected islands
visited = set()
islands = []
for f in bm.faces:
    if f in visited:
        continue
    island = []
    queue = [f]
    visited.add(f)
    while queue:
        curr = queue.pop()
        island.append(curr)
        for e in curr.edges:
            for nbr in e.link_faces:
                if nbr not in visited:
                    visited.add(nbr)
                    queue.append(nbr)
    islands.append(island)

print(f"Total islands: {len(islands)}")
flipped_count = 0
for isl in islands:
    vol = 0.0
    for f in isl:
        if len(f.verts) >= 3:
            v0 = f.verts[0].co
            for j in range(1, len(f.verts) - 1):
                v1 = f.verts[j].co
                v2 = f.verts[j + 1].co
                vol += v0.dot(v1.cross(v2)) / 6.0
    if vol < -1e-5:
        # Negative volume means inverted normals! Flip all faces in this island!
        for f in isl:
            f.normal_flip()
        flipped_count += 1

print(f"[✓] Flipped {flipped_count} inverted islands!")

bm.to_mesh(mesh_obj.data)
bm.free()

# Re-check
bm2 = bmesh.new()
bm2.from_mesh(mesh_obj.data)
bm2.faces.ensure_lookup_table()
visited2 = set()
remaining_inverted = 0
for f in bm2.faces:
    if f in visited2: continue
    isl = []
    q = [f]
    visited2.add(f)
    while q:
        c = q.pop()
        isl.append(c)
        for e in c.edges:
            for nbr in e.link_faces:
                if nbr not in visited2:
                    visited2.add(nbr)
                    q.append(nbr)
    vol = 0.0
    for f in isl:
        if len(f.verts) >= 3:
            v0 = f.verts[0].co
            for j in range(1, len(f.verts) - 1):
                v1 = f.verts[j].co
                v2 = f.verts[j + 1].co
                vol += v0.dot(v1.cross(v2)) / 6.0
    if vol < -1e-5:
        remaining_inverted += 1
bm2.free()
print(f"[+] Validation: remaining inverted islands: {remaining_inverted} / {len(islands)}")

# Export back to FBX
bpy.ops.export_scene.fbx(
    filepath=out_fbx,
    check_existing=False,
    use_selection=False,
    global_scale=1.0,
    apply_unit_scale=True,
    apply_scale_options='FBX_SCALE_NONE',
    bake_space_transform=False,
    object_types={'ARMATURE', 'MESH'},
    use_mesh_modifiers=True,
    mesh_smooth_type='FACE',
    use_subsurf=False,
    use_armature_deform_only=True,
    add_leaf_bones=False,
    primary_bone_axis='Y',
    secondary_bone_axis='X',
    axis_forward='-Z',
    axis_up='Y'
)
print(f"[✓] Successfully re-exported clean FBX to {out_fbx}")
