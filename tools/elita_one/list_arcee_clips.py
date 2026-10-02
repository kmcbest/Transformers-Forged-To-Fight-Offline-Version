import sys
from pathlib import Path
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parent.parent.parent
BUNDLE = ROOT / "extracted_apk" / "assets" / "assetpack" / "arcee_gs_deluxe2014_odr" / "arcee_gs_deluxe2014.assetbundle"
env = UnityPy.load(str(BUNDLE))

print(f"=== AnimationClips in {BUNDLE.name} ===")
for obj in env.objects:
    if obj.type.name == "AnimationClip":
        tree = obj.read_typetree()
        print(f"  Clip: '{tree.get('m_Name')}' (PathID {obj.path_id})")
