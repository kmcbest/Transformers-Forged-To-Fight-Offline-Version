import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
import UnityPy
from pathlib import Path

# Load Megatron donor summary
with open(r"E:\Agent\TFTF-blender\3rd-party-models\Brawl\00_donor_reference\donor_summary.json", "r", encoding="utf-8") as f:
    donor = json.load(f)

meg_hashes = donor["meshes"]["cha_megatron_cin_rotf_00"]["boneHashes"]
meg_tos = donor["avatars"]["cha_megatron_cin_rotf_00Avatar"]["tos"]

print(f"Megatron has {len(meg_hashes)} bone hashes:")
meg_hash_to_path = {h: meg_tos.get(str(h), "") for h in meg_hashes}
for h, p in meg_hash_to_path.items():
    print(f"  {h} -> {p}")

# Load Brawl mesh bundle
bundle_path = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\AssetBundles\brawl_mesh.assetbundle")
env = UnityPy.load(str(bundle_path))
for obj in env.objects:
    if obj.type.name == "Mesh":
        tt = obj.read_typetree()
        if tt.get("m_Name") == "cha_brawl_gs_00":
            b_hashes = tt.get("m_BoneNameHashes", [])
            print(f"\nBrawl Robot has {len(b_hashes)} bone hashes:")
            for bh in b_hashes:
                # Check if it matches any Megatron hash directly
                match = meg_hash_to_path.get(bh, "NO_DIRECT_MATCH")
                print(f"  {bh} -> {match}")
