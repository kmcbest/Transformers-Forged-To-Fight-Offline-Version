import json

with open(r"E:\Agent\TFTF-blender\tools\elita_one\arcee_unity_verts_skin.json", "r") as f:
    skin = json.load(f)

v = skin["verts"][1114]
print(f"Vert 1114: pos=({v['x']}, {v['y']}, {v['z']}), bones={v['b']}, weights={v['w']}")

# Check vert 0, 1, 2 vs OBJ vert 0, 1, 2
with open(r"E:\Agent\TFTF-blender\tools\elita_one\arcee_extracted\arcee_robot_reference.obj", "r") as f:
    obj_lines = [l.strip() for l in f if l.startswith("v ")]

print(f"Total OBJ vertices: {len(obj_lines)}")
print("OBJ vert 0:", obj_lines[0])
print("OBJ vert 1114:", obj_lines[1114])
