import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
BRAWL_BUNDLE = ROOT / "assets_redeco" / "brawl_gs.assetbundle"

env = UnityPy.load(str(BRAWL_BUNDLE))
sf = list(env.assets)[0]

for smr_pid in (-1713043385139994820, 6657504797783083318):
    smr_tt = sf.objects[smr_pid].read_typetree()
    mesh_pid = smr_tt["m_Mesh"]["m_PathID"]
    mesh_tt = sf.objects[mesh_pid].read_typetree()
    print(f"\nRobot SMR PID={smr_pid}:")
    print(f"  m_Bones length: {len(smr_tt['m_Bones'])}")
    print(f"  Mesh '{mesh_tt['m_Name']}' m_BindPose length: {len(mesh_tt['m_BindPose'])}")
    print(f"  Mesh m_BoneNameHashes length: {len(mesh_tt['m_BoneNameHashes'])}")
    
    # Check if any bone in m_Bones is null or dangling
    for idx, b in enumerate(smr_tt["m_Bones"]):
        b_pid = b["m_PathID"]
        if b_pid not in sf.objects:
            print(f"  ERROR: Bone[{idx}] PID={b_pid} NOT FOUND in objects!")
        else:
            b_obj = sf.objects[b_pid]
            if b_obj.type.name != "Transform":
                print(f"  ERROR: Bone[{idx}] PID={b_pid} is type {b_obj.type.name}, not Transform!")
    
    # Check RootBone
    rb_pid = smr_tt["m_RootBone"]["m_PathID"]
    if rb_pid not in sf.objects:
        print(f"  ERROR: RootBone PID={rb_pid} NOT FOUND in objects!")
    else:
        print(f"  RootBone PID={rb_pid} is valid Transform.")
