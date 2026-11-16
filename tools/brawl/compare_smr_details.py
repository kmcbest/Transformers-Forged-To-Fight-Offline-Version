import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

BASE_DIR = Path(r"E:\Agent\TFTF-blender")
DONOR_BUNDLE = BASE_DIR / r"extracted_apk\assets\assetpack\megatron_cin_rotf_odr\megatron_cin_rotf.assetbundle"
BRAWL_BUNDLE = BASE_DIR / r"assets_redeco\brawl_gs.assetbundle"

env_d = UnityPy.load(str(DONOR_BUNDLE))
env_b = UnityPy.load(str(BRAWL_BUNDLE))

# 1. Compare meshes
print("=== Compare Meshes ===")
for env, label in [(env_d, "Donor"), (env_b, "Brawl")]:
    for o in env.objects:
        if o.type.name == "Mesh":
            tt = o.read_typetree()
            print(f"[{label}] Mesh PID={o.path_id} Name='{tt.get('m_Name')}'")
            print(f"  BindPoses={len(tt.get('m_BindPose', []))} BoneHashes={len(tt.get('m_BoneNameHashes', []))} RootHash={tt.get('m_RootBoneNameHash')}")
            print(f"  Hashes: {tt.get('m_BoneNameHashes', [])[:5]}...")

# 2. Compare Robot SMRs
print("\n=== Compare SMRs ===")
for env, label in [(env_d, "Donor"), (env_b, "Brawl")]:
    for o in env.objects:
        if o.type.name == "SkinnedMeshRenderer":
            tt = o.read_typetree()
            print(f"[{label}] SMR PID={o.path_id} Enabled={tt.get('m_Enabled')} MeshPID={tt.get('m_Mesh', {}).get('m_PathID')}")
            print(f"  RootBone={tt.get('m_RootBone', {}).get('m_PathID')} BonesLen={len(tt.get('m_Bones', []))}")
            bones = [b['m_PathID'] for b in tt.get('m_Bones', [])]
            print(f"  Bones PIDs: {bones[:5]}...")
