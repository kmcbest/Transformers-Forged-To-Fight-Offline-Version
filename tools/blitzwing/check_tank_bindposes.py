import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
from pathlib import Path
import UnityPy

p_donor = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_gs_leader2015_odr\megatron_gs_leader2015.assetbundle")
env_d = UnityPy.load(str(p_donor))

for o in env_d.objects:
    if o.type.name == "Mesh":
        tt = o.read_typetree()
        if tt["m_Name"] == "cha_megatron_gs_leader2015_01":
            print("Donor Tank Mesh:")
            print("  BoneNameHashes:", tt["m_BoneNameHashes"])
            print("  RootBoneNameHash:", tt["m_RootBoneNameHash"])
            print("  BindPose count:", len(tt["m_BindPose"]))
            print("  BindPose[0]:", tt["m_BindPose"][0])

p_bw = Path(r"E:\Agent\TFTF-blender\assets_redeco\blitzwing_gs.assetbundle")
env_b = UnityPy.load(str(p_bw))

for o in env_b.objects:
    if o.type.name == "Mesh":
        tt = o.read_typetree()
        if tt["m_Name"] == "cha_blitzwing_gs_01":
            print("\nBlitzwing Tank Mesh in assets_redeco:")
            print("  BoneNameHashes:", tt["m_BoneNameHashes"])
            print("  RootBoneNameHash:", tt["m_RootBoneNameHash"])
            print("  BindPose count:", len(tt["m_BindPose"]))
            print("  BindPose[0]:", tt["m_BindPose"][0])
