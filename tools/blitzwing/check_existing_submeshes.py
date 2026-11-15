import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

p_mesh = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\AssetBundles\blitzwing_mesh.assetbundle")
env = UnityPy.load(str(p_mesh))

for o in env.objects:
    if o.type.name == "Mesh":
        tt = o.read_typetree()
        name = tt["m_Name"]
        if "tank" in name or "jet" in name:
            print(f"\nMesh: '{name}'")
            print("  submeshes:", len(tt["m_SubMeshes"]))
            for s, sm in enumerate(tt["m_SubMeshes"]):
                print(f"    Submesh {s}: firstVertex={sm.get('firstVertex')}, vertexCount={sm.get('vertexCount')}, indexCount={sm.get('indexCount')}, firstByte={sm.get('firstByte')}")
