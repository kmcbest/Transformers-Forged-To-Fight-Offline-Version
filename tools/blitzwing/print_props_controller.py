import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import json
import UnityPy

ROOT = Path(r"E:\Agent\TFTF-blender")
meg_donor = ROOT / "extracted_apk" / "assets" / "assetpack" / "megatron_gs_leader2015_odr" / "megatron_gs_leader2015.assetbundle"

env = UnityPy.load(str(meg_donor))
for o in env.objects:
    if o.path_id in (-8490429130128858862, -6224204825453341495):
        d = o.read_typetree()
        print(f"=== PID {o.path_id} ===")
        print(json.dumps(d, indent=2))
