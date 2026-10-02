import UnityPy

bundles = [
    r"E:\Agent\TFTF\assets_netflix\character_anim_procedural.assetbundle",
    r"E:\Agent\TFTF\assets_netflix\moves.assetbundle"
]

for bpath in bundles:
    print("="*50)
    print("Scanning:", bpath)
    env = UnityPy.load(bpath)
    clips = []
    for obj in env.objects:
        if obj.type.name == "AnimationClip":
            data = obj.read()
            name = data.m_Name.lower()
            if any(k in name for k in ["arcee", "scout", "female", "windblade", "chromia"]):
                clips.append(data.m_Name)
    print(f"Total matching clips: {len(clips)}")
    for c in clips[:20]:
        print(" ", c)
