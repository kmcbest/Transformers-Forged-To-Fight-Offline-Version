import sys
from pathlib import Path
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(r"E:\Agent\TFTF-blender")
elita_bundle = ROOT / "toolchain" / "unity_build_project" / "AssetBundles" / "elita_one_mesh.assetbundle"
env = UnityPy.load(str(elita_bundle))

d_path_to_name = {}
for obj in env.objects:
    if obj.type.name == "Transform":
        t = obj.read_typetree()
        go_ptr = t.get("m_GameObject", {})
        for g_obj in env.objects:
            if g_obj.path_id == go_ptr.get("m_PathID") and g_obj.type.name == "GameObject":
                d_path_to_name[obj.path_id] = g_obj.read_typetree().get("m_Name")
                break

for obj in env.objects:
    if obj.type.name == "SkinnedMeshRenderer":
        tree = obj.read_typetree()
        bones = [d_path_to_name.get(b.get("m_PathID")) for b in tree.get("m_Bones", [])]
        print(f"Compiled SMR has {len(bones)} bones:")
        for idx, b in enumerate(bones):
            print(f"  {idx:2d}: {b}")
