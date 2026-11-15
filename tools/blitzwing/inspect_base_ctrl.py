import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

p_bundle = Path(r"E:\Agent\TFTF-blender\assets_redeco\blitzwing_gs.assetbundle")
env = UnityPy.load(str(p_bundle))

for o in env.objects:
    if o.path_id == -4355188988576005738:
        tt = o.read_typetree()
        print("Type:", o.type.name)
        print("Name:", tt.get("m_Name"))
        print("States count:", len(tt.get("m_States", [])))
        for s in tt.get("m_States", []):
            print(f"  State: {s.get('m_State', {}).get('m_Name')} (hash={s.get('m_State', {}).get('m_NameHash')})")
