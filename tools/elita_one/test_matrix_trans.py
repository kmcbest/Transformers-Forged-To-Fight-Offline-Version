import json
import mathutils

REST_JSON = r"E:\Agent\TFTF-blender\tools\elita_one\arcee_unity_rest_matrices.json"
with open(REST_JSON, "r") as f:
    rest_data = json.load(f)

C = mathutils.Matrix((
    (1, 0, 0, 0),
    (0, 0, 1, 0),
    (0, 1, 0, 0),
    (0, 0, 0, 1)
))

for b in rest_data["bones"]:
    if b["name"] in ["Reference", "Hips", "Spine"]:
        m_raw = b["m"]
        M_u = mathutils.Matrix((m_raw[0:4], m_raw[4:8], m_raw[8:12], m_raw[12:16]))
        M_b = C @ M_u @ C
        print(f"{b['name']}: M_u trans={M_u.translation}, M_b trans={M_b.translation}")
