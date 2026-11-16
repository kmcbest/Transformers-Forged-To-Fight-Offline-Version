import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

anim_bundle = r"E:\Agent\TFTF-blender\assets_netflix\character_anim_procedural.assetbundle"
env = UnityPy.load(anim_bundle)

clip_names = {}
for obj in env.objects:
    if obj.type.name == "AnimationClip":
        tt = obj.read_typetree()
        clip_names[obj.path_id] = tt.get("m_Name")

# Print clips matching attack or special
print(f"Total AnimationClips in procedural bundle: {len(clip_names)}")
for pid, name in clip_names.items():
    if "attack" in name.lower() or "special" in name.lower() or "medium" in name.lower():
        print(f"PID={pid} -> {name}")
