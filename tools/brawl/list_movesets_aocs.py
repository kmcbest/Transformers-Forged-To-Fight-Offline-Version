import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

BASE_DIR = Path(r"E:\Agent\TFTF-blender")
DONOR = BASE_DIR / r"extracted_apk\assets\assetpack\megatron_cin_rotf_odr\megatron_cin_rotf.assetbundle"
env = UnityPy.load(str(DONOR))

for o in env.objects:
    if o.type.name == "MonoBehaviour":
        tt = o.read_typetree()
        if "_moves" in tt:
            go_pid = tt.get("m_GameObject", {}).get("m_PathID")
            moves = [m.get("_name") for m in tt.get("_moves", [])]
            print(f"MoveSet PID={o.path_id} on GO={go_pid}: {len(moves)} moves, e.g. {moves[:3]}")
    elif o.type.name == "AnimatorOverrideController":
        tt = o.read_typetree()
        name = tt.get("m_Name")
        ctrl = tt.get("m_Controller")
        print(f"AOC PID={o.path_id} Name='{name}', Controller={ctrl}")
