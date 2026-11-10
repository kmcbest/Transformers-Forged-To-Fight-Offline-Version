import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

p_prowl = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\prowl_gs_deluxe2016_odr\prowl_gs_deluxe2016.assetbundle")
env = UnityPy.load(str(p_prowl))

id_to_name = {}
for obj in env.objects:
    if obj.type.name == "GameObject":
        tree = obj.read_typetree()
        id_to_name[obj.path_id] = tree.get("m_Name", "")

tr_nodes = {}
for obj in env.objects:
    if obj.type.name == "Transform":
        tree = obj.read_typetree()
        go_pid = tree.get("m_GameObject", {}).get("m_PathID", 0)
        tr_nodes[obj.path_id] = {
            "name": id_to_name.get(go_pid, ""),
            "parent": tree.get("m_Father", {}).get("m_PathID", 0),
            "children": [c.get("m_PathID", 0) for c in tree.get("m_Children", [])]
        }

for obj in env.objects:
    if obj.type.name == "SkinnedMeshRenderer":
        tree = obj.read_typetree()
        go_pid = tree.get("m_GameObject", {}).get("m_PathID", 0)
        smr_name = id_to_name.get(go_pid, "")
        # trace parents
        tr_pid = tree.get("m_GameObject", {}).get("m_PathID", 0) # wait, transform has go_pid
        # find transform for this go
        t_pid = next((tid for tid, td in tr_nodes.items() if td["name"] == smr_name), 0)
        hierarchy = [smr_name]
        curr = t_pid
        while curr and curr in tr_nodes:
            p_tr = tr_nodes[curr]["parent"]
            if p_tr in tr_nodes:
                hierarchy.append(tr_nodes[p_tr]["name"])
                curr = p_tr
            else:
                break
        print(f"SMR '{smr_name}': hierarchy = {' -> '.join(reversed(hierarchy))}")
