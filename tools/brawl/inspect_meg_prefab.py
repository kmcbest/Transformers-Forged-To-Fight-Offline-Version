import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_cin_rotf_odr\megatron_cin_rotf.assetbundle"
env = UnityPy.load(bundle_path)

for obj in env.objects:
    if obj.type.name == "GameObject" and "megatron_cin_rotf" in getattr(obj.read(), 'm_Name', ''):
        d = obj.read()
        print(f"GameObject: {d.m_Name}")
        # Look for SkinnedMeshRenderer
        for c in d.m_Components:
            c_obj = c.read()
            if c_obj.type.name == "SkinnedMeshRenderer":
                smr = c_obj.read()
                print(f"  SMR: {smr.m_GameObject.read().m_Name}")
                mesh = smr.m_Mesh.read()
                print(f"    Mesh: {mesh.m_Name}")
                bones = [b.read().m_Name for b in smr.m_Bones if b]
                print(f"    Bones ({len(bones)}): {bones[:10]}")
