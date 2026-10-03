import sys
from pathlib import Path
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(r"E:\Agent\TFTF-blender")
elita_bundle = ROOT / "assets_redeco" / "elita_one_gs.assetbundle"
arcee_bundle = ROOT / "extracted_apk" / "assets" / "assetpack" / "arcee_gs_deluxe2014_odr" / "arcee_gs_deluxe2014.assetbundle"

e_env = UnityPy.load(str(elita_bundle))
a_env = UnityPy.load(str(arcee_bundle))

e_objs = {obj.path_id: obj for obj in e_env.objects}
a_objs = {obj.path_id: obj for obj in a_env.objects}

def dict_diff(d1, d2, path=""):
    diffs = []
    if type(d1) != type(d2):
        return [f"{path}: type mismatch {type(d1)} != {type(d2)}"]
    if isinstance(d1, dict):
        all_keys = set(d1.keys()) | set(d2.keys())
        for k in all_keys:
            if k not in d1:
                diffs.append(f"{path}.{k}: missing in Arcee")
            elif k not in d2:
                diffs.append(f"{path}.{k}: missing in Elita")
            else:
                diffs.extend(dict_diff(d1[k], d2[k], f"{path}.{k}"))
    elif isinstance(d1, list):
        if len(d1) != len(d2):
            diffs.append(f"{path}: len {len(d1)} != {len(d2)}")
        for i in range(min(len(d1), len(d2))):
            diffs.extend(dict_diff(d1[i], d2[i], f"{path}[{i}]"))
    else:
        if d1 != d2:
            diffs.append(f"{path}: {d1} != {d2}")
    return diffs

target_pids = [-990971635626090465, 3949589716393965935, -4178002549372221558, 8283545308434878436]

for pid in target_pids:
    at = a_objs[pid].read_typetree()
    et = e_objs[pid].read_typetree()
    diffs = dict_diff(at, et)
    print(f"\n--- SMR {pid} Diffs ({len(diffs)}) ---")
    for d in diffs[:20]:
        print(" ", d)

print("\n--- Mesh 5260487394226442925 (Robot) Diffs ---")
m0_at = a_objs[5260487394226442925].read_typetree()
m0_et = e_objs[5260487394226442925].read_typetree()
# Ignore vertex data raw buffers
m0_at_meta = {k: v for k, v in m0_at.items() if k not in ["m_VertexData", "m_IndexBuffer", "m_Skin"]}
m0_et_meta = {k: v for k, v in m0_et.items() if k not in ["m_VertexData", "m_IndexBuffer", "m_Skin"]}
for d in dict_diff(m0_at_meta, m0_et_meta)[:25]:
    print(" ", d)

print("\n--- Mesh 8812986522665902312 (Vehicle) Diffs ---")
m1_at = a_objs[8812986522665902312].read_typetree()
m1_et = e_objs[8812986522665902312].read_typetree()
m1_at_meta = {k: v for k, v in m1_at.items() if k not in ["m_VertexData", "m_IndexBuffer", "m_Skin"]}
m1_et_meta = {k: v for k, v in m1_et.items() if k not in ["m_VertexData", "m_IndexBuffer", "m_Skin"]}
for d in dict_diff(m1_at_meta, m1_et_meta)[:25]:
    print(" ", d)
