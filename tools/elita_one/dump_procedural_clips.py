import UnityPy

bpath = r"E:\Agent\TFTF\assets_netflix\character_anim_procedural.assetbundle"
env = UnityPy.load(bpath)
clips = []
for obj in env.objects:
    if obj.type.name == "AnimationClip":
        data = obj.read()
        clips.append(data.m_Name)

print(f"Total clips in character_anim_procedural: {len(clips)}")
with open(r"E:\Agent\TFTF-blender\tools\elita_one\all_procedural_clips.txt", "w", encoding="utf-8") as f:
    for c in sorted(clips):
        f.write(c + "\n")
print("Saved to tools/elita_one/all_procedural_clips.txt")
