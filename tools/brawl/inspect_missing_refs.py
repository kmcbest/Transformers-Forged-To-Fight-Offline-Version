import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
MEG_BUNDLE = ROOT / "extracted_apk" / "assets" / "assetpack" / "megatron_cin_rotf_odr" / "megatron_cin_rotf.assetbundle"
BRAWL_BUNDLE = ROOT / "assets_redeco" / "brawl_gs.assetbundle"

missing_pids = {-7854615674899395621, -7777457830161264517, -62711741483785396, 2367818045411061912}

def find_referrers(bundle_path, label):
    print(f"\nSearching referrers in {label}...")
    env = UnityPy.load(str(bundle_path))
    sf = list(env.assets)[0]
    for pid, obj in sf.objects.items():
        try:
            tt = obj.read_typetree()
        except:
            continue
        text = str(tt)
        for m in missing_pids:
            if str(m) in text:
                print(f"  In {label}: Object PID={pid} ({obj.type.name}) references missing PID={m}")
                if obj.type.name == "SkinnedMeshRenderer":
                    print(f"    SMR Materials: {tt.get('m_Materials')}")
                    print(f"    SMR Mesh: {tt.get('m_Mesh')}")
                elif obj.type.name == "Material":
                    print(f"    Mat Name: {tt.get('m_Name')}")

find_referrers(MEG_BUNDLE, "MEGATRON")
find_referrers(BRAWL_BUNDLE, "BRAWL")
