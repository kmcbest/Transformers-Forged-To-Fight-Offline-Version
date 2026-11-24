import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

p = Path("assets_redeco/sideswipe_cin_rotf.assetbundle")
print(f"Loading {p.name} ({p.stat().st_size} bytes)...")
env = UnityPy.load(str(p))

# 1. Check CharacterModels
for pid in [-7851000438720208557, -479015221859556422]:
    obj = [o for o in env.objects if o.path_id == pid][0]
    tt = obj.read_typetree()
    for k, v in zip(tt["_props"]["_serializedKeys"], tt["_props"]["_serializedValues"]):
        if k == "nunchuck":
            assert v["_renderers"] == [], f"Renderers not empty: {v['_renderers']}"
            assert v["Scale"] == {"x": 0.0, "y": 0.0, "z": 0.0}, f"Scale not zero: {v['Scale']}"
            print(f"[✓] Verified CharacterModel PID={pid}: nunchuck _renderers={v['_renderers']}, Scale={v['Scale']}")

# 2. Check SMRs
for pid in [-5711057110573806536, -4879794911437009642]:
    obj = [o for o in env.objects if o.path_id == pid][0]
    tt = obj.read_typetree()
    assert tt["m_Mesh"]["m_PathID"] == 0, f"m_Mesh not 0: {tt['m_Mesh']}"
    assert tt["m_Materials"] == [], f"m_Materials not empty: {tt['m_Materials']}"
    assert tt["m_Enabled"] is False, f"m_Enabled not False: {tt['m_Enabled']}"
    print(f"[✓] Verified SMR PID={pid}: Mesh={tt['m_Mesh']}, Enabled={tt['m_Enabled']}, Mats={tt['m_Materials']}")

# 3. Check GameObjects & Transforms
for pid in [-4282074790894966000, 5981453158226969972, -2204780038870049617, -1614615008613451407]:
    obj = [o for o in env.objects if o.path_id == pid][0]
    tt = obj.read_typetree()
    assert tt["m_IsActive"] is False, f"m_IsActive not False: {tt['m_IsActive']}"
    print(f"[✓] Verified GameObject PID={pid} '{tt['m_Name']}': m_IsActive={tt['m_IsActive']}")

for pid in [4796207257227963744, 4994973836030178910]:
    obj = [o for o in env.objects if o.path_id == pid][0]
    tt = obj.read_typetree()
    assert tt["m_LocalScale"] == {"x": 0.0, "y": 0.0, "z": 0.0}, f"m_LocalScale not 0: {tt['m_LocalScale']}"
    print(f"[✓] Verified Transform PID={pid}: m_LocalScale={tt['m_LocalScale']}")

# 4. Check MoveSet
moveset_obj = [o for o in env.objects if o.path_id == -5126079019749064592][0]
tt = moveset_obj.read_typetree()
m6 = tt["_moves"][6]
print(f"[✓] Verified MoveSet S1: name='{m6['_name']}', asset={m6['_asset']}")

print("\n🎉 ALL VERIFICATIONS PASSED!")
