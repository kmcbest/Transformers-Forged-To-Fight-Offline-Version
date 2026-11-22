import sys, os
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

sys.path.insert(0, r"E:\Agent\TFTF-blender")
import UnityPy
import numpy as np
from pathlib import Path
from tools.validate_port_gates import parse_unity_mesh_streams

donor_path = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatronus_gs_kabam_odr\megatronus_gs_kabam.assetbundle")
mesh_path = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\AssetBundles\blastoff_mesh.assetbundle")

env_d = UnityPy.load(str(donor_path))
env_m = UnityPy.load(str(mesh_path))

d_tt = next(o.read_typetree() for o in env_d.objects if o.type.name == 'Mesh' and o.read_typetree()['m_Name'].endswith('_00') and 'wpns' not in o.read_typetree()['m_Name'].lower())
av = next(o.read_typetree() for o in env_d.objects if o.type.name == 'Avatar')
tos = dict(av.get('m_TOS', []))
bone_names = [tos.get(h, f'h_{h}').split('/')[-1] for h in d_tt['m_BoneNameHashes']]

m_tt = next(o.read_typetree() for o in env_m.objects if o.type.name == 'Mesh' and o.read_typetree()['m_Name'] == 'cha_blastoff_gs_00')
pts, uvs, ws, bi = parse_unity_mesh_streams(m_tt)

print(f"{'Bone Name':20s} | {'Donor Bone (X, Y, Z)':26s} | {'BlastOff Verts Mean (X, Y, Z)':32s} | {'Diff X':8s}")
print("-" * 95)

for bidx, bname in enumerate(bone_names):
    bp = d_tt['m_BindPose'][bidx]
    mat = np.array([
        [bp['e00'], bp['e01'], bp['e02'], bp['e03']],
        [bp['e10'], bp['e11'], bp['e12'], bp['e13']],
        [bp['e20'], bp['e21'], bp['e22'], bp['e23']],
        [bp['e30'], bp['e31'], bp['e32'], bp['e33']],
    ])
    inv = np.linalg.inv(mat)
    bx, by, bz = inv[0, 3], inv[1, 3], inv[2, 3]

    mask = (bi[:, 0] == bidx) & (ws[:, 0] > 0.4)
    if mask.sum() > 0:
        vx, vy, vz = pts[mask, 0].mean(), pts[mask, 1].mean(), pts[mask, 2].mean()
        dx = abs(vx - bx)
        flag = " [FAIL]" if dx > 1.5 and any(k in bname for k in ['Arm', 'Leg']) else ""
        print(f"{bname:20s} | ({bx:+7.3f}, {by:+7.3f}, {bz:+7.3f}) | ({vx:+7.3f}, {vy:+7.3f}, {vz:+7.3f}) [n={mask.sum():4d}] | {dx:6.3f}{flag}")
    else:
        print(f"{bname:20s} | ({bx:+7.3f}, {by:+7.3f}, {bz:+7.3f}) | NO VERTS")
