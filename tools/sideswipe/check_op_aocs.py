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
    if o.type.name == "AnimatorOverrideController":
        tt = o.read_typetree()
        print(f"\nAOC PID={pid}, name={tt.get('m_Name')}:")
        for cl in tt.get("m_Clips", []):
            over = cl.get("m_OverrideClip", {})
            if over.get("m_PathID") in (-8797122268252923436, -885727052547764263, -341215899653024):
                print(f"  Slot orig={cl.get('m_OriginalClip',{}).get('m_PathID')} -> over={over}")

for pid, o in sf_op.objects.items():
    if o.type.name == "MonoBehaviour":
        tt = o.read_typetree()
        if "_overrideControllerList" in tt:
            print(f"\nMatineeAOC PID={pid}:")
            for item in tt.get("_overrideControllerList", []):
                cname = item.get("OverrideClipName", "")
                if "sword" in cname.lower() or "special_03" in cname.lower():
                    print(f"  sh={item.get('StateHash')}: {cname}")
