import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path("e:/Agent/TFTF-blender/assets_redeco/blitzwing_gs.assetbundle")
env = UnityPy.load(str(bundle_path))
obj_map = {o.path_id: o for o in env.objects}

print("=== CHECKING TANK GAMEOBJECT AND TRANSFORM HIERARCHY ===")

# Tank SMR GameObjects: Showcase=-5385736693872477217, Combat=6479682388170250398
for name, go_pid in [("Showcase Tank GO", -5385736693872477217), ("Combat Tank GO", 6479682388170250398)]:
    if go_pid in obj_map:
        go = obj_map[go_pid].read_typetree()
        print(f"\n{name} (PID {go_pid}):")
        print(f"  Name: {go.get('m_Name')}, Active: {go.get('m_IsActive')}")
        print(f"  Components: {go.get('m_Component')}")
        for comp in go.get('m_Component', []):
            c_pid = comp['component']['m_PathID']
            c_obj = obj_map.get(c_pid)
            if c_obj:
                c_tt = c_obj.read_typetree()
                if c_obj.type.name == "Transform":
                    print(f"  Transform {c_pid}: pos={c_tt.get('m_LocalPosition')}, rot={c_tt.get('m_LocalRotation')}, scale={c_tt.get('m_LocalScale')}, parent={c_tt.get('m_Father')}")
                elif c_obj.type.name == "SkinnedMeshRenderer":
                    print(f"  SMR {c_pid}: enabled={c_tt.get('m_Enabled')}, rootBone={c_tt.get('m_RootBone')}, bones={c_tt.get('m_Bones')}")

# Jet SMR GameObjects: Showcase=-7481134504555158405, Combat=3992037002325232027
for name, smr_pid in [("Showcase Jet SMR", -7481134504555158405), ("Combat Jet SMR", 3992037002325232027)]:
    if smr_pid in obj_map:
        smr = obj_map[smr_pid].read_typetree()
        go_pid = smr["m_GameObject"]["m_PathID"]
        go = obj_map[go_pid].read_typetree()
        print(f"\n{name} GO (PID {go_pid}):")
        print(f"  Name: {go.get('m_Name')}, Active: {go.get('m_IsActive')}")
        print(f"  Components: {go.get('m_Component')}")
        for comp in go.get('m_Component', []):
            c_pid = comp['component']['m_PathID']
            c_obj = obj_map.get(c_pid)
            if c_obj:
                c_tt = c_obj.read_typetree()
                if c_obj.type.name == "Transform":
                    print(f"  Transform {c_pid}: pos={c_tt.get('m_LocalPosition')}, rot={c_tt.get('m_LocalRotation')}, scale={c_tt.get('m_LocalScale')}, parent={c_tt.get('m_Father')}")
                elif c_obj.type.name == "SkinnedMeshRenderer":
                    print(f"  SMR {c_pid}: enabled={c_tt.get('m_Enabled')}, rootBone={c_tt.get('m_RootBone')}, bones={c_tt.get('m_Bones')}")

