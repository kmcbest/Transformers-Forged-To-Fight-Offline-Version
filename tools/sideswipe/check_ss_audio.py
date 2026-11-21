import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

ROOT = Path(r"E:\Agent\TFTF-blender")
env_ss = UnityPy.load(str(ROOT / "assets_redeco" / "sideswipe_cin_rotf.assetbundle"))
sf_ss = list(env_ss.assets)[0]

for pid, o in sf_ss.objects.items():
    if o.type.name == "MonoBehaviour":
        tt = o.read_typetree()
        if "_events" in tt:
            print(f"CharacterAudio PID={pid}:")
            for e in tt.get("_events", []):
                gen = e.get("_genEvent", "")
                over = e.get("_override", "")
                if any(k in gen.lower() or k in over.lower() for k in ["special", "heavy", "victory"]):
                    print(f"  {gen} -> {over}")
            print(f"  _specialCharacterAudio count: {len(tt.get('_specialCharacterAudio', []))}")
            for sa in tt.get("_specialCharacterAudio", []):
                print(f"    sa: {sa}")
