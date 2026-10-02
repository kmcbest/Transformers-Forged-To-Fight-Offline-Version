import json
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
anim_path = ROOT / "tools" / "elita_one" / "arcee_attackLight_01.json"

with open(anim_path, "r", encoding="utf-8") as f:
    anim = json.load(f)

print("Clip:", anim.get("clipName"))
print("Frames count:", len(anim.get("frames", [])))
print("Sample rate:", anim.get("sampleRate"))
print("Length:", anim.get("length"))

first_frame = anim["frames"][0]
print(f"Bones in frame 0: {len(first_frame['bones'])}")
bone_map = {b["name"]: b for b in first_frame["bones"]}
for name in ["Hips", "Spine", "Head", "LeftArm", "LeftForeArm", "LeftHand", "RightArm", "RightForeArm", "RightHand"]:
    if name in bone_map:
        b = bone_map[name]
        print(f"  {name}: pos=({b['px']:.3f}, {b['py']:.3f}, {b['pz']:.3f}) rot=({b['rw']:.3f}, {b['rx']:.3f}, {b['ry']:.3f}, {b['rz']:.3f})")
