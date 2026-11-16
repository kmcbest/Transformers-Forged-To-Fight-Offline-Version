import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path
import json

ROOT = Path(r"E:\Agent\TFTF-blender")
MEG_BUNDLE = ROOT / "extracted_apk" / "assets" / "assetpack" / "megatron_cin_rotf_odr" / "megatron_cin_rotf.assetbundle"
BRAWL_BUNDLE = ROOT / "assets_redeco" / "brawl_gs.assetbundle"

def inspect_mbs(bundle_path, root_name):
    env = UnityPy.load(str(bundle_path))
    sf = list(env.assets)[0]
    for pid, obj in sf.objects.items():
        if obj.type.name == "GameObject":
            tt = obj.read_typetree()
            if tt["m_Name"] == root_name:
                print(f"\n=== MonoBehaviours on {root_name} in {bundle_path.name} ===")
                for comp in tt.get("m_Component", []):
                    c_pid = comp["component"]["m_PathID"]
                    c_obj = sf.objects.get(c_pid)
                    if c_obj and c_obj.type.name == "MonoBehaviour":
                        mtt = c_obj.read_typetree()
                        print(f"\n--- MB PID={c_pid} ---")
                        print(json.dumps(mtt, indent=2, default=str))

inspect_mbs(MEG_BUNDLE, "Megatron_Cin_ROTF_lw")
inspect_mbs(BRAWL_BUNDLE, "brawl_gs_lw")
