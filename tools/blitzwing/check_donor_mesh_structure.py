import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

donor_path = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_gs_leader2015_odr\megatron_gs_leader2015.assetbundle")
env = UnityPy.load(str(donor_path))
obj_map = {o.path_id: o for o in env.objects}

for pid, label in [(8396146535644667895, "Donor Tank"), (-6391917038499381755, "Donor Cannon")]:
    tt = obj_map[pid].read_typetree()
    print(f"\n{label} ({pid}):")
    print("  m_Name:", tt["m_Name"])
    print("  m_SubMeshes:", len(tt["m_SubMeshes"]))
    print("  m_BoneNameHashes:", tt["m_BoneNameHashes"])
    print("  m_BindPose count:", len(tt["m_BindPose"]))
    print("  Channels:")
    for ch in tt["m_VertexData"]["m_Channels"]:
        print("    ", ch)
