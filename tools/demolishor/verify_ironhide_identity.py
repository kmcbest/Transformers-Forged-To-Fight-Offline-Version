# -*- coding: utf-8 -*-
import sys
import numpy as np
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

env = UnityPy.load('extracted_apk/assets/assetpack/ironhide_cin_rotf_odr/ironhide_cin_rotf.assetbundle')

# 1. Get Ironhide's 80 bindposes
iron_bindposes = None
for obj in env.objects:
    if obj.type.name == 'Mesh':
        tree = obj.read_typetree()
        if tree.get('m_Name') == 'cha_ironhide_cin_rotf_00':
            iron_bindposes = tree.get('m_BindPose', [])
            break

# 2. Get the 80 bones from Ironhide's SMR
target_smr = None
for obj in env.objects:
    if obj.type.name == 'SkinnedMeshRenderer':
        tree = obj.read_typetree()
        if len(tree.get('m_Bones', [])) == 80:
            target_smr = tree
            break

# 3. Build world matrices for all transforms in the prefab
tr_dict = {}
for obj in env.objects:
    if obj.type.name == 'Transform':
        tr_dict[obj.path_id] = obj.read_typetree()

def q_to_rot(q):
    x, y, z, w = q['x'], q['y'], q['z'], q['w']
    return np.array([
        [1 - 2*(y**2 + z**2), 2*(x*y - z*w), 2*(x*z + y*w), 0],
        [2*(x*y + z*w), 1 - 2*(x**2 + z**2), 2*(y*z - x*w), 0],
        [2*(x*z - y*w), 2*(y*z + x*w), 1 - 2*(x**2 + y**2), 0],
        [0, 0, 0, 1]
    ])

def tr_to_mat(tr):
    pos = tr.get('m_LocalPosition', {'x':0,'y':0,'z':0})
    rot = tr.get('m_LocalRotation', {'x':0,'y':0,'z':0,'w':1})
    scale = tr.get('m_LocalScale', {'x':1,'y':1,'z':1})
    
    t_mat = np.eye(4)
    t_mat[0, 3] = pos['x']
    t_mat[1, 3] = pos['y']
    t_mat[2, 3] = pos['z']
    
    r_mat = q_to_rot(rot)
    
    s_mat = np.diag([scale['x'], scale['y'], scale['z'], 1.0])
    return t_mat @ r_mat @ s_mat

# Compute world transform recursively
world_matrices = {}
def get_world(tr_id):
    if tr_id in world_matrices:
        return world_matrices[tr_id]
    tr = tr_dict[tr_id]
    local_m = tr_to_mat(tr)
    parent_id = tr.get('m_Father', {}).get('m_PathID', 0)
    if parent_id and parent_id in tr_dict:
        wm = get_world(parent_id) @ local_m
    else:
        wm = local_m
    world_matrices[tr_id] = wm
    return wm

def bp_to_mat(bp):
    return np.array([
        [bp['e00'], bp['e01'], bp['e02'], bp['e03']],
        [bp['e10'], bp['e11'], bp['e12'], bp['e13']],
        [bp['e20'], bp['e21'], bp['e22'], bp['e23']],
        [bp['e30'], bp['e31'], bp['e32'], bp['e33']]
    ])

print("--- Verifying M_bone * BindPose for Ironhide ---")
smr_bones = target_smr.get('m_Bones', [])
max_errors = []
for idx in range(min(10, len(smr_bones))):
    tr_id = smr_bones[idx].get('m_PathID')
    wm = get_world(tr_id)
    bp = bp_to_mat(iron_bindposes[idx])
    
    # In Unity: skinning = M_bone * BindPose
    prod = wm @ bp
    diff = np.abs(prod - np.eye(4)).max()
    max_errors.append(diff)
    print(f"Bone {idx}: max |M * B - I| = {diff:.6f}")

print(f"\nAverage error across first 10 bones: {np.mean(max_errors):.6f}")
