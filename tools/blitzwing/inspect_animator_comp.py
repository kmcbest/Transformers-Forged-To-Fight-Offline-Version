import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

p_bundle = Path(r"E:\Agent\TFTF-blender\assets_redeco\blitzwing_gs.assetbundle")
env = UnityPy.load(str(p_bundle))
obj_map = {o.path_id: o for o in env.objects}

for o in env.objects:
    if o.type.name == "GameObject":
        tt = o.read_typetree()
        if tt["m_Name"] in ("transformed", "transformed_2", "cannon"):
            print(f"\nGO '{tt['m_Name']}' (PID {o.path_id}):")
            for c in tt["m_Component"]:
                cid = c["component"]["m_PathID"]
                if cid in obj_map:
                    comp_type = obj_map[cid].type.name
                    print(f"  Component {comp_type} (PID {cid})")
                    if comp_type == "Animator":
                        atr = obj_map[cid].read_typetree()
                        print(f"    Controller: {atr.get('m_Controller')}")
