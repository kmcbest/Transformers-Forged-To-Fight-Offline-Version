# -*- coding: utf-8 -*-
import sys
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

env_d = UnityPy.load('d:/Agent/tftf/toolchain/unity_build_project/AssetBundles/demolishor_mesh.assetbundle')
hashes_d = []
for obj in env_d.objects:
    if obj.type.name == 'Mesh':
        tree = obj.read_typetree()
        if 'demolishor' in tree.get('m_Name', '').lower():
            hashes_d = tree.get('m_BoneNameHashes', [])
            break

env_i = UnityPy.load('extracted_apk/assets/assetpack/ironhide_cin_rotf_odr/ironhide_cin_rotf.assetbundle')
hashes_i = []
for obj in env_i.objects:
    if obj.type.name == 'Mesh':
        tree = obj.read_typetree()
        if tree.get('m_Name') == 'cha_ironhide_cin_rotf_00':
            hashes_i = tree.get('m_BoneNameHashes', [])
            break

print("Demolishor hashes:", len(hashes_d))
print("Ironhide hashes:  ", len(hashes_i))
matches = [h1 == h2 for h1, h2 in zip(hashes_d, hashes_i)]
print(f"Matching hashes count: {sum(matches)} / {len(hashes_i)}")
if sum(matches) != len(hashes_i):
    for idx, (h1, h2) in enumerate(zip(hashes_d, hashes_i)):
        if h1 != h2:
            print(f"  Mismatch at {idx}: Demo={h1} vs Iron={h2}")
