import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

ROOT = Path(r"E:\Agent\TFTF-blender")
env_op = UnityPy.load(str(ROOT / "extracted_apk" / "assets" / "assetpack" / "optimusprime_cin_tf_odr" / "optimusprime_cin_tf.assetbundle"))
sf_op = list(env_op.assets)[0]

for pid, o in sf_op.objects.items():
    if o.type.name == "MonoBehaviour":
        tt = o.read_typetree()
        if "_events" in tt:
            print(f"CharacterAudio PID={pid}:")
            for e in tt.get("_events", []):
                gen = e.get("_genEvent", "")
                over = e.get("_override", "")
                if any(k in gen.lower() or k in over.lower() for k in ["special_3", "sp3", "special_03", "heavy", "victory"]):
                    print(f"  {gen} -> {over}")
            print(f"  _specialCharacterAudio count: {len(tt.get('_specialCharacterAudio', []))}")
            for sa in tt.get("_specialCharacterAudio", []):
                print(f"    sa: {sa}")
