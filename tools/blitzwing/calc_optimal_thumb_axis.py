import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
import numpy as np
from scipy.spatial.transform import Rotation as R

with open(r'E:\Agent\TFTF-blender\tools\blitzwing\megatron_51_authoritative_bindposes.json', encoding='utf-8') as f:
    d = json.load(f)

for side, expected_dir in [('Left', [-0.126, -0.517, -0.024]), ('Right', [+0.126, -0.517, -0.024])]:
    bname = f'{side}HandThumb1'
    m_data = d[f'bones'][bname]['bind_pose_matrix']
    m = np.array([[m_data[f'e{r}{c}'] for c in range(4)] for r in range(4)])
    b2w = np.linalg.inv(m)
    loc_x = b2w[:3, 0]
    loc_y = b2w[:3, 1]
    loc_z = b2w[:3, 2]
    
    p_t1 = np.array(d['bones'][f'{side}HandThumb1']['unity_world_pos'])
    p_idx = np.array(d['bones'][f'{side}HandIndex1']['unity_world_pos'])
    
    # Target direction: from Thumb1 towards index finger when curled
    # Index finger curls down around Y=4.5..4.8, Z=0.35..0.45
    targ_vec = p_idx - p_t1
    targ_dir = targ_vec / np.linalg.norm(targ_vec)
    
    # Current bone direction in rest
    p_t2 = np.array(d['bones'][f'{side}HandThumb2']['unity_world_pos'])
    rest_dir = (p_t2 - p_t1) / np.linalg.norm(p_t2 - p_t1)
    
    print(f"\n==================== {side} Thumb ====================")
    print(f"Thumb1 pos: {np.round(p_t1, 3)}")
    print(f"Index1 pos: {np.round(p_idx, 3)}")
    print(f"Target direction towards Index1: {np.round(targ_dir, 3)}")
    print(f"Rest thumb direction: {np.round(rest_dir, 3)}")
    
    # What rotation R takes rest_dir towards targ_dir?
    # In world space:
    # rot_axis_world = cross(rest_dir, targ_dir)
    rot_axis_world = np.cross(rest_dir, targ_dir)
    rot_axis_world = rot_axis_world / np.linalg.norm(rot_axis_world)
    angle_deg = np.degrees(np.arccos(np.clip(np.dot(rest_dir, targ_dir), -1, 1)))
    print(f"World rotation axis to reach index: {np.round(rot_axis_world, 3)}, angle: {angle_deg:.1f} deg")
    
    # Convert rot_axis_world into bone local coordinates!
    # rot_axis_local = [dot(rot_axis_world, loc_x), dot(rot_axis_world, loc_y), dot(rot_axis_world, loc_z)]
    rot_axis_local = np.array([
        np.dot(rot_axis_world, loc_x),
        np.dot(rot_axis_world, loc_y),
        np.dot(rot_axis_world, loc_z)
    ])
    print(f"Bone LOCAL rotation axis: {np.round(rot_axis_local, 3)}")
