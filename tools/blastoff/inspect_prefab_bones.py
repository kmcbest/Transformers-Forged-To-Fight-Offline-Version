import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

TARGET = Path("assets_redeco/blastoff_gs.assetbundle")
env = UnityPy.load(str(TARGET))
obj_map = {o.path_id: o for o in env.objects}

for o in env.objects:
    if o.type.name == "GameObject":
        tt = o.read_typetree()
        name = tt.get("m_Name")
        if name in ("Blastoff_GS", "Blastoff_GS_lw", "Reference", "Hips", "character_model"):
            print(f"GameObject {name} (PID={o.path_id}):")
            for comp in tt.get("m_Component", []):
                c_obj = obj_map.get(comp["component"]["m_PathID"])
                if c_obj and c_obj.type.name == "Transform":
                    t_tt = c_obj.read_typetree()
                    print(f"  Transform m_LocalPosition: {t_tt.get('m_LocalPosition')}")
                    print(f"  Transform m_LocalScale: {t_tt.get('m_LocalScale')}")
