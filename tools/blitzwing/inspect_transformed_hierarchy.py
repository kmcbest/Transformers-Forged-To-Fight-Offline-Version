import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

donor_path = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_gs_leader2015_odr\megatron_gs_leader2015.assetbundle")
env = UnityPy.load(str(donor_path))

for o in env.objects:
    if o.type.name == "GameObject":
        tt = o.read_typetree()
        if tt["m_Name"] == "transformed":
            print(f"GameObject 'transformed': PathID={o.path_id}")
            comps = tt.get("m_Component", [])
            for c in comps:
                comp_pid = c["component"]["m_PathID"]
                for obj in env.objects:
                    if obj.path_id == comp_pid:
                        print(f"  Component: {obj.type.name} (PID={obj.path_id})")
                        if obj.type.name == "Transform":
                            tr = obj.read_typetree()
                            print(f"    Children count: {len(tr.get('m_Children', []))}")
                            for ch in tr.get("m_Children", []):
                                ch_pid = ch["m_PathID"]
                                for o2 in env.objects:
                                    if o2.path_id == ch_pid:
                                        ch_tr = o2.read_typetree()
                                        go_pid = ch_tr["m_GameObject"]["m_PathID"]
                                        for o3 in env.objects:
                                            if o3.path_id == go_pid:
                                                print(f"      Child GO: '{o3.read_typetree()['m_Name']}'")
