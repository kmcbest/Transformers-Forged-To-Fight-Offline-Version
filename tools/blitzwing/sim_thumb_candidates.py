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

def sim_hand(curl_deg=75.0):
    for side in ['Left', 'Right']:
        print(f"\n==================== SIMULATING {side} HAND (curl={curl_deg}°) ====================")
        # 1. Simulate Index finger curled
        p_idx1 = np.array(d['bones'][f'{side}HandIndex1']['unity_world_pos'])
        p_idx2 = np.array(d['bones'][f'{side}HandIndex2']['unity_world_pos'])
        p_idx3 = np.array(d['bones'][f'{side}HandIndex3']['unity_world_pos'])
        
        # Index curls around Z: Left +Z, Right -Z
        idx_sign = 1 if side == 'Left' else -1
        r_idx = R.from_euler('z', idx_sign * curl_deg, degrees=True)
        
        v12 = p_idx2 - p_idx1
        v23 = p_idx3 - p_idx2
        
        curled_idx2 = p_idx1 + r_idx.apply(v12)
        curled_idx3 = curled_idx2 + (r_idx * r_idx).apply(v23)
        print(f"Curled Index Knuckles:")
        print(f"  Index1: {np.round(p_idx1, 3)}")
        print(f"  Index2: {np.round(curled_idx2, 3)}")
        print(f"  Index3: {np.round(curled_idx3, 3)}")
        
        # 2. Simulate Thumb curled with new axis
        # Let's test different axes:
        # Axis A: Vector3.forward (Old buggy)
        # Axis B: Derived axis
        p_t1 = np.array(d['bones'][f'{side}HandThumb1']['unity_world_pos'])
        p_t2 = np.array(d['bones'][f'{side}HandThumb2']['unity_world_pos'])
        p_t3 = np.array(d['bones'][f'{side}HandThumb3']['unity_world_pos'])
        
        m_t1 = np.array([[d['bones'][f'{side}HandThumb1']['bind_pose_matrix'][f'e{r}{c}'] for c in range(4)] for r in range(4)])
        b2w_1 = np.linalg.inv(m_t1)
        
        v_t12 = p_t2 - p_t1
        v_t23 = p_t3 - p_t2
        
        for name, local_axis in [
            ("Old Buggy (0, 0, sign)", [0, 0, idx_sign]),
            ("Derived Natural Hinge", [0, -0.85 if side == 'Left' else -0.85, 0.52 if side == 'Left' else -0.52]),
            ("Inverted (0, 0, -sign)", [0, 0, -idx_sign]),
            ("Pure Y (0, -1, 0)", [0, -1, 0]),
            ("Swept Hinge [0, -0.7, 0.7*sign]", [0, -0.7071, 0.7071 * idx_sign])
        ]:
            axis_norm = np.array(local_axis) / np.linalg.norm(local_axis)
            # Apply to Thumb1 (sweep across) and Thumb2/3 (flex)
            # Bone-to-world rotation:
            # In Unity: world_rot = b2w * rot_local
            rot_t1 = R.from_rotvec(np.radians(curl_deg * 0.7) * axis_norm)
            rot_t2 = R.from_rotvec(np.radians(curl_deg * 0.9) * axis_norm)
            
            # In world:
            rot_w_1 = b2w_1[:3, :3] @ rot_t1.as_matrix() @ b2w_1[:3, :3].T
            curled_t2 = p_t1 + rot_w_1 @ v_t12
            
            rot_w_2 = rot_w_1 @ (b2w_1[:3, :3] @ rot_t2.as_matrix() @ b2w_1[:3, :3].T)
            curled_t3 = curled_t2 + rot_w_2 @ v_t23
            
            # Distance from curled_t3 to curled_idx2 (intermediate phalanx of index)
            dist_to_idx2 = np.linalg.norm(curled_t3 - curled_idx2)
            dist_to_idx3 = np.linalg.norm(curled_t3 - curled_idx3)
            
            print(f"\n  Candidate [{name}]:")
            print(f"    Thumb2: {np.round(curled_t2, 3)}")
            print(f"    Thumb3: {np.round(curled_t3, 3)}")
            print(f"    Distance to Index2: {dist_to_idx2:.3f} m, to Index3: {dist_to_idx3:.3f} m")

sim_hand(75.0)
