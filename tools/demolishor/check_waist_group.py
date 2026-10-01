# -*- coding: utf-8 -*-
import bpy

bpy.ops.wm.open_mainfile(filepath="tools/demolishor/demolishor_phase1.blend")
mesh = bpy.data.objects.get("RB_DemolishorWeaponArm_SKEL.mo.dmx")
vg_names = {vg.index: vg.name for vg in mesh.vertex_groups}

# Find vertices around X=0.97, Y=-0.16, Z=6.27 in phase1
pts = [v for v in mesh.data.vertices if 0.6 < v.co.x < 1.4 and 5.5 < v.co.z < 7.0]
print(f"Found {len(pts)} vertices in waist area:")
v_groups = {}
for v in pts:
    for g in v.groups:
        name = vg_names.get(g.group)
        if name and g.weight > 0.1:
            v_groups[name] = v_groups.get(name, 0) + 1

for name, count in sorted(v_groups.items(), key=lambda kv: -kv[1]):
    print(f"  {name:25s}: {count} vertices")
