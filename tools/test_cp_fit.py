import bpy
from pathlib import Path

bpy.ops.wm.read_factory_settings(use_empty=True)
fbx_path = Path("3rd-party-models/transformers-fall-of-cybertron-demolishor/source/transformers fall of cybertron Demolishor.fbx").resolve()
bpy.ops.import_scene.fbx(filepath=str(fbx_path))

rb = bpy.data.objects.get("RB_DemolishorWeaponArm_SKEL.mo.dmx")
cp = bpy.data.objects.get("CP_DemolishorArm_SKEL.mo.dmx")

print("Original RB vertices:", len(rb.data.vertices))
print("Original CP vertices:", len(cp.data.vertices))

# Check relative transforms in original FBX:
print("RB matrix_world:\n", rb.matrix_world)
print("CP matrix_world:\n", cp.matrix_world)

# Check CP AABB relative to RB Right Arm:
r_fa_vg = [vg.index for vg in rb.vertex_groups if "R_Arm03" in vg.name or "R_Elbow" in vg.name]
r_fa_pts = [v.co for v in rb.data.vertices if any(g.group in r_fa_vg for g in v.groups)]
cp_pts = [v.co for v in cp.data.vertices]

print(f"RB Right Forearm span: X=[{min(p.x for p in r_fa_pts):.2f}, {max(p.x for p in r_fa_pts):.2f}] Y=[{min(p.y for p in r_fa_pts):.2f}, {max(p.y for p in r_fa_pts):.2f}] Z=[{min(p.z for p in r_fa_pts):.2f}, {max(p.z for p in r_fa_pts):.2f}]")
print(f"CP Forearm Armor span: X=[{min(p.x for p in cp_pts):.2f}, {max(p.x for p in cp_pts):.2f}] Y=[{min(p.y for p in cp_pts):.2f}, {max(p.y for p in cp_pts):.2f}] Z=[{min(p.z for p in cp_pts):.2f}, {max(p.z for p in cp_pts):.2f}]")
