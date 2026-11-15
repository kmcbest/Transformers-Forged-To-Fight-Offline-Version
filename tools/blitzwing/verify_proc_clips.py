import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

proc_path = Path("e:/Agent/TFTF-blender/assets_netflix/character_anim_procedural.assetbundle")
if not proc_path.exists():
    proc_path = Path("E:/Agent/TFTF/extracted_apk/assets/assetpack/characters_procedural_odr/character_anim_procedural.assetbundle")

env = UnityPy.load(str(proc_path))
pids = {o.path_id: o for o in env.objects}

test_pids = [
    2235498278053343569, 8156662034948264509, -8977399132283187477, 6003597289559234958,
    7862591952412139551, -3119635653397265966, 7218399588967537672, -4633680087473212482, -2236987077198429143
]
for pid in test_pids:
    if pid in pids:
        print(f"Found {pid}: '{pids[pid].read_typetree().get('m_Name')}'")
    else:
        print(f"MISSING {pid} in procedural!")
