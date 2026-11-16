import sys
from pathlib import Path
import UnityPy

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

donor_path = Path("extracted_apk/assets/assetpack/megatron_cin_rotf_odr/megatron_cin_rotf.assetbundle")
env_d = UnityPy.load(str(donor_path))
sf = list(env_d.files.values())[0] if not hasattr(list(env_d.files.values())[0], 'files') else list(list(env_d.files.values())[0].files.values())[0]

tank_mesh = sf.objects[-9025351850097636016].read_typetree()
print("Megatron Donor Tank Mesh:")
print("  Name:", tank_mesh.get("m_Name"))
print("  BoneNameHashes:", tank_mesh.get("m_BoneNameHashes"))
print("  RootBoneNameHash:", tank_mesh.get("m_RootBoneNameHash"))
print("  BindPoses count:", len(tank_mesh.get("m_BindPose", [])))
print("  BindPose 0:", tank_mesh.get("m_BindPose", [])[0])
if len(tank_mesh.get("m_BindPose", [])) > 1:
    print("  BindPose 1:", tank_mesh.get("m_BindPose", [])[1])

# Also check SMR for tank in donor
for pid in [-4076617426109914192, -2983655943056242676]:
    smr = sf.objects[pid].read_typetree()
    print(f"\nDonor Tank SMR {pid}:")
    print("  Bones count:", len(smr.get("m_Bones", [])))
    print("  Bones:", smr.get("m_Bones", []))
    print("  RootBone:", smr.get("m_RootBone", {}))
