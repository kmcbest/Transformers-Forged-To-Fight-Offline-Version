import bpy
import bmesh
import mathutils

BLEND_FILE = r"tools\demolishor\demolishor_ironhide_side_by_side.blend"
bpy.ops.wm.open_mainfile(filepath=BLEND_FILE)

demo_mesh = bpy.data.objects.get("Demolishor_Mesh")
finger_group_names = [vg.name for vg in demo_mesh.vertex_groups if "finger" in vg.name.lower() or "thumb" in vg.name.lower() or "index" in vg.name.lower() or "middle" in vg.name.lower() or "ring" in vg.name.lower() or "pinky" in vg.name.lower()]
print(f"Finger groups count: {len(finger_group_names)}: {finger_group_names}")

# 1. Clean accidental finger weights from non-hand vertices (Z > 7.0m)
cleaned = 0
for v in demo_mesh.data.vertices:
    if v.co.z > 7.0: # Upper body, shoulders, head, back
        for g in v.groups:
            vg_name = demo_mesh.vertex_groups[g.group].name
            if vg_name in finger_group_names:
                demo_mesh.vertex_groups[g.group].remove([v.index])
                cleaned += 1

print(f"[✓] Cleaned {cleaned} accidental finger weights from upper body.")

# 2. Fix Smokestacks: weight the 4 exhaust pipes (Z > 9.6m) strictly to Spine1 (upper back engine)
vg_spine1 = demo_mesh.vertex_groups.get("Spine1") or demo_mesh.vertex_groups.new(name="Spine1")
bm = bmesh.new()
bm.from_mesh(demo_mesh.data)
visited = set()
islands = []
for v in bm.verts:
    if v in visited: continue
    isl = []
    stack = [v]
    visited.add(v)
    while stack:
        cur = stack.pop()
        isl.append(cur)
        for e in cur.link_edges:
            other = e.other_vert(cur)
            if other not in visited:
                visited.add(other)
                stack.append(other)
    islands.append(isl)

smokestack_verts = 0
for isl in islands:
    center = sum((v.co for v in isl), mathutils.Vector()) / len(isl)
    # The 4 smokestacks are at Z > 9.6m and |X| between 1.0 and 2.2
    if center.z > 9.6 and 0.8 < abs(center.x) < 2.5:
        for v in isl:
            # Clear all groups and assign 100% to Spine1
            for g in demo_mesh.data.vertices[v.index].groups:
                demo_mesh.vertex_groups[g.group].remove([v.index])
            vg_spine1.add([v.index], 1.0, 'REPLACE')
            smokestack_verts += 1

print(f"[✓] Weighted {smokestack_verts} smokestack vertices 100% to Spine1 (no more floating smokestacks!).")

# 3. Fix Symmetrical Shoulder Pads:
# Ensure Left Shoulder Pad (X < -0.5, Z in [8.0, 9.5], on shoulder) is assigned to LeftShoulderPad
vg_lsp = demo_mesh.vertex_groups.get("LeftShoulderPad") or demo_mesh.vertex_groups.new(name="LeftShoulderPad")
vg_rsp = demo_mesh.vertex_groups.get("RightShoulderPad") or demo_mesh.vertex_groups.new(name="RightShoulderPad")

fixed_pads = 0
for isl in islands:
    center = sum((v.co for v in isl), mathutils.Vector()) / len(isl)
    # Shoulder pad armor pieces: Z in [8.2, 9.2], |X| in [0.7, 1.4], Y in [-0.8, 0.6]
    if 8.2 < center.z < 9.2 and 0.7 < abs(center.x) < 1.4:
        target_pad = vg_rsp if center.x > 0 else vg_lsp
        for v in isl:
            for g in demo_mesh.data.vertices[v.index].groups:
                demo_mesh.vertex_groups[g.group].remove([v.index])
            target_pad.add([v.index], 1.0, 'REPLACE')
            fixed_pads += 1

print(f"[✓] Normalized {fixed_pads} shoulder pad vertices symmetrically to Left/Right ShoulderPad.")

# 4. Normalize weights & limit to 4 per vertex (Unity standard)
bpy.context.view_layer.objects.active = demo_mesh
bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL', limit=4)
bpy.ops.object.vertex_group_normalize_all(group_select_mode='ALL', lock_active=False)
bpy.ops.object.mode_set(mode='OBJECT')

bm.free()
bpy.ops.wm.save_as_mainfile(filepath=BLEND_FILE)
print("[✓] Demolishor mesh fully cleaned, articulated, and saved to blend file!")
