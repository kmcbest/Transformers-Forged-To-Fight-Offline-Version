import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

DONOR_BUNDLE = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_cin_rotf_odr\megatron_cin_rotf.assetbundle")
env = UnityPy.load(str(DONOR_BUNDLE))
sf = list(env.assets)[0]

m_r = sf.objects[8927022796776742380].read_typetree()
print("Donor Robot Mesh m_BoneNameHashes:", m_r.get("m_BoneNameHashes"))
print("Donor Robot Mesh m_RootBoneNameHash:", m_r.get("m_RootBoneNameHash"))

m_v = sf.objects[-9025351850097636016].read_typetree()
print("Donor Vehicle Mesh m_BoneNameHashes:", m_v.get("m_BoneNameHashes"))
print("Donor Vehicle Mesh m_RootBoneNameHash:", m_v.get("m_RootBoneNameHash"))
