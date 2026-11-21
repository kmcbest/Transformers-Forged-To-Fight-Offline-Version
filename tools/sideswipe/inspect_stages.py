import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
DONORS_DIR = ROOT / "extracted_apk" / "assets" / "assetpack"

# 1. Inspect Drift VictoryStagePrefab
env_drift = UnityPy.load(str(DONORS_DIR / "drift_cin_aoe_odr" / "drift_cin_aoe.assetbundle"))
sf_d = list(env_drift.assets)[0]
print(f"Drift Externals: {[(i+1, e.path) for i, e in enumerate(sf_d.externals)]}")
for o in env_drift.objects:
    if o.type.name == "MonoBehaviour":
        tt = o.read_typetree()
        if "VictoryStagePrefab" in tt:
            print("Drift PlayerReferences:")
            print("  VictoryStagePrefab:", tt.get("VictoryStagePrefab"))
            print("  SpecialStagePrefab:", tt.get("SpecialStagePrefab"))

# 2. Inspect Optimus Prime SpecialStagePrefab
env_op = UnityPy.load(str(DONORS_DIR / "optimusprime_cin_tf_odr" / "optimusprime_cin_tf.assetbundle"))
sf_op = list(env_op.assets)[0]
print(f"\nOptimus Externals: {[(i+1, e.path) for i, e in enumerate(sf_op.externals)]}")
for o in env_op.objects:
    if o.type.name == "MonoBehaviour":
        tt = o.read_typetree()
        if "SpecialStagePrefab" in tt:
            print("Optimus PlayerReferences:")
            print("  VictoryStagePrefab:", tt.get("VictoryStagePrefab"))
            print("  SpecialStagePrefab:", tt.get("SpecialStagePrefab"))

sp_pid = 3256447252977910551
sp_obj = [o for o in env_op.objects if o.path_id == sp_pid]
if sp_obj:
    print(f"\nOptimus SpecialStagePrefab ({sp_pid}): Type={sp_obj[0].type.name}")
    tt = sp_obj[0].read_typetree()
    print(f"  Name={tt.get('m_Name')}")

# 3. Inspect Barricade / Sideswipe Victory & Special Stage Prefabs
env_ss = UnityPy.load(str(ROOT / "assets_redeco" / "sideswipe_cin_rotf.assetbundle"))
sf_ss = list(env_ss.assets)[0]
print(f"\nSideswipe Externals: {[(i+1, e.path) for i, e in enumerate(sf_ss.externals)]}")
for o in env_ss.objects:
    if o.type.name == "MonoBehaviour":
        tt = o.read_typetree()
        if "SpecialStagePrefab" in tt:
            print("Sideswipe PlayerReferences:")
            print("  VictoryStagePrefab:", tt.get("VictoryStagePrefab"))
            print("  SpecialStagePrefab:", tt.get("SpecialStagePrefab"))
