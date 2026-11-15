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

mesh = obj_map[-6391917038499381755].read_typetree()
print("Cannon Mesh:")
print("  Name:", mesh["m_Name"])
print("  BoneNameHashes:", mesh["m_BoneNameHashes"])
print("  RootBoneNameHash:", mesh["m_RootBoneNameHash"])
print("  BindPose count:", len(mesh["m_BindPose"]))
for i, bp in enumerate(mesh["m_BindPose"]):
    print(f"  BindPose[{i}]:", bp)
