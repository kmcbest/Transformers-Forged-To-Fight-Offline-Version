import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
BLITZ_BUNDLE = ROOT / "assets_redeco" / "blitzwing_gs.assetbundle"

if BLITZ_BUNDLE.exists():
    env = UnityPy.load(str(BLITZ_BUNDLE))
    sf = list(env.assets)[0]
    for pid, obj in sf.objects.items():
        if obj.type.name == "SkinnedMeshRenderer":
            tt = obj.read_typetree()
            go_pid = tt.get("m_GameObject", {}).get("m_PathID")
            go_name = sf.objects[go_pid].read_typetree()["m_Name"] if go_pid in sf.objects else ""
            mesh_pid = tt["m_Mesh"]["m_PathID"]
            mtt = sf.objects[mesh_pid].read_typetree() if mesh_pid in sf.objects else {}
            print(f"Blitzwing SMR on '{go_name}':")
            print(f"  SMR m_Bones count: {len(tt['m_Bones'])}")
            print(f"  Mesh '{mtt.get('m_Name')}' m_BindPose count: {len(mtt.get('m_BindPose', []))}")
            print(f"  Mesh m_BoneNameHashes count: {len(mtt.get('m_BoneNameHashes', []))}")
else:
    print("Blitzwing bundle not found")
