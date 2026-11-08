import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
import numpy as np

bundle_path = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\AssetBundles\vortex_mesh.assetbundle"
env = UnityPy.load(bundle_path)

for obj in env.objects:
    if obj.type.name == "Mesh":
        m = obj.read()
        if m.m_Name == "cha_vortex_vh_grafted":
            verts = np.array(m.m_Vertices).reshape(-1, 3)
            print(f"Total vertices: {len(verts)}")
            print(f"X min/max: [{verts[:, 0].min():.2f}, {verts[:, 0].max():.2f}]")
            print(f"Y min/max: [{verts[:, 1].min():.2f}, {verts[:, 1].max():.2f}]")
            print(f"Z min/max: [{verts[:, 2].min():.2f}, {verts[:, 2].max():.2f}]")
            # Find the nose (max/min Y) and tail
            nose_idx = np.argmax(verts[:, 1])
            tail_idx = np.argmin(verts[:, 1])
            print(f"Nose vertex at index {nose_idx}: {verts[nose_idx]}")
            print(f"Tail vertex at index {tail_idx}: {verts[tail_idx]}")
            # Find rotor top (max Z) and belly (min Z)
            rotor_idx = np.argmax(verts[:, 2])
            belly_idx = np.argmin(verts[:, 2])
            print(f"Rotor vertex at index {rotor_idx}: {verts[rotor_idx]}")
            print(f"Belly vertex at index {belly_idx}: {verts[belly_idx]}")
            break
