import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

bundle_path = r"E:\Agent\TFTF-blender\assets_redeco\blitzwing_gs.assetbundle"
env = UnityPy.load(bundle_path)

for obj in env.objects:
    if obj.type.name == "GameObject":
        d = obj.read()
        name = getattr(d, "m_Name", "")
        if "transformed" in name.lower():
            print(f"GameObject PathID {obj.path_id}: {name}")
            for comp in d.m_Components:
                print(f"  Component: {comp.type.name} (PID {comp.path_id})")
                if comp.type.name == "Animator":
                    tt = comp.read_typetree()
                    print(f"    Animator Controller: {tt.get('m_Controller')}")
