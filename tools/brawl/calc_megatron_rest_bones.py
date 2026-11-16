import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
import numpy as np

with open(r'E:\Agent\TFTF-blender\3rd-party-models\Brawl\00_donor_reference\donor_summary.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

mesh = d['meshes']['cha_megatron_cin_rotf_00']
avatar_tos = d['avatars']['cha_megatron_cin_rotf_00Avatar']['tos']

print("--- MEGAMATRON CIN REST POSE BONE POSITIONS (Unity Space) ---")
rest_positions = {}
for idx, (h, bp) in enumerate(zip(mesh['boneHashes'], mesh['bindposes'])):
    mat = np.array([
        [bp['e00'], bp['e01'], bp['e02'], bp['e03']],
        [bp['e10'], bp['e11'], bp['e12'], bp['e13']],
        [bp['e20'], bp['e21'], bp['e22'], bp['e23']],
        [bp['e30'], bp['e31'], bp['e32'], bp['e33']]
    ])
    inv_mat = np.linalg.inv(mat)
    pos = inv_mat[:3, 3]
    h_str = str(h)
    bone_path = avatar_tos.get(h_str, "UNKNOWN")
    short_name = bone_path.split('/')[-1] if bone_path != "UNKNOWN" else f"bone_{idx}"
    rest_positions[short_name] = pos
    print(f"[{idx:02d}] {short_name:<16}: Unity Pos = ({pos[0]:8.4f}, {pos[1]:8.4f}, {pos[2]:8.4f})")

# Also check overall bounds of cha_megatron_cin_rotf_00_robot.obj
with open(r'E:\Agent\TFTF-blender\3rd-party-models\Brawl\00_donor_reference\cha_megatron_cin_rotf_00_robot.obj', 'r') as f:
    verts = []
    for line in f:
        if line.startswith('v '):
            parts = line.strip().split()
            verts.append([float(parts[1]), float(parts[2]), float(parts[3])])
    verts = np.array(verts)
    print("\nMegatron Robot OBJ bounds:")
    print(f"  X: [{verts[:,0].min():.4f}, {verts[:,0].max():.4f}] (span={verts[:,0].max()-verts[:,0].min():.4f})")
    print(f"  Y: [{verts[:,1].min():.4f}, {verts[:,1].max():.4f}] (span={verts[:,1].max()-verts[:,1].min():.4f})")
    print(f"  Z: [{verts[:,2].min():.4f}, {verts[:,2].max():.4f}] (span={verts[:,2].max()-verts[:,2].min():.4f})")
