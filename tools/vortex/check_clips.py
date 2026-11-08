import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

g_bundle_path = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\grindor_cin_rotf_odr\grindor_cin_rotf.assetbundle"
moves_bundle_path = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\characters\moves.assetbundle"

print("--- Checking grindor bundle ---")
env_g = UnityPy.load(g_bundle_path)
for obj in env_g.objects:
    if obj.type.name == "AnimationClip":
        data = obj.read()
        name = getattr(data, 'name', None) or getattr(data, 'm_Name', '')
        print(f"Grindor clip: {name}")

print("\n--- Checking moves bundle for grindor / brute clips ---")
env_m = UnityPy.load(moves_bundle_path)
grindor_clips = []
for obj in env_m.objects:
    if obj.type.name == "AnimationClip":
        data = obj.read()
        name = getattr(data, 'name', None) or getattr(data, 'm_Name', '')
        if "grindor" in name.lower() or "brute" in name.lower():
            grindor_clips.append(name)

print(f"Total matching clips in moves.assetbundle: {len(grindor_clips)}")
for c in grindor_clips[:20]:
    print(" ", c)
