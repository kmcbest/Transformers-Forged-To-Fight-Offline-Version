import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path

# Inspect blitzwing_tank.fbx.meta
tank_meta = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Blitzwing\blitzwing_tank.fbx.meta")
if tank_meta.exists():
    print("Tank FBX meta lines:")
    for line in tank_meta.read_text(encoding="utf-8").splitlines()[:30]:
        print(" ", line)

jet_meta = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Blitzwing\blitzwing_jet.fbx.meta")
if jet_meta.exists():
    print("\nJet FBX meta lines:")
    for line in jet_meta.read_text(encoding="utf-8").splitlines()[:30]:
        print(" ", line)
