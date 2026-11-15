import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

ROOT = Path(r"E:\Agent\TFTF-blender")
bundle_path = ROOT / "extracted_apk" / "assets" / "assetpack" / "megatron_gs_leader2015_odr" / "megatron_gs_leader2015.assetbundle"
env = UnityPy.load(str(bundle_path))

for obj in env.objects:
    if obj.type.name == "GameObject":
        tt = obj.read_typetree()
        name = tt.get("m_Name", "")
        # print components
        comps = [c["component"]["m_PathID"] for c in tt.get("m_Component", [])]
        if any(k in name.lower() for k in ("trans", "prop", "model", "tank", "wpn", "cannon")):
            print(f"GameObject PID {obj.path_id}: Name '{name}' | Comps: {len(comps)}")
