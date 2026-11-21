import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

ROOT = Path(r"E:\Agent\TFTF-blender")

def find_clips(bundle_path):
    env = UnityPy.load(str(bundle_path))
    sf = list(env.assets)[0]
    clips = []
    for pid, o in sf.objects.items():
        if o.type.name == "AnimationClip":
            tt = o.read_typetree()
            name = tt.get("m_Name", "")
            if "optimus_prime_attackspecial_03" in name.lower():
                clips.append((pid, name))
    return clips

# Check in Optimus bundle
op_p = ROOT / "extracted_apk" / "assets" / "assetpack" / "optimusprime_cin_tf_odr" / "optimusprime_cin_tf.assetbundle"
print("In Optimus bundle:", find_clips(op_p))

# Check in character_anim_procedural
anim_p = ROOT / "extracted_apk" / "assets" / "assetpack" / "characters_procedural_odr" / "character_anim_procedural.assetbundle"
print("In character_anim_procedural:", find_clips(anim_p))
