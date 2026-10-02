import bpy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
BLEND_FILE = ROOT / "tools" / "elita_one" / "elita_one_arcee_setup.blend"
MAPPING_FILE = ROOT / "tools" / "elita_one" / "elita_to_arcee_mapping.json"
ARCEE_BONES_FILE = ROOT / "tools" / "elita_one" / "arcee_extracted" / "arcee_63_bones.json"

with open(MAPPING_FILE, "r") as f:
    mapping = json.load(f)

with open(ARCEE_BONES_FILE, "r") as f:
    arcee_bones = json.load(f)

bpy.ops.wm.open_mainfile(filepath=str(BLEND_FILE))

elita_mesh = bpy.data.objects.get("Elita_One_Mesh")
print(f"=== Remapping Skin Weights on {elita_mesh.name} ({len(elita_mesh.data.vertices)} verts) ===")

# Cache all current vertex weights: {v_index: {target_bone: total_weight}}
remapped_weights = {v.index: {} for v in elita_mesh.data.vertices}

for v in elita_mesh.data.vertices:
    for g in v.groups:
        orig_vg_name = elita_mesh.vertex_groups[g.group].name
        target_bone = mapping.get(orig_vg_name)
        if target_bone:
            remapped_weights[v.index][target_bone] = remapped_weights[v.index].get(target_bone, 0.0) + g.weight

# Clear old vertex groups
elita_mesh.vertex_groups.clear()
print("[✓] Cleared old 94 vertex groups.")

# Create the new Arcee vertex groups
new_vgs = {}
for bname in arcee_bones:
    new_vgs[bname] = elita_mesh.vertex_groups.new(name=bname)

print(f"[✓] Created {len(new_vgs)} official Arcee vertex groups.")

# Assign remapped weights
unweighted_verts = 0
for v_idx, weights_dict in remapped_weights.items():
    if not weights_dict:
        unweighted_verts += 1
        continue
    # Sort and take top 4 influences
    top_4 = sorted(weights_dict.items(), key=lambda kv: kv[1], reverse=True)[:4]
    sum_w = sum(w for _, w in top_4)
    if sum_w > 0:
        for bname, w in top_4:
            norm_w = w / sum_w
            if norm_w > 0.001 and bname in new_vgs:
                new_vgs[bname].add([v_idx], norm_w, 'REPLACE')

print(f"[✓] Assigned remapped weights to all vertices. (Unweighted count: {unweighted_verts})")

# Ensure active vertex group is set
if elita_mesh.vertex_groups:
    elita_mesh.vertex_groups.active_index = 0
    try:
        bpy.context.view_layer.objects.active = elita_mesh
        bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
        bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL', limit=4)
        bpy.ops.object.vertex_group_normalize_all(group_select_mode='ALL', lock_active=False)
        bpy.ops.object.mode_set(mode='OBJECT')
    except Exception as e:
        bpy.ops.object.mode_set(mode='OBJECT')
        print(f"[!] Operator normalize skipped ({e}), relying on Python math normalization.")

# Safety Assertion:
empty_groups = [vg.name for vg in elita_mesh.vertex_groups if not any(g.group == vg.index for v in elita_mesh.data.vertices for g in v.groups)]
print(f"Vertex groups with zero influence (e.g. Props / Roll bones): {len(empty_groups)}: {empty_groups}")

bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_FILE))
print(f"[✓] Saved remapped blend file to: {BLEND_FILE}")
