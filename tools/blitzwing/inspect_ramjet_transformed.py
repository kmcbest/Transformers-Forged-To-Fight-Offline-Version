import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

rj_bundle = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\ramjet_gs_deluxe2008_odr\ramjet_gs_deluxe2008.assetbundle")
env = UnityPy.load(str(rj_bundle))
obj_map = {o.path_id: o for o in env.objects}

for o in env.objects:
    if o.type.name == "GameObject":
        tt = o.read_typetree()
        if tt["m_Name"] == "transformed":
            print(f"\nRamjet GO 'transformed' PID {o.path_id}:")
            for c in tt["m_Component"]:
                cid = c["component"]["m_PathID"]
                if cid in obj_map:
                    comp = obj_map[cid]
                    print(f"  Component: {comp.type.name} (PID {cid})")
                    if comp.type.name == "Transform":
                        ctr = comp.read_typetree()
                        father_id = ctr["m_Father"]["m_PathID"]
                        father_name = obj_map[father_id].read_typetree().get("m_Name") if father_id in obj_map else "unknown"
                        children = [obj_map[ch["m_PathID"]].read_typetree().get("m_Name") for ch in ctr["m_Children"] if ch["m_PathID"] in obj_map]
                        print(f"    Father: {father_id} ({father_name})")
                        print(f"    Children: {children}")
                        print(f"    Pos: {ctr['m_LocalPosition']}, Rot: {ctr['m_LocalRotation']}")
                    elif comp.type.name == "Animator":
                        atr = comp.read_typetree()
                        print(f"    Controller: {atr.get('m_Controller')}")
                        print(f"    Avatar: {atr.get('m_Avatar')}")
