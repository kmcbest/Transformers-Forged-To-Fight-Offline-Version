import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

ROOT = Path(r"E:\Agent\TFTF-blender")
meg_donor = ROOT / "extracted_apk" / "assets" / "assetpack" / "megatron_gs_leader2015_odr" / "megatron_gs_leader2015.assetbundle"

env = UnityPy.load(str(meg_donor))
for o in env.objects:
    if o.type.name == "MonoBehaviour":
        try:
            d = o.read_typetree()
            print(f"MonoBehaviour PID={o.path_id}, name={d.get('m_Name')}, keys={list(d.keys())[:10]}")
        except Exception as e:
            print(f"MonoBehaviour PID={o.path_id} (could not read typetree: {e})")
