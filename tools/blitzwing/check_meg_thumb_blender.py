import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
from pathlib import Path
import bpy
from mathutils import Vector, Matrix, Quaternion
import numpy as np

ROOT = Path(r"E:\Agent\TFTF-blender")
BLEND_SRC = ROOT / "3rd-party-models" / "blitzwing_extracted" / "rar" / "Blitzwing.blend"
MEG_51_JSON = ROOT / "tools" / "blitzwing" / "megatron_51_authoritative_bindposes.json"
meg_data = json.loads(MEG_51_JSON.read_text(encoding="utf-8"))

def u_to_b(pos):
    return Vector((-float(pos[0]), -float(pos[2]), float(pos[1])))

# Megatron bind pose matrix in Unity:
# bp is inv(WorldMatrix). So WorldMatrix = inv(bp).
def get_meg_world_mat_in_blender(bname):
    bp = meg_data["bones"][bname]["bind_pose_matrix"]
    m_u = np.array([
        [bp['e00'], bp['e01'], bp['e02'], bp['e03']],
        [bp['e10'], bp['e11'], bp['e12'], bp['e13']],
        [bp['e20'], bp['e21'], bp['e22'], bp['e23']],
        [bp['e30'], bp['e31'], bp['e32'], bp['e33']]
    ])
    inv_u = np.linalg.inv(m_u)
    
    # Unity -> Blender change of basis:
    # ux = -bx => bx = -ux
    # uy = bz  => by = -uz
    # uz = -by => bz = uy
    # P = [[-1, 0, 0, 0], [0, 0, -1, 0], [0, 1, 0, 0], [0, 0, 0, 1]]
    P = np.array([
        [-1,  0,  0,  0],
        [ 0,  0, -1,  0],
        [ 0,  1,  0,  0],
        [ 0,  0,  0,  1]
    ])
    inv_P = np.linalg.inv(P)
    m_b = P @ inv_u @ inv_P
    
    b_mat = Matrix()
    for r in range(4):
        for c in range(4):
            b_mat[r][c] = m_b[r, c]
    return b_mat

print("=== Megatron Thumb Bindpose in Blender Space ===")
for side, pfx in [("L", "Left"), ("R", "Right")]:
    for k in [1, 2, 3]:
        bname = f"{pfx}HandThumb{k}"
        M = get_meg_world_mat_in_blender(bname)
        print(f"\n{bname}:")
        print(f"  Head pos: {M.translation.to_tuple(3)}")
        print(f"  Col 0 (X axis): {M.to_3x3()[0].to_tuple(3)}")
        print(f"  Col 1 (Y axis): {M.to_3x3()[1].to_tuple(3)}")
        print(f"  Col 2 (Z axis): {M.to_3x3()[2].to_tuple(3)}")
