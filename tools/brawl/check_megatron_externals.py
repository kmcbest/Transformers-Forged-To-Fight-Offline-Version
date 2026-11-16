import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

DONOR_BUNDLE = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_cin_rotf_odr\megatron_cin_rotf.assetbundle")
env = UnityPy.load(str(DONOR_BUNDLE))
sf = list(env.assets)[0]

print(f"Donor bundle has {len(sf.externals)} externals:")
for idx, ext in enumerate(sf.externals, 1):
    print(f"  [{idx}] {ext.path}")

BRAWL_BUNDLE = Path(r"E:\Agent\TFTF-blender\assets_redeco\brawl_gs.assetbundle")
env_b = UnityPy.load(str(BRAWL_BUNDLE))
sf_b = list(env_b.assets)[0]
print(f"\nBrawl bundle has {len(sf_b.externals)} externals:")
for idx, ext in enumerate(sf_b.externals, 1):
    print(f"  [{idx}] {ext.path}")
