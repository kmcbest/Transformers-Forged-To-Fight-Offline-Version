import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
TARN_BUNDLE = ROOT / "assets_redeco" / "tarn_gs.assetbundle"

env = UnityPy.load(str(TARN_BUNDLE))
sf = list(env.assets)[0]

for pid, obj in sf.objects.items():
    if obj.type.name == "SkinnedMeshRenderer":
        tt = obj.read_typetree()
        go_pid = tt.get("m_GameObject", {}).get("m_PathID")
        go_name = sf.objects[go_pid].read_typetree()["m_Name"] if go_pid in sf.objects else ""
        if "01" in go_name or "vehicle" in go_name.lower():
            mesh_pid = tt["m_Mesh"]["m_PathID"]
            mesh_obj = sf.objects[mesh_pid]
            mtt = mesh_obj.read_typetree()
            print(f"Tarn Vehicle SMR PID={pid} on GO '{go_name}':")
            print(f"  SMR m_Bones count: {len(tt['m_Bones'])}")
            print(f"  SMR m_RootBone: {tt['m_RootBone']}")
            print(f"  Mesh '{mtt['m_Name']}' m_BoneNameHashes count: {len(mtt['m_BoneNameHashes'])}")
            print(f"  Mesh m_BindPose count: {len(mtt['m_BindPose'])}")
            print(f"  Mesh m_RootBoneNameHash: {mtt['m_RootBoneNameHash']}")
            print(f"  Mesh m_BoneNameHashes: {mtt['m_BoneNameHashes']}")
