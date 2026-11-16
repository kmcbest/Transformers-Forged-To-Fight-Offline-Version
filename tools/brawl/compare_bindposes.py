import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

ROOT = Path(r"E:\Agent\TFTF-blender")
MESH_BUNDLE = ROOT / "toolchain" / "unity_build_project" / "AssetBundles" / "brawl_mesh.assetbundle"
DONOR_BUNDLE = ROOT / "extracted_apk" / "assets" / "assetpack" / "megatron_cin_rotf_odr" / "megatron_cin_rotf.assetbundle"

env_m = UnityPy.load(str(MESH_BUNDLE))
src_r = next(o.read_typetree() for o in env_m.objects if o.type.name == "Mesh" and o.read_typetree()["m_Name"] == "cha_brawl_gs_00")

env_d = UnityPy.load(str(DONOR_BUNDLE))
obj_map = {o.path_id: o for o in env_d.objects}
dst_r = obj_map[8927022796776742380].read_typetree()

print("src_r bindpose count:", len(src_r["m_BindPose"]))
print("dst_r bindpose count:", len(dst_r["m_BindPose"]))

print("\nFirst bindpose matrix:")
print("src:", src_r["m_BindPose"][0])
print("dst:", dst_r["m_BindPose"][0])
