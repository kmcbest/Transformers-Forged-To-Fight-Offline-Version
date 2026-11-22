import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

mb_path = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\AssetBundles\blastoff_mesh.assetbundle")
donor_path = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatronus_gs_kabam_odr\megatronus_gs_kabam.assetbundle")

env_mb = UnityPy.load(str(mb_path))
env_donor = UnityPy.load(str(donor_path))

mb_meshes = {o.read_typetree()["m_Name"]: o.read_typetree() for o in env_mb.objects if o.type.name == "Mesh"}
donor_meshes = {o.read_typetree()["m_Name"]: o.read_typetree() for o in env_donor.objects if o.type.name == "Mesh"}

print("=== Comparing Robot Meshes ===")
r_mb = mb_meshes["cha_blastoff_gs_00"]
r_donor = donor_meshes["cha_megatronus_gs_kabam_00"]
print(f"BlastOff BindPose len: {len(r_mb.get('m_BindPose', []))}")
print(f"Donor BindPose len: {len(r_donor.get('m_BindPose', []))}")
print(f"Donor BoneNameHashes len: {len(r_donor.get('m_BoneNameHashes', []))}")

print("\n=== Comparing Vehicle Meshes ===")
v_mb = mb_meshes["cha_blastoff_gs_01"]
v_donor = donor_meshes["cha_megatronus_gs_kabam_01"]
print(f"BlastOff Veh BindPose len: {len(v_mb.get('m_BindPose', []))}")
print(f"Donor Veh BindPose len: {len(v_donor.get('m_BindPose', []))}")
print(f"Donor Veh BoneNameHashes len: {len(v_donor.get('m_BoneNameHashes', []))}")
