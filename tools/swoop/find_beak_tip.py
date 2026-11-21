import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

mesh_bundle = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\AssetBundles\swoop_mesh.assetbundle")
env = UnityPy.load(str(mesh_bundle))

for obj in env.objects:
    if obj.type.name == "Mesh" and obj.read_typetree().get("m_Name") == "cha_swoop_gs_00":
        mesh = obj.read()
        verts = getattr(mesh, "m_Vertices", None)
        if verts is None:
            # try typetree
            tt = obj.read_typetree()
            # check if vertices can be read
            print("m_Vertices not on object directly")
        else:
            print(f"Total vertices: {len(verts)}")
            # verts could be list of Vector3 or tuples
            chest_verts = []
            for v in verts:
                vx, vy, vz = getattr(v, "X", v[0]), getattr(v, "Y", v[1]), getattr(v, "Z", v[2])
                if 5.0 <= vy <= 8.5 and abs(vx) < 0.8:
                    chest_verts.append((vx, vy, vz))
            chest_verts.sort(key=lambda v: v[2], reverse=True)
            print("Top 10 forwardmost chest vertices (Pteranodon Beak Tip):")
            for v in chest_verts[:10]:
                print(f"  X={v[0]:.3f}, Y={v[1]:.3f}, Z={v[2]:.3f}")
        break
