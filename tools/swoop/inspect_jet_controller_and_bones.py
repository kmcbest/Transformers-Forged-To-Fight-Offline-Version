import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import UnityPy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
TFTF = Path(r"E:\Agent\TFTF")

SWOOP = ROOT / "assets_redeco/swoop_gs_deluxe2008.assetbundle"
e = UnityPy.load(str(SWOOP))
omap = {o.path_id: o for o in e.objects}

ac = omap[341294063036995988].read_typetree()
print("Jet Base AnimatorController:", ac["m_Name"])
print("m_TOS:", list(ac.get("m_TOS", [])))
ctrl = ac.get("m_Controller", {})
for layer in ctrl.get("m_StateMachineArray", []):
    for st in layer.get("m_StateConstantArray", []):
        print("  State:", st.get("m_NameID"), st.get("m_FullPathID"), st.get("m_Speed"), st.get("m_BlendTreeConstantIndexArray"))

# Check Skywarp vs Ramjet HeavyAttack move & fight AOC & jet AOC
SKYWARP = TFTF / "extracted_apk/assets/assetpack/skywarp_gs_leader2015_odr/skywarp_gs_leader2015.assetbundle"
es = UnityPy.load(str(SKYWARP))
for o in es.objects:
    if o.type.name == "AnimatorController":
        st = o.read_typetree()
        print("Skywarp AnimatorController:", st["m_Name"], "PID=", o.path_id)

# Also inspect Swoop's SMR 4450385079657545705 m_Bones vs cha_swoop_gs_01 vertex weights!
print("\n=== Check cha_swoop_gs_01 SMR 4450385079657545705 ===")
smr = omap[4450385079657545705].read_typetree()
print("m_Bones count:", len(smr["m_Bones"]), "m_RootBone:", smr["m_RootBone"])
for idx, b in enumerate(smr["m_Bones"]):
    tr = omap[b["m_PathID"]].read_typetree()
    go = omap[tr["m_GameObject"]["m_PathID"]].read_typetree()
    print(f"  bone[{idx:2d}]: {go['m_Name']} active={go['m_IsActive']} pos={tr['m_LocalPosition']} sca={tr['m_LocalScale']}")
