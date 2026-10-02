import json
import numpy as np

bindposes_raw = json.loads(open("tools/elita_one/arcee_extracted/arcee_bindposes.json").read())
bone_names = json.loads(open("tools/elita_one/arcee_63_bones.json").read())

print("Analyzing Arcee's authoritative bindposes:")
for i, name in enumerate(bone_names):
    bp = bindposes_raw[i]
    M_inv = np.array([
        [bp["e00"], bp["e01"], bp["e02"], bp["e03"]],
        [bp["e10"], bp["e11"], bp["e12"], bp["e13"]],
        [bp["e20"], bp["e21"], bp["e22"], bp["e23"]],
        [bp["e30"], bp["e31"], bp["e32"], bp["e33"]],
    ])
    M_bone = np.linalg.inv(M_inv)
    pos = M_bone[:3, 3]
    if name in ["Hips", "Spine", "Spine1", "LeftArm", "RightArm", "LeftForeArm", "RightForeArm", "LeftUpLeg", "RightUpLeg", "LeftLeg", "RightLeg"]:
        print(f"Bone {name:15s} Rest Pos: X={pos[0]:7.3f}, Y={pos[1]:7.3f}, Z={pos[2]:7.3f}")
        # Let's inspect the rotation / direction vectors (X, Y, Z axes of the bone)
        axis_x = M_bone[:3, 0]
        axis_y = M_bone[:3, 1]
        axis_z = M_bone[:3, 2]
        print(f"   Axis X (right):   [{axis_x[0]:6.3f}, {axis_x[1]:6.3f}, {axis_x[2]:6.3f}]")
        print(f"   Axis Y (up):      [{axis_y[0]:6.3f}, {axis_y[1]:6.3f}, {axis_y[2]:6.3f}]")
        print(f"   Axis Z (forward): [{axis_z[0]:6.3f}, {axis_z[1]:6.3f}, {axis_z[2]:6.3f}]")
