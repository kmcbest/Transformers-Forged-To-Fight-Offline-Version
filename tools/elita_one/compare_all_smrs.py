import sys
from pathlib import Path
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(r"E:\Agent\TFTF-blender")
elita_bundle = ROOT / "assets_redeco" / "elita_one_gs.assetbundle"
arcee_bundle = ROOT / "extracted_apk" / "assets" / "assetpack" / "arcee_gs_deluxe2014_odr" / "arcee_gs_deluxe2014.assetbundle"

def inspect_bundle(bundle_path, name):
    print(f"\n==================== {name} ====================")
    env = UnityPy.load(str(bundle_path))
    go_dict = {}
    tr_dict = {}
    tr_to_go = {}
    go_to_tr = {}

    for obj in env.objects:
        if obj.type.name == "GameObject":
            go_dict[obj.path_id] = obj.read_typetree()
        elif obj.type.name == "Transform":
            tr = obj.read_typetree()
            tr_dict[obj.path_id] = tr
            go_id = tr.get("m_GameObject", {}).get("m_PathID")
            tr_to_go[obj.path_id] = go_id
            go_to_tr[go_id] = obj.path_id

    def get_prefab_transforms(root_go_id):
        result = {}
        def recurse(go_id):
            go = go_dict.get(go_id)
            if not go: return
            n = go.get('m_Name')
            tr_id = go_to_tr.get(go_id)
            if n not in result:
                result[n] = tr_id
            tr = tr_dict.get(tr_id)
            if tr:
                for child in tr.get('m_Children', []):
                    c_tr_id = child.get('m_PathID')
                    c_go_id = tr_to_go.get(c_tr_id)
                    recurse(c_go_id)
        recurse(root_go_id)
        return result

    # Identify root GameObjects
    root_gos = []
    for pid, go in go_dict.items():
        tr_id = go_to_tr.get(pid)
        tr = tr_dict.get(tr_id)
        if tr and tr.get("m_Father", {}).get("m_PathID") == 0:
            root_gos.append((pid, go.get("m_Name")))
    print(f"Root GameObjects: {root_gos}")

    p1_id = -5193028223035516378
    p2_id = -4037407093067927022
    p1_tr = get_prefab_transforms(p1_id)
    p2_tr = get_prefab_transforms(p2_id)
    print(f"P1 ({p1_id}) tr count: {len(p1_tr)}, P2 ({p2_id}) tr count: {len(p2_tr)}")

    for obj in env.objects:
        if obj.type.name == "SkinnedMeshRenderer":
            smr = obj.read_typetree()
            go_id = smr.get("m_GameObject", {}).get("m_PathID")
            go_name = go_dict.get(go_id, {}).get("m_Name", "unknown")
            mesh_id = smr.get("m_Mesh", {}).get("m_PathID")
            root_bone = smr.get("m_RootBone", {}).get("m_PathID")
            bones = smr.get("m_Bones", [])
            in_p1 = sum(1 for b in bones if b.get("m_PathID") in p1_tr.values())
            in_p2 = sum(1 for b in bones if b.get("m_PathID") in p2_tr.values())
            rb_in_p1 = root_bone in p1_tr.values()
            rb_in_p2 = root_bone in p2_tr.values()
            mats = [m.get("m_PathID") for m in smr.get("m_Materials", [])]
            print(f"SMR PID {obj.path_id} (GO: {go_name}, Mesh: {mesh_id}):")
            print(f"  Bones count: {len(bones)} | In P1: {in_p1}, In P2: {in_p2}")
            print(f"  RootBone: {root_bone} (in P1: {rb_in_p1}, in P2: {rb_in_p2})")
            print(f"  Materials: {mats}")

inspect_bundle(arcee_bundle, "ARCEE ORIGINAL")
inspect_bundle(elita_bundle, "ELITA ONE CURRENT")
