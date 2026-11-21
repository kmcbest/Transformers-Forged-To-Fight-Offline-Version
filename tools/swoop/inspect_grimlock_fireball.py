import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\grimlock_gs_mp08_odr\grimlock_gs_mp08.assetbundle")
env = UnityPy.load(str(bundle_path))
obj_map = {obj.path_id: obj for obj in env.objects}

fireball_go = obj_map.get(5433757232512100521)
if fireball_go:
    d = fireball_go.read_typetree()
    print("projectile_grimlock_fireball components:")
    for c in d.get("m_Component", []):
        cid = c.get("component", {}).get("m_PathID")
        c_obj = obj_map.get(cid)
        if c_obj:
            print(f"  [{c_obj.type.name}] PID={cid}")
            if c_obj.type.name == "MonoBehaviour":
                m_tt = c_obj.read_typetree()
                print("    MonoBehaviour name:", m_tt.get("m_Name"), "script:", m_tt.get("m_Script"))
            elif c_obj.type.name == "Transform":
                td = c_obj.read_typetree()
                print(f"    Transform pos={td.get('m_LocalPosition')}, rot={td.get('m_LocalRotation')}, scale={td.get('m_LocalScale')}")
                for ch in td.get("m_Children", []):
                    ch_tr = obj_map.get(ch.get("m_PathID"))
                    if ch_tr:
                        ch_go = obj_map.get(ch_tr.read_typetree().get("m_GameObject", {}).get("m_PathID"))
                        if ch_go:
                            print(f"      Child: {ch_go.read_typetree().get('m_Name')} (PID={ch_go.path_id})")
