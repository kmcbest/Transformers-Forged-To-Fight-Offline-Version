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
    if obj.type.name == "Mesh":
        tree = obj.read_typetree()
        if tree.get("m_Name") == "cha_elita_one_gs_00":
            bp = tree.get("m_BindPose", [])
            print(f"Mesh cha_elita_one_gs_00 bindpose count: {len(bp)}")
    elif obj.type.name == "SkinnedMeshRenderer":
        tree = obj.read_typetree()
        bones = [d_path_to_name.get(b.get("m_PathID")) for b in tree.get("m_Bones", [])]
        print(f"SMR bone count: {len(bones)}")
        print("SMR bone names:", bones[:15])
