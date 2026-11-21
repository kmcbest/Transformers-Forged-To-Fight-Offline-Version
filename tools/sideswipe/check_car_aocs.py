import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

ROOT = Path(r"E:\Agent\TFTF-blender")

def inspect_car_aoc(bundle_p, name):
    env = UnityPy.load(str(bundle_p))
    sf = list(env.assets)[0]
    for pid, o in sf.objects.items():
        if o.type.name == "AnimatorOverrideController":
            tt = o.read_typetree()
            if "car" in tt.get("m_Name", "").lower() or "truck" in tt.get("m_Name", "").lower():
                print(f"\n{name} Car AOC PID={pid}, name={tt.get('m_Name')}:")
                clips = tt.get("m_Clips", [])
                print(f"  Total clips: {len(clips)}")
                for idx, cl in enumerate(clips):
                    orig = cl.get("m_OriginalClip", {}).get("m_PathID")
                    over = cl.get("m_OverrideClip", {})
                    # Look for SP3 or transformed clips
                    if idx in (0, 1, 2, 3, 4, 5, 60, 61, 62, 63, 64, 65) or any(k in str(over) for k in ["Special", "special", "341215899653024"]):
                        print(f"    Slot {idx:02d} (orig {orig}): over={over}")

inspect_car_aoc(ROOT / "extracted_apk" / "assets" / "assetpack" / "optimusprime_cin_tf_odr" / "optimusprime_cin_tf.assetbundle", "Optimus")
inspect_car_aoc(ROOT / "assets_redeco" / "sideswipe_cin_rotf.assetbundle", "Sideswipe")
