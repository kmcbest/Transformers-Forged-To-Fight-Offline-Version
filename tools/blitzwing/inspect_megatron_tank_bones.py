import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

donor_path = Path("E:/Agent/TFTF/assets_ios/megatron_gs_leader2015_odr/megatron_gs_leader2015.assetbundle")
env = UnityPy.load(str(donor_path))
obj_map = {o.path_id: o for o in env.objects}

smr = obj_map[2138194849323017337].read_typetree()
print("Showcase Megatron Tank SMR bones:")
for idx, b in enumerate(smr["m_Bones"]):
    pid = b["m_PathID"]
    tr = obj_map[pid].read_typetree()
    go = obj_map[tr["m_GameObject"]["m_PathID"]].read_typetree()
    is_root = (pid == smr["m_RootBone"]["m_PathID"])
    print(f"  [{idx:2d}] PID {pid}: '{go['m_Name']}' {'(ROOT)' if is_root else ''} pos={tr['m_LocalPosition']} rot={tr['m_LocalRotation']}")
