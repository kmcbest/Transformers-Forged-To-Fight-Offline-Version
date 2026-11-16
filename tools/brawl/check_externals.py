import sys
from pathlib import Path
import UnityPy

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

donor_path = Path("extracted_apk/assets/assetpack/megatron_cin_rotf_odr/megatron_cin_rotf.assetbundle")
brawl_path = Path("assets_redeco/brawl_gs.assetbundle")

env_d = UnityPy.load(str(donor_path))
env_b = UnityPy.load(str(brawl_path))

sf_d = list(env_d.files.values())[0] if not hasattr(list(env_d.files.values())[0], 'files') else list(list(env_d.files.values())[0].files.values())[0]
sf_b = list(env_b.files.values())[0] if not hasattr(list(env_b.files.values())[0], 'files') else list(list(env_b.files.values())[0].files.values())[0]

print("Donor externals:")
for idx, ext in enumerate(sf_d.externals):
    print(f"  [{idx+1}] guid={ext.guid}, type={ext.type}, path='{ext.path}'")

print("Brawl externals:")
for idx, ext in enumerate(sf_b.externals):
    print(f"  [{idx+1}] guid={ext.guid}, type={ext.type}, path='{ext.path}'")
