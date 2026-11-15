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

for side, axis_sign in [('Left', +1), ('Right', -1)]:
    bname = f'{side}HandThumb1'
    m_data = d['bones'][bname]['bind_pose_matrix']
    m = np.array([[m_data[f'e{r}{c}'] for c in range(4)] for r in range(4)])
    b2w = np.linalg.inv(m)
    loc_x = b2w[:3, 0]
    loc_y = b2w[:3, 1]
    loc_z = b2w[:3, 2]
    
    # Bone vector in rest:
    p1 = np.array(d['bones'][f'{side}HandThumb1']['unity_world_pos'])
    p2 = np.array(d['bones'][f'{side}HandThumb2']['unity_world_pos'])
    bone_v = p2 - p1
    
    print(f"=== {side} Thumb ===")
    print("  Local X in world:", np.round(loc_x, 4))
    print("  Local Y in world:", np.round(loc_y, 4))
    print("  Local Z in world:", np.round(loc_z, 4))
    print("  Bone vector in rest:", np.round(bone_v, 4))
    
    # When rotated by 70 deg around local axis (0, 0, axis_sign):
    theta = np.radians(70.0 * axis_sign)
    rot_local = R.from_rotvec([0, 0, theta])
    
    # Bone in local coords is [-len, 0, 0]
    bone_len = np.linalg.norm(bone_v)
    v_local_curled = rot_local.apply([-bone_len, 0, 0])
    v_world_curled = v_local_curled[0] * loc_x + v_local_curled[1] * loc_y + v_local_curled[2] * loc_z
    print(f"  Curled bone vector in world (theta=70 deg, axis=(0,0,{axis_sign})):", np.round(v_world_curled, 4))
