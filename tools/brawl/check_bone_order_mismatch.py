import sys
from pathlib import Path
import UnityPy

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

mesh_bundle = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\AssetBundles\brawl_mesh.assetbundle")
donor_bundle = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_cin_rotf_odr\megatron_cin_rotf.assetbundle")

env_m = UnityPy.load(str(mesh_bundle))
env_d = UnityPy.load(str(donor_bundle))

sf_m = list(env_m.files.values())[0] if not hasattr(list(env_m.files.values())[0], 'files') else list(list(env_m.files.values())[0].files.values())[0]
sf_d = list(env_d.files.values())[0] if not hasattr(list(env_d.files.values())[0], 'files') else list(list(env_d.files.values())[0].files.values())[0]

mesh_src = next(o for o in sf_m.objects.values() if o.type.name == "Mesh" and o.read_typetree().get("m_Name") == "cha_brawl_gs_00").read_typetree()
mesh_dst = sf_d.objects[8927022796776742380].read_typetree()

print("Src (Unity FBX) BoneHashes:", mesh_src.get("m_BoneNameHashes"))
print("Dst (Megatron Donor) BoneHashes:", mesh_dst.get("m_BoneNameHashes"))

print("\nAre BoneHashes identical?:", mesh_src.get("m_BoneNameHashes") == mesh_dst.get("m_BoneNameHashes"))
