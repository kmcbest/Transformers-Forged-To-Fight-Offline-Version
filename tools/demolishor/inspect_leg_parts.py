# -*- coding: utf-8 -*-
import bpy

bpy.ops.wm.open_mainfile(filepath="tools/demolishor/demolishor_phase1.blend")
mesh = bpy.data.objects.get("RB_DemolishorWeaponArm_SKEL.mo.dmx") or bpy.data.objects.get("cha_demolishor_gs_01")

leg_vgs = [vg for vg in mesh.vertex_groups if any(k in vg.name for k in ["Leg", "Thigh", "Knee", "Toe", "Ankle", "Foot"])]
print("Leg vertex groups:")
for vg in leg_vgs:
    pts = [v.co for v in mesh.data.vertices if any(g.group == vg.index and g.weight > 0.3 for g in v.groups)]
    if pts:
        cx = sum(p.x for p in pts) / len(pts)
        cz = sum(p.z for p in pts) / len(pts)
        print(f"  {vg.name:20s}: count={len(pts):4d}, Center=(X={cx:6.2f}, Z={cz:6.2f})")
