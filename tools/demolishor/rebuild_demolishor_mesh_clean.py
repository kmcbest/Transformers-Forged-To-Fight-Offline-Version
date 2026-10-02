import bpy
import bmesh
import mathutils
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BLEND_SBS = ROOT / "demolishor_ironhide_side_by_side.blend"
BLEND_P2 = ROOT / "demolishor_phase2_inspect.blend"

print("=== Rebuilding Demolishor Mesh Cleanly from Phase 2 Inspect ===")
bpy.ops.wm.open_mainfile(filepath=str(BLEND_SBS))

# 1. Load clean mesh data from BLEND_P2
with bpy.data.libraries.load(str(BLEND_P2), link=False) as (data_from, data_to):
    if "cha_demolishor_gs_01" in data_from.objects:
        data_to.objects = ["cha_demolishor_gs_01"]

clean_obj = bpy.data.objects.get("cha_demolishor_gs_01")
demo_mesh = bpy.data.objects.get("Demolishor_Mesh")
demo_arm = bpy.data.objects.get("Demolishor_Armature")

# Replace geometry and vertex groups with clean uncorrupted phase 2 data
demo_mesh.data = clean_obj.data.copy()
bpy.data.objects.remove(clean_obj, do_unlink=True)
print(f"[✓] Replaced Demolishor_Mesh with clean geometry ({len(demo_mesh.data.vertices)} verts, {len(demo_mesh.vertex_groups)} VGs).")

# 2. Fix Smokestacks: weight the 4 exhaust pipes (Z > 9.6m) strictly to Spine1
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
collar_verts = 0
head_verts = 0

vg_head = demo_mesh.vertex_groups.get("Head") or demo_mesh.vertex_groups.new(name="Head")

for isl in islands:
    center = sum((v.co for v in isl), mathutils.Vector()) / len(isl)
    # 4 smokestacks at Z > 9.6m and |X| between 0.8 and 2.5
    if center.z > 9.6 and 0.8 < abs(center.x) < 2.5:
        for v in isl:
            for g in demo_mesh.data.vertices[v.index].groups:
                demo_mesh.vertex_groups[g.group].remove([v.index])
            vg_spine1.add([v.index], 1.0, 'REPLACE')
            smokestack_verts += 1
    # Collar armor at Z in [8.2, 9.2], |X| in [0.7, 1.4]: assign to Spine1 so it DOES NOT flap outwards like wings!
    elif 8.2 < center.z < 9.2 and 0.7 < abs(center.x) < 1.4:
        for v in isl:
            for g in demo_mesh.data.vertices[v.index].groups:
                demo_mesh.vertex_groups[g.group].remove([v.index])
            vg_spine1.add([v.index], 1.0, 'REPLACE')
            collar_verts += 1
    # Head at Z in [8.3, 9.8], |X| < 0.6: assign to Head
    elif 8.3 < center.z < 9.8 and abs(center.x) < 0.6 and center.y > 0.0:
        for v in isl:
            for g in demo_mesh.data.vertices[v.index].groups:
                demo_mesh.vertex_groups[g.group].remove([v.index])
            vg_head.add([v.index], 1.0, 'REPLACE')
            head_verts += 1

print(f"[✓] Weighted {smokestack_verts} smokestack vertices to Spine1.")
print(f"[✓] Weighted {collar_verts} collar armor vertices to Spine1 (no flapping shoulder pads).")
print(f"[✓] Weighted {head_verts} head vertices to Head.")

# 3. Articulate Hands & Fingers strictly from hand islands (NEVER touching chest or torso)
# Right Hand: X > 1.66, Z in [3.5, 5.05]
# Left Hand: X < -1.66, Z in [3.5, 5.05]

def articulate_hand(is_right):
    prefix = "Right" if is_right else "Left"
    vg_hand = demo_mesh.vertex_groups.get(f"{prefix}Hand")
    if not vg_hand: return
    
    sign = 1.0 if is_right else -1.0
    
    # Finger VGs
    vg_t1 = demo_mesh.vertex_groups.get(f"{prefix}HandThumb1") or demo_mesh.vertex_groups.new(name=f"{prefix}HandThumb1")
    vg_t2 = demo_mesh.vertex_groups.get(f"{prefix}HandThumb2") or demo_mesh.vertex_groups.new(name=f"{prefix}HandThumb2")
    vg_i1 = demo_mesh.vertex_groups.get(f"{prefix}HandIndex1") or demo_mesh.vertex_groups.new(name=f"{prefix}HandIndex1")
    vg_i2 = demo_mesh.vertex_groups.get(f"{prefix}HandIndex2") or demo_mesh.vertex_groups.new(name=f"{prefix}HandIndex2")
    vg_m1 = demo_mesh.vertex_groups.get(f"{prefix}HandMiddle1") or demo_mesh.vertex_groups.new(name=f"{prefix}HandMiddle1")
    vg_m2 = demo_mesh.vertex_groups.get(f"{prefix}HandMiddle2") or demo_mesh.vertex_groups.new(name=f"{prefix}HandMiddle2")
    vg_r1 = demo_mesh.vertex_groups.get(f"{prefix}HandRing1") or demo_mesh.vertex_groups.new(name=f"{prefix}HandRing1")
    vg_r2 = demo_mesh.vertex_groups.get(f"{prefix}HandRing2") or demo_mesh.vertex_groups.new(name=f"{prefix}HandRing2")
    vg_p1 = demo_mesh.vertex_groups.get(f"{prefix}HandPinky1") or demo_mesh.vertex_groups.new(name=f"{prefix}HandPinky1")
    vg_p2 = demo_mesh.vertex_groups.get(f"{prefix}HandPinky2") or demo_mesh.vertex_groups.new(name=f"{prefix}HandPinky2")
    
    hand_islands = []
    for isl in islands:
        cos = np.array([demo_mesh.data.vertices[v.index].co for v in isl])
        center = cos.mean(axis=0)
        # Strictly verify this island is inside hand bounding box
        if (sign * center[0] > 1.6) and (3.4 < center[2] < 5.1):
            hand_islands.append((isl, center))
            
    print(f"Found {len(hand_islands)} islands in {prefix} Hand.")
    
    # Sort by Y (forward/inward to backward/outward)
    hand_islands.sort(key=lambda item: item[1][1], reverse=True)
    
    for isl, center in hand_islands:
        y = center[1]
        z = center[2]
        v_indices = [v.index for v in isl]
        
        # Palm / wrist: large piece (e.g. 65 verts) or near wrist (Z > 4.5 and |X| < 2.5)
        if len(isl) > 40:
            # Palm stays on Hand
            continue
            
        # Thumb: Y in [0.75, 1.1]
        if y > 0.74:
            tgt = vg_t2 if z < 4.0 else vg_t1
        # Index: Y in [0.58, 0.74]
        elif y > 0.58:
            tgt = vg_i2 if z < 3.9 else vg_i1
        # Middle: Y in [0.35, 0.58]
        elif y > 0.35:
            tgt = vg_m2 if z < 3.9 else vg_m1
        # Ring: Y in [0.10, 0.35]
        elif y > 0.10:
            tgt = vg_r2 if z < 3.9 else vg_r1
        # Pinky: Y <= 0.10
        else:
            tgt = vg_p2 if z < 3.9 else vg_p1
            
        for idx in v_indices:
            vg_hand.remove([idx])
            tgt.add([idx], 1.0, 'REPLACE')

articulate_hand(is_right=True)
articulate_hand(is_right=False)

# 4. Strict Safety Assertion: Verify that ZERO vertices with |X| < 1.5 or Z > 5.5 have finger weights!
finger_names = [vg.name for vg in demo_mesh.vertex_groups if any(k in vg.name.lower() for k in ["thumb", "index", "middle", "ring", "pinky"])]
violations = []
for v in demo_mesh.data.vertices:
    for g in v.groups:
        vg_name = demo_mesh.vertex_groups[g.group].name
        if vg_name in finger_names:
            if abs(v.co.x) < 1.5 or v.co.z > 5.5 or v.co.z < 3.0:
                violations.append((v.index, vg_name, v.co))

if violations:
    raise RuntimeError(f"FATAL: Found {len(violations)} non-hand vertices with finger weights! Example: {violations[0]}")
else:
    print("[✓] STRICT SAFETY CHECK PASSED: Exactly 0 non-hand vertices have finger weights!")

# 5. Normalize weights & limit to 4 per vertex
bpy.context.view_layer.objects.active = demo_mesh
bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL', limit=4)
bpy.ops.object.vertex_group_normalize_all(group_select_mode='ALL', lock_active=False)
bpy.ops.object.mode_set(mode='OBJECT')

bm.free()
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_SBS))
print(f"[✓] Successfully saved clean, articulated Demolishor to: {BLEND_SBS}")
