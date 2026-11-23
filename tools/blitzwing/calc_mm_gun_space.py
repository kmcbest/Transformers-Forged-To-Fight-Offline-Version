import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import UnityPy
from pathlib import Path
from inspect_sword_space_and_fx import tr_to_m4, bp_to_m4, m4_mul, m4_pt

ROOT_GM = Path(r"E:\Agent\TFTF")
mm_env = UnityPy.load(str(ROOT_GM / "extracted_apk/assets/assetpack/motormaster_gs_voyager2015_odr/motormaster_gs_voyager2015.assetbundle"))
mm_map = {o.path_id: o for o in mm_env.objects}

# MM gun TR=4791454051944404170 -> Reference TR=-7004962172419422833 -> COG TR=-1325075375823704567
mm_gun = tr_to_m4(mm_map[4791454051944404170].read_typetree())
mm_ref = tr_to_m4(mm_map[-7004962172419422833].read_typetree())
mm_cog = tr_to_m4(mm_map[-1325075375823704567].read_typetree())
mm_mesh = mm_map[2697988736999805448].read_typetree()
mm_bp = bp_to_m4(mm_mesh["m_BindPose"][0])

M_mm = m4_mul(m4_mul(mm_gun, mm_ref), m4_mul(mm_cog, mm_bp))
print("=== Motormaster Gun Mesh -> LeftHand Matrix ===")
for row in M_mm:
    print(" ", [round(x, 4) for x in row])

# Print localAABB center & min/max mapped to LeftHand space!
c = mm_mesh["m_LocalAABB"]["m_Center"]
e = mm_mesh["m_LocalAABB"]["m_Extent"]
corners = [
    (c["x"] + sx*e["x"], c["y"] + sy*e["y"], c["z"] + sz*e["z"])
    for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)
]
mapped = [m4_pt(M_mm, p) for p in corners]
print("MM Gun bbox in LeftHand space:")
print(f"  X: [{min(p[0] for p in mapped):.3f}, {max(p[0] for p in mapped):.3f}]")
print(f"  Y: [{min(p[1] for p in mapped):.3f}, {max(p[1] for p in mapped):.3f}]")
print(f"  Z: [{min(p[2] for p in mapped):.3f}, {max(p[2] for p in mapped):.3f}]")
print("  Basis mapping:")
for ax, v in [("Mesh +X (width)", (1,0,0)), ("Mesh +Y (-barrel)", (0,1,0)), ("Mesh +Z (+top)", (0,0,1))]:
    p = m4_pt(M_mm, v)
    d = [round(p[i] - M_mm[i][3], 3) for i in range(3)]
    print(f"    {ax:<20} -> LeftHand {d}")
print("  Mesh grip center (0.0, 0.4582, -1.9340) -> LeftHand:", [round(x, 3) for x in m4_pt(M_mm, (0.0, 0.4582, -1.9340))])
