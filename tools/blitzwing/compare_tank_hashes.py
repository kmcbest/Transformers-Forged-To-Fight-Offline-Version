import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

mesh_bundle = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\AssetBundles\blitzwing_mesh.assetbundle"
env1 = UnityPy.load(mesh_bundle)
donor_bundle = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_gs_leader2015_odr\megatron_gs_leader2015.assetbundle"
env2 = UnityPy.load(donor_bundle)

m1 = [o for o in env1.objects if getattr(o.read(), 'm_Name', '') == 'cha_blitzwing_gs_01_tank'][0]
m2 = [o for o in env2.objects if o.path_id == 8396146535644667895][0]

tt1 = m1.read_typetree()
tt2 = m2.read_typetree()

print("BW Tank Hashes:", tt1.get("m_BoneNameHashes"))
print("Donor Tank Hashes:", tt2.get("m_BoneNameHashes"))
print("Hashes equal?", tt1.get("m_BoneNameHashes") == tt2.get("m_BoneNameHashes"))
