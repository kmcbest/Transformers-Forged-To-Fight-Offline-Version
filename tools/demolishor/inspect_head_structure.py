# -*- coding: utf-8 -*-
import bpy

bpy.ops.wm.open_mainfile(filepath="tools/demolishor/demolishor_phase1.blend")
mesh = bpy.data.objects.get("RB_DemolishorWeaponArm_SKEL.mo.dmx")
vg_names = {vg.index: vg.name for vg in mesh.vertex_groups}

head_vgs = [vg for vg in mesh.vertex_groups if any(k in vg.name.lower() for k in ["head", "neck", "jaw", "face", "eye"])]
print("Head-related vertex groups in Demolishor:")
for vg in head_vgs:
    pts = [v.co for v in mesh.data.vertices if any(g.group == vg.index and g.weight > 0.2 for g in v.groups)]
    if pts:
        cx = sum(p.x for p in pts) / len(pts)
        cy = sum(p.y for p in pts) / len(pts)
        cz = sum(p.z for p in pts) / len(pts)
        print(f"  {vg.name:25s}: count={len(pts):4d}, Center=(X={cx:6.2f}, Y={cy:6.2f}, Z={cz:6.2f})")
