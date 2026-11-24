import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy
import numpy as np

DONOR = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_gs_leader2015_odr\megatron_gs_leader2015.assetbundle")
BW_MESH = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\AssetBundles\blitzwing_mesh.assetbundle")

env_d = UnityPy.load(str(DONOR))
env_b = UnityPy.load(str(BW_MESH))

meg_m = next(o for o in env_d.objects if o.path_id == 3463271531423751283).read_typetree()
bw_m = next(o for o in env_b.objects if o.type.name == "Mesh" and "00" in o.read_typetree().get("m_Name", "")).read_typetree()

sys.path.insert(0, r"E:\Agent\TFTF-blender\tools")
from validate_port_gates import parse_unity_mesh_streams

m_pts, m_uvs, m_ws, m_bi = parse_unity_mesh_streams(meg_m)
b_pts, b_uvs, b_ws, b_bi = parse_unity_mesh_streams(bw_m)

avatar = next(o for o in env_d.objects if o.type.name == "Avatar" and "00" in o.read_typetree().get("m_Name", "")).read_typetree()
tos_map = {k: v for k, v in avatar.get("m_TOS", [])}
hashes = meg_m["m_BoneNameHashes"]
bone_names = [tos_map.get(h, str(h)).split("/")[-1] for h in hashes]

print("=== Bone Weights Comparison on Fingers ===")
for bname in ["LeftHandIndex1", "LeftHandIndex2", "LeftHandIndex3", "LeftHandMiddle1", "LeftHandMiddle2", "LeftHandMiddle3"]:
    if bname in bone_names:
        bidx = bone_names.index(bname)
        m_mask = (m_bi[:, 0] == bidx) | (m_bi[:, 1] == bidx) | (m_bi[:, 2] == bidx) | (m_bi[:, 3] == bidx)
        b_mask = (b_bi[:, 0] == bidx) | (b_bi[:, 1] == bidx) | (b_bi[:, 2] == bidx) | (b_bi[:, 3] == bidx)
        print(f"\nBone [{bidx}] {bname}:")
        print(f"  Megatron verts with weight: {m_mask.sum()}")
        if m_mask.sum() > 0:
            m_pos = m_pts[m_mask]
            print(f"    Megatron bounds X: [{m_pos[:,0].min():.2f}, {m_pos[:,0].max():.2f}], Y: [{m_pos[:,1].min():.2f}, {m_pos[:,1].max():.2f}], Z: [{m_pos[:,2].min():.2f}, {m_pos[:,2].max():.2f}]")
        print(f"  Blitzwing verts with weight: {b_mask.sum()}")
        if b_mask.sum() > 0:
            b_pos = b_pts[b_mask]
            print(f"    Blitzwing bounds X: [{b_pos[:,0].min():.2f}, {b_pos[:,0].max():.2f}], Y: [{b_pos[:,1].min():.2f}, {b_pos[:,1].max():.2f}], Z: [{b_pos[:,2].min():.2f}, {b_pos[:,2].max():.2f}]")
