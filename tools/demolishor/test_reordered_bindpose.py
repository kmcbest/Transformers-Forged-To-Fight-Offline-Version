# -*- coding: utf-8 -*-
import sys
import numpy as np
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

# 1. Load Ironhide
env_i = UnityPy.load('extracted_apk/assets/assetpack/ironhide_cin_rotf_odr/ironhide_cin_rotf.assetbundle')

# Ironhide bindposes and bones
iron_bindposes = None
for obj in env_i.objects:
    if obj.type.name == 'Mesh':
        tree = obj.read_typetree()
        if tree.get('m_Name') == 'cha_ironhide_cin_rotf_00':
            iron_bindposes = tree.get('m_BindPose', [])
            break

go_names = {}
tr_to_go = {}
tr_dict = {}
for obj in env_i.objects:
    if obj.type.name == 'GameObject':
        go_names[obj.path_id] = obj.read_typetree().get('m_Name')
    elif obj.type.name == 'Transform':
        tree = obj.read_typetree()
        tr_dict[obj.path_id] = tree
        tr_to_go[obj.path_id] = tree.get('m_GameObject', {}).get('m_PathID')

iron_smr_bones = []
for obj in env_i.objects:
    if obj.type.name == 'SkinnedMeshRenderer':
        tree = obj.read_typetree()
        bones = tree.get('m_Bones', [])
        if len(bones) == 80:
            for b in bones:
                tr_id = b.get('m_PathID')
                iron_smr_bones.append(go_names.get(tr_to_go.get(tr_id)))
            break

# 2. Load Demolishor bundle
env_d = UnityPy.load('assets_redeco/demolishor_gs.assetbundle')
demo_smr_bones = []
for obj in env_d.objects:
    if obj.type.name == 'SkinnedMeshRenderer':
        tree = obj.read_typetree()
        bones = tree.get('m_Bones', [])
        if len(bones) == 80:
            for b in bones:
                tr_id = b.get('m_PathID')
                demo_smr_bones.append(go_names.get(tr_to_go.get(tr_id)))
            break

print(f"Ironhide bones: {len(iron_smr_bones)}")
print(f"Demolishor bones: {len(demo_smr_bones)}")

# Build transform lookup
def bp_to_mat(bp):
    return np.array([
        [bp['e00'], bp['e01'], bp['e02'], bp['e03']],
        [bp['e10'], bp['e11'], bp['e12'], bp['e13']],
        [bp['e20'], bp['e21'], bp['e22'], bp['e23']],
        [bp['e30'], bp['e31'], bp['e32'], bp['e33']]
    ])

# Map each Demolishor bone to its corresponding Ironhide bindpose
matched_count = 0
reordered_bindposes = []
for j, bname in enumerate(demo_smr_bones):
    if bname in iron_smr_bones:
        iron_idx = iron_smr_bones.index(bname)
        reordered_bindposes.append(iron_bindposes[iron_idx])
        matched_count += 1
    else:
        print(f"Bone {bname} not found in Ironhide!")

print(f"Successfully mapped {matched_count} / {len(demo_smr_bones)} bindposes!")

# Verify for Demolishor SMR:
# Does M_demo_bone * reordered_bindpose == Identity?
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
    return t_mat @ q_to_rot(rot) @ np.diag([scale['x'], scale['y'], scale['z'], 1.0])

world_matrices = {}
def get_world(tr_id):
    if tr_id in world_matrices: return world_matrices[tr_id]
    tr = tr_dict[tr_id]
    local_m = tr_to_mat(tr)
    p_id = tr.get('m_Father', {}).get('m_PathID', 0)
    wm = get_world(p_id) @ local_m if (p_id and p_id in tr_dict) else local_m
    world_matrices[tr_id] = wm
    return wm

errors = []
target_demo_smr = None
for obj in env_d.objects:
    if obj.type.name == 'SkinnedMeshRenderer':
        tree = obj.read_typetree()
        if len(tree.get('m_Bones', [])) == 80:
            target_demo_smr = tree
            break

for j, b in enumerate(target_demo_smr.get('m_Bones', [])):
    tr_id = b.get('m_PathID')
    wm = get_world(tr_id)
    bp = bp_to_mat(reordered_bindposes[j])
    prod = wm @ bp
    diff = np.abs(prod - np.eye(4)).max()
    errors.append(diff)

print(f"Max error across all 80 bones: {max(errors):.6f}")
print(f"Mean error across all 80 bones: {np.mean(errors):.6f}")
