# -*- coding: utf-8 -*-
import json
import sys
import numpy as np
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

# 1. Load Ironhide's original bindposes
env_iron = UnityPy.load('extracted_apk/assets/assetpack/ironhide_cin_rotf_odr/ironhide_cin_rotf.assetbundle')
iron_bindposes = None
for obj in env_iron.objects:
    if obj.type.name == 'Mesh':
        tree = obj.read_typetree()
        if tree.get('m_Name') == 'cha_ironhide_cin_rotf_00':
            iron_bindposes = tree.get('m_BindPose', [])
            break

# 2. Load Demolishor's compiled bindposes from Unity
env_demo = UnityPy.load('d:/Agent/tftf/toolchain/unity_build_project/AssetBundles/demolishor_mesh.assetbundle')
demo_bindposes = None
for obj in env_demo.objects:
    if obj.type.name == 'Mesh':
        tree = obj.read_typetree()
        if 'demolishor' in tree.get('m_Name', '').lower():
            demo_bindposes = tree.get('m_BindPose', [])
            break

print(f"Ironhide bindposes count: {len(iron_bindposes)}")
print(f"Demolishor bindposes count: {len(demo_bindposes)}")

with open('tools/demolishor/ironhide_80_bones.json', 'r', encoding='utf-8') as f:
    bones_data = json.load(f)
bone_order = bones_data['bone_order']

def bp_to_mat(bp):
    return np.array([
        [bp['e00'], bp['e01'], bp['e02'], bp['e03']],
        [bp['e10'], bp['e11'], bp['e12'], bp['e13']],
        [bp['e20'], bp['e21'], bp['e22'], bp['e23']],
        [bp['e30'], bp['e31'], bp['e32'], bp['e33']]
    ])

print("\n--- Comparing BindPoses (Ironhide vs Demolishor) ---")
test_bones = ['Hips', 'Spine', 'LeftShoulder', 'LeftArm', 'LeftForeArm', 'RightArm', 'LeftUpLeg']

for b in test_bones:
    idx = bone_order.index(b)
    m_iron = bp_to_mat(iron_bindposes[idx])
    m_demo = bp_to_mat(demo_bindposes[idx])
    
    # Invert to get bone world transform in rest pose
    inv_iron = np.linalg.inv(m_iron)
    inv_demo = np.linalg.inv(m_demo)
    
    pos_iron = inv_iron[:3, 3]
    pos_demo = inv_demo[:3, 3]
    
    diff = np.abs(m_iron - m_demo).max()
    print(f"\nBone: {b} (Index {idx})")
    print(f"  Ironhide World Pos:   ({pos_iron[0]:7.2f}, {pos_iron[1]:7.2f}, {pos_iron[2]:7.2f})")
    print(f"  Demolishor World Pos: ({pos_demo[0]:7.2f}, {pos_demo[1]:7.2f}, {pos_demo[2]:7.2f})")
    print(f"  Max Diff in Matrix:   {diff:.4f}")
    print(f"  Ironhide Rot:\n{m_iron[:3, :3]}")
    print(f"  Demolishor Rot:\n{m_demo[:3, :3]}")
