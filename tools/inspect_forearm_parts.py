import bpy
from pathlib import Path

bpy.ops.wm.read_factory_settings(use_empty=True)
fbx_path = Path("3rd-party-models/transformers-fall-of-cybertron-demolishor/source/transformers fall of cybertron Demolishor.fbx").resolve()
bpy.ops.import_scene.fbx(filepath=str(fbx_path))

rb = bpy.data.objects.get("RB_DemolishorWeaponArm_SKEL.mo.dmx")
# Look at the left arm gauntlet on RB mesh:
# Left arm gauntlet vertices:
l_forearm_vg = [vg.index for vg in rb.vertex_groups if "L_Arm03" in vg.name or "L_Elbow" in vg.name]
r_forearm_vg = [vg.index for vg in rb.vertex_groups if "R_Arm03" in vg.name or "R_Elbow" in vg.name]

l_fa_verts = [v for v in rb.data.vertices if any(g.group in l_forearm_vg and g.weight > 0.2 for g in v.groups)]
r_fa_verts = [v for v in rb.data.vertices if any(g.group in r_forearm_vg and g.weight > 0.2 for g in v.groups)]

print(f"Left ForeArm vertices count in RB mesh: {len(l_fa_verts)}")
print(f"Right ForeArm vertices count in RB mesh: {len(r_fa_verts)}")

# Also inspect CP mesh
cp = bpy.data.objects.get("CP_DemolishorArm_SKEL.mo.dmx")
print(f"CP mesh vertices count: {len(cp.data.vertices)}")
