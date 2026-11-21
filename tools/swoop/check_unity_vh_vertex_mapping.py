import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from tools.validate_port_gates import parse_unity_mesh_streams

env = UnityPy.load(r"e:\Agent\TFTF-blender\toolchain\unity_build_project\AssetBundles\swoop_mesh.assetbundle")
for o in env.objects:
    if o.type.name == "Mesh":
        tt = o.read_typetree()
        if tt["m_Name"] == "cha_swoop_gs_01":
            pts, uvs, ws, bi = parse_unity_mesh_streams(tt)
            print(f"cha_swoop_gs_01 Unity pts shape: {pts.shape}")
            print(f"  Unity X range: [{pts[:,0].min():+.4f}, {pts[:,0].max():+.4f}]")
            print(f"  Unity Y range: [{pts[:,1].min():+.4f}, {pts[:,1].max():+.4f}]")
            print(f"  Unity Z range: [{pts[:,2].min():+.4f}, {pts[:,2].max():+.4f}]")
            bnames = [
                "chop1_gun_FX", "chop1_cone_center", "chop1_gun_center", "chop1_head_center",
                "chop1_chest_center", "chop1_chest_hidden_center", "chop1_chest_turbine_right",
                "chop2_torso_hip_center", "chop1_back_center", "chop2_arm_bicep_right", "COG",
                "chop2_leg_upper_right", "chop1_forearm_right", "chop2_hand_right", "chop1_calf_right",
                "chop2_leg_lower_right", "chop1_calf_wing_right", "chop1_cannon_right", "chop1_foot_right",
                "chop1_chest_turbine_left", "chop2_arm_bicep_left", "chop2_leg_upper_left",
                "chop1_forearm_left", "chop2_hand_left", "chop1_calf_left", "chop2_leg_lower_left",
                "chop1_calf_wing_left", "chop1_cannon_left", "chop1_foot_left"
            ]
            for bidx, bn in enumerate(bnames):
                mask = (bi[:, 0] == bidx) & (ws[:, 0] > 0.5)
                if mask.sum() > 0:
                    m = pts[mask].mean(axis=0)
                    print(f"  Bone {bn:<26} ({mask.sum():4d}v): mean Unity=({m[0]:+.4f}, {m[1]:+.4f}, {m[2]:+.4f})")
