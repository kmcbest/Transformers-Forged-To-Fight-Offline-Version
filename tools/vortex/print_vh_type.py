import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

bundle_path = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\AssetBundles\vortex_mesh.assetbundle"
env = UnityPy.load(bundle_path)

for obj in env.objects:
    if obj.type.name == "Mesh":
        m = obj.read()
        if m.m_Name == "cha_vortex_vh_grafted":
            print("m_Vertices type:", type(m.m_Vertices))
            print("m_Vertices len:", len(m.m_Vertices))
            if len(m.m_Vertices) > 0:
                print("First item:", m.m_Vertices[0])
            break
