import os
import UnityPy

def find_clips():
    base_dir = r"E:\Agent\TFTF-blender\extracted_apk\assets"
    print("Scanning extracted_apk for arcee clips...")
    for root, dirs, files in os.walk(base_dir):
        for f in files:
            if f.endswith(".assetbundle"):
                full_path = os.path.join(root, f)
                try:
                    env = UnityPy.load(full_path)
                    clips = []
                    for obj in env.objects:
                        if obj.type.name == "AnimationClip":
                            data = obj.read()
                            if "arcee" in data.name.lower() or "female" in data.name.lower():
                                clips.append(data.name)
                    if clips:
                        print(f"Found in {full_path}: {len(clips)} clips")
                        for c in clips[:10]:
                            print(f"  - {c}")
                        if len(clips) > 10:
                            print(f"  ... and {len(clips)-10} more")
                except Exception as e:
                    pass

if __name__ == "__main__":
    find_clips()
