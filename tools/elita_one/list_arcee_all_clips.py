import UnityPy
from pathlib import Path

# Search for arcee bundle
candidates = list(Path(".").glob("**/arcee_gs_deluxe2014.assetbundle"))
for c in candidates:
    print("Found bundle:", c)
    env = UnityPy.load(str(c))
    clips = [obj.read().m_Name for obj in env.objects if obj.type.name == "AnimationClip"]
    print(f"Total AnimationClips: {len(clips)}")
    for cl in sorted(clips):
        print("  -", cl)
    break
