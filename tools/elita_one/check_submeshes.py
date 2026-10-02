import sys
from pathlib import Path
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(r"E:\Agent\TFTF-blender")
elita_bundle = ROOT / "toolchain" / "unity_build_project" / "AssetBundles" / "elita_one_mesh.assetbundle"
env = UnityPy.load(str(elita_bundle))

for obj in env.objects:
    if obj.type.name == "Mesh":
        tree = obj.read_typetree()
        if tree.get("m_Name") == "cha_elita_one_gs_00":
            sms = tree.get("m_SubMeshes", [])
            print(f"Submeshes count: {len(sms)}")
            for i, sm in enumerate(sms):
                print(f"  Submesh {i}: firstByte={sm.get('firstByte')}, indexCount={sm.get('indexCount')}, topology={sm.get('topology')}")
