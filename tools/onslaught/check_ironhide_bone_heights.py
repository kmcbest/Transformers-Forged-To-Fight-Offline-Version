import json

with open(r"E:\Agent\TFTF-blender\tools\demolishor\ironhide_80_bones.json", "r", encoding="utf-8") as f:
    data = json.load(f)

bones = data["bones"]

for bname in ["Head", "Neck", "Spine1", "Hips", "LeftUpLeg", "LeftLeg", "LeftFoot", "LeftHand", "RightHand"]:
    if bname in bones:
        mat = bones[bname]["matrix"]
        # In a 4x4 row-major matrix: trans is mat[0][3], mat[1][3], mat[2][3] or column
        # Let's inspect the matrix format
        tx, ty, tz = mat[0][3], mat[1][3], mat[2][3]
        print(f"Bone {bname:15s}: pos = ({tx:.3f}, {ty:.3f}, {tz:.3f})")
