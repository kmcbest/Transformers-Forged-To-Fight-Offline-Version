import sys
from pathlib import Path
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(r"E:\Agent\TFTF-blender")
elita_bundle = ROOT / "assets_redeco" / "elita_one_gs.assetbundle"
arcee_bundle = ROOT / "extracted_apk" / "assets" / "assetpack" / "arcee_gs_deluxe2014_odr" / "arcee_gs_deluxe2014.assetbundle"

def check_cross_refs(bundle_path, label):
    print(f"\n==================== {label} ====================")
    env = UnityPy.load(str(bundle_path))
    
    go_dict = {}
    tr_dict = {}
    tr_to_go = {}
    go_to_tr = {}
    components_by_go = {}

    for obj in env.objects:
        if obj.type.name == "GameObject":
            go = obj.read_typetree()
            go_dict[obj.path_id] = go
            for c in go.get("m_Component", []):
                # c is {'component': {'m_FileID': 0, 'm_PathID': ...}}
                cid = c.get("component", {}).get("m_PathID")
                components_by_go.setdefault(obj.path_id, []).append(cid)
        elif obj.type.name == "Transform":
            tr = obj.read_typetree()
            tr_dict[obj.path_id] = tr
            go_id = tr.get("m_GameObject", {}).get("m_PathID")
            tr_to_go[obj.path_id] = go_id
            go_to_tr[go_id] = obj.path_id

    def get_prefab_nodes(root_go_id):
        gos = set()
        trs = set()
        comps = set()
        def recurse(gid):
            if gid in gos: return
            gos.add(gid)
            tid = go_to_tr.get(gid)
            if tid:
                trs.add(tid)
                tr = tr_dict.get(tid)
                if tr:
                    for child in tr.get("m_Children", []):
                        cid = child.get("m_PathID")
                        cgid = tr_to_go.get(cid)
                        if cgid:
                            recurse(cgid)
            for cid in components_by_go.get(gid, []):
                comps.add(cid)
        recurse(root_go_id)
        return gos, trs, comps

    p1_id = -5193028223035516378
    p2_id = -4037407093067927022

    p1_gos, p1_trs, p1_comps = get_prefab_nodes(p1_id)
    p2_gos, p2_trs, p2_comps = get_prefab_nodes(p2_id)

    print(f"P1: {len(p1_gos)} GOs, {len(p1_trs)} TRs, {len(p1_comps)} Comps")
    print(f"P2: {len(p2_gos)} GOs, {len(p2_trs)} TRs, {len(p2_comps)} Comps")

    p1_all = p1_gos | p1_trs | p1_comps
    p2_all = p2_gos | p2_trs | p2_comps

    overlap = p1_all & p2_all
    print(f"Direct overlap between P1 and P2: {len(overlap)}")
    if overlap:
        for x in overlap:
            print(f"  Overlap PID: {x}")

    # Now check if any component in P2 references any PID in P1, or vice versa
    def scan_refs(tree_obj):
        refs = []
        if isinstance(tree_obj, dict):
            if "m_PathID" in tree_obj:
                refs.append(tree_obj["m_PathID"])
            for v in tree_obj.values():
                refs.extend(scan_refs(v))
        elif isinstance(tree_obj, list):
            for v in tree_obj:
                refs.extend(scan_refs(v))
        return refs

    obj_dict = {obj.path_id: obj for obj in env.objects}
    
    # Check P2 objects referencing P1
    p2_to_p1_refs = []
    for pid in p2_all:
        if pid in obj_dict:
            try:
                tree = obj_dict[pid].read_typetree()
                refs = scan_refs(tree)
                for r in refs:
                    if r in p1_all:
                        p2_to_p1_refs.append((pid, obj_dict[pid].type.name, r))
            except Exception:
                pass
    
    # Check P1 objects referencing P2
    p1_to_p2_refs = []
    for pid in p1_all:
        if pid in obj_dict:
            try:
                tree = obj_dict[pid].read_typetree()
                refs = scan_refs(tree)
                for r in refs:
                    if r in p2_all:
                        p1_to_p2_refs.append((pid, obj_dict[pid].type.name, r))
            except Exception:
                pass

    print(f"P2 objects referencing P1: {len(p2_to_p1_refs)}")
    for src, tname, tgt in p2_to_p1_refs:
        print(f"  P2 {tname} ({src}) -> P1 ({tgt})")

    print(f"P1 objects referencing P2: {len(p1_to_p2_refs)}")
    for src, tname, tgt in p1_to_p2_refs:
        print(f"  P1 {tname} ({src}) -> P2 ({tgt})")

check_cross_refs(arcee_bundle, "ARCEE BASE")
check_cross_refs(elita_bundle, "ELITA ONE")
