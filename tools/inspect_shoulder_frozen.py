import bpy

bpy.ops.wm.open_mainfile(filepath="tools/demolishor/demolishor_phase2_inspect.blend")
mesh = bpy.data.objects.get("cha_demolishor_gs_01")
vg_names = {vg.index: vg.name for vg in mesh.vertex_groups}

# Find vertices high above the shoulder:
# In Image: Z > 8.5, Y around [-1.5, 0.5], X around [-3.5, 3.5]
target_verts = []
for v in mesh.data.vertices:
    if v.co.z >= 8.5:
        # Check if it's NOT the head (head is X in [-0.8, 0.8], Y in [-0.5, 0.8])
        if abs(v.co.x) > 0.8:
            target_verts.append(v)

print(f"Found {len(target_verts)} shoulder/back exhaust vertices above Z=8.5")

# Check which vertex groups they belong to:
vg_counts = {}
unweighted = 0
for v in target_verts:
    if not v.groups:
        unweighted += 1
        continue
    for g in v.groups:
        if g.weight > 0.1:
            name = vg_names.get(g.group, f"VG_{g.group}")
            vg_counts[name] = vg_counts.get(name, 0) + 1

print(f"Unweighted count: {unweighted}")
print("Vertex group distribution for these pieces:")
for name, cnt in sorted(vg_counts.items(), key=lambda x: x[1], reverse=True):
    print(f"  {name:25s}: {cnt} vertices")
