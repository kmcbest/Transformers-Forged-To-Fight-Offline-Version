import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
import numpy as np
from PIL import Image

BUNDLE_PATH = r"assets_redeco/vortex_gs.assetbundle"
print(f"[*] Loading {BUNDLE_PATH}...")
env = UnityPy.load(BUNDLE_PATH)

obj_map = {obj.path_id: obj for obj in env.objects}

def update_material_properties(mat_tt, colors=None, floats=None, texs=None):
    if colors:
        new_cols = []
        for c in mat_tt["m_SavedProperties"]["m_Colors"]:
            prop_name = c[0]
            if prop_name in colors:
                new_cols.append((prop_name, colors[prop_name]))
            else:
                new_cols.append(c)
        mat_tt["m_SavedProperties"]["m_Colors"] = new_cols
        
    if floats:
        new_floats = []
        for f in mat_tt["m_SavedProperties"]["m_Floats"]:
            prop_name = f[0]
            if prop_name in floats:
                new_floats.append((prop_name, floats[prop_name]))
            else:
                new_floats.append(f)
        mat_tt["m_SavedProperties"]["m_Floats"] = new_floats
        
    if texs:
        new_texs = []
        for te in mat_tt["m_SavedProperties"]["m_TexEnvs"]:
            prop_name = te[0]
            if prop_name in texs:
                new_te_dict = dict(te[1])
                new_te_dict["m_Texture"] = {"m_FileID": 0, "m_PathID": texs[prop_name]}
                new_texs.append((prop_name, new_te_dict))
            else:
                new_texs.append(te)
        mat_tt["m_SavedProperties"]["m_TexEnvs"] = new_texs

# 1. Update Helicopter Textures with clean DecepticonLogo
emblem_diff = Image.open(r"e:\Agent\TFTF-blender\tools\vortex\emblem_diff_512.png")
emblem_raoe = Image.open(r"e:\Agent\TFTF-blender\tools\vortex\emblem_raoe_512.png")

tex_wpns_a = obj_map[6239694728433603131].read()
tex_wpns_a.image = emblem_diff
tex_wpns_a.save()
print("[✓] Replaced cha_grindor_cin_rotf_wpns_a with clean 512x512 emblem diffuse.")

tex_wpns_raoe = obj_map[3025951477767776163].read()
tex_wpns_raoe.image = emblem_raoe
tex_wpns_raoe.save()
print("[✓] Replaced wpns_RAOE with clean 512x512 emblem RAOE (emissive=220).")

# 2. Update Helicopter Mesh: cha_grindor_cin_rotf_01 (PID -2766188856892899435)
vh_mesh_obj = obj_map[-2766188856892899435]
vh_m = vh_mesh_obj.read()
vh_m_tt = vh_mesh_obj.read_typetree()

vd = vh_m_tt["m_VertexData"]
vc = vd["m_VertexCount"]
raw_bytes = bytearray(vd["m_DataSize"])

# Stride 0 = 40 (pos 0..12, normal 12..24, tangent 24..40)
# Stride 1 = 8 (uv 0..8 at stream 1 offset = vc * 40)
pos_arr = np.ndarray((vc, 3), dtype=np.float32, buffer=raw_bytes, strides=(40, 4), offset=0)
uv_arr = np.ndarray((vc, 2), dtype=np.float32, buffer=raw_bytes, strides=(8, 4), offset=vc*40)

# Offset 8 emblem vertices along normal by +0.015m to completely prevent Z-fighting!
norm_right = np.array([0.8801, -0.0637, 0.4706], dtype=np.float32)
norm_right /= np.linalg.norm(norm_right)
norm_left = np.array([-0.8801, -0.0637, 0.4706], dtype=np.float32)
norm_left /= np.linalg.norm(norm_left)

for vi in [171, 172, 173, 174]:
    pos_arr[vi] += norm_right * 0.015
for vi in [175, 176, 177, 178]:
    pos_arr[vi] += norm_left * 0.015

# Remap emblem UVs to standard clean quad [0, 1]
# Right side:
# Top-Left: v173 (0.0, 1.0)
# Top-Right: v171 (1.0, 1.0)
# Bottom-Left: v172 (0.0, 0.0)
# Bottom-Right: v174 (1.0, 0.0)
uv_arr[173] = [0.0, 1.0]
uv_arr[171] = [1.0, 1.0]
uv_arr[172] = [0.0, 0.0]
uv_arr[174] = [1.0, 0.0]

# Left side:
# Top-Left: v178 (0.0, 1.0)
# Top-Right: v175 (1.0, 1.0)
# Bottom-Left: v176 (0.0, 0.0)
# Bottom-Right: v177 (1.0, 0.0)
uv_arr[178] = [0.0, 1.0]
uv_arr[175] = [1.0, 1.0]
uv_arr[176] = [0.0, 0.0]
uv_arr[177] = [1.0, 0.0]

vd["m_DataSize"] = bytes(raw_bytes)

# Partition Helicopter IndexBuffer: 4 emblem triangles (Tris 59, 60, 61, 62) -> SubMesh 1
ib_vh = np.frombuffer(bytes(vh_m.m_IndexBuffer), dtype=np.uint16).reshape(-1, 3)
total_vh_tris = len(ib_vh)
print(f"Total triangles in cha_grindor_cin_rotf_01: {total_vh_tris}")

emblem_vh_indices = set([59, 60, 61, 62])
body_vh_tris = [ib_vh[i] for i in range(total_vh_tris) if i not in emblem_vh_indices]
emblem_vh_tris = [ib_vh[i] for i in range(total_vh_tris) if i in emblem_vh_indices]

body_vh_ib = np.array(body_vh_tris, dtype=np.uint16).flatten()
emblem_vh_ib = np.array(emblem_vh_tris, dtype=np.uint16).flatten()
new_vh_ib = np.concatenate([body_vh_ib, emblem_vh_ib])

body_vh_count = len(body_vh_ib)
emblem_vh_count = len(emblem_vh_ib)
print(f"Helicopter SubMesh 0 (Body): {body_vh_count} indices ({body_vh_count//3} tris)")
print(f"Helicopter SubMesh 1 (Emblem): {emblem_vh_count} indices ({emblem_vh_count//3} tris)")

vh_m_tt["m_IndexBuffer"] = list(new_vh_ib.tobytes())
orig_vh_sm0 = vh_m_tt["m_SubMeshes"][0]
sm0_vh = dict(orig_vh_sm0)
sm0_vh["firstByte"] = 0
sm0_vh["indexCount"] = body_vh_count

sm1_vh = dict(orig_vh_sm0)
sm1_vh["firstByte"] = body_vh_count * 2
sm1_vh["indexCount"] = emblem_vh_count

vh_m_tt["m_SubMeshes"] = [sm0_vh, sm1_vh]
vh_mesh_obj.save_typetree(vh_m_tt)
print("[✓] Helicopter Mesh partitioned into SubMesh 0 (Body) and SubMesh 1 (Emblem).")

# 3. Update Helicopter Materials and SMRs
MAT_VEHICLE_PID = -3423934603996225370
MAT_EMBLEM_PID = -7619844944224089758

# Configure MAT_EMBLEM_PID
mat_emblem_obj = obj_map[MAT_EMBLEM_PID]
mat_emblem_tt = mat_emblem_obj.read_typetree()
update_material_properties(
    mat_emblem_tt,
    colors={
        "_emissive_intensity_col": {"r": 0.75, "g": 0.10, "b": 1.0, "a": 0.0},
        "_Color": {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0},
        "_base_col": {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0},
    },
    floats={"_emissive_overbright_range": 28.0, "_emissive_range": 1.0},
    texs={
        "_base_tex": 6239694728433603131,
        "_normal_tex": 4939845825144636112,
        "_pbr_composite_tex": 3025951477767776163,
    }
)
mat_emblem_obj.save_typetree(mat_emblem_tt)
print("[✓] Helicopter Emblem Material configured with DecepticonLogo and Neon Purple glow.")

# Configure MAT_VEHICLE_PID
mat_veh_obj = obj_map[MAT_VEHICLE_PID]
mat_veh_tt = mat_veh_obj.read_typetree()
update_material_properties(
    mat_veh_tt,
    colors={"_emissive_intensity_col": {"r": 0.75, "g": 0.10, "b": 1.0, "a": 0.0}},
    floats={"_emissive_overbright_range": 28.0, "_emissive_range": 1.0}
)
mat_veh_obj.save_typetree(mat_veh_tt)
print("[✓] Helicopter Body Material configured with Neon Purple glow.")

# Update Helicopter SMRs
for smr_pid in [-3058981427382277161, 6619623465709811202]:
    smr_obj = obj_map[smr_pid]
    smr_tt = smr_obj.read_typetree()
    smr_tt["m_Materials"] = [
        {"m_FileID": 0, "m_PathID": MAT_VEHICLE_PID},
        {"m_FileID": 0, "m_PathID": MAT_EMBLEM_PID},
    ]
    smr_obj.save_typetree(smr_tt)
print("[✓] Helicopter SMRs bound to [MAT_VEHICLE_PID, MAT_EMBLEM_PID].")

# 4. Partition Robot Mesh: cha_grindor_cin_rotf_00 (PID 5703189533076905359)
rob_mesh_obj = obj_map[5703189533076905359]
rob_m = rob_mesh_obj.read()
rob_m_tt = rob_mesh_obj.read_typetree()

ib_rob = np.frombuffer(bytes(rob_m.m_IndexBuffer), dtype=np.uint16).reshape(-1, 3)
total_rob_tris = len(ib_rob)
print(f"Total triangles in cha_grindor_cin_rotf_00: {total_rob_tris}")

eye_rob_indices = set([6074, 6084] + list(range(6098, 6108)))
print(f"Vortex Robot Eye triangles count: {len(eye_rob_indices)}")

body_rob_tris = [ib_rob[i] for i in range(total_rob_tris) if i not in eye_rob_indices]
eye_rob_tris = [ib_rob[i] for i in range(total_rob_tris) if i in eye_rob_indices]

body_rob_ib = np.array(body_rob_tris, dtype=np.uint16).flatten()
eye_rob_ib = np.array(eye_rob_tris, dtype=np.uint16).flatten()
new_rob_ib = np.concatenate([body_rob_ib, eye_rob_ib])

body_rob_count = len(body_rob_ib)
eye_rob_count = len(eye_rob_ib)
print(f"Robot SubMesh 0 (Body/Sword/Emblem): {body_rob_count} indices ({body_rob_count//3} tris)")
print(f"Robot SubMesh 1 (Eyes): {eye_rob_count} indices ({eye_rob_count//3} tris)")

rob_m_tt["m_IndexBuffer"] = list(new_rob_ib.tobytes())
orig_rob_sm0 = rob_m_tt["m_SubMeshes"][0]
sm0_rob = dict(orig_rob_sm0)
sm0_rob["firstByte"] = 0
sm0_rob["indexCount"] = body_rob_count

sm1_rob = dict(orig_rob_sm0)
sm1_rob["firstByte"] = body_rob_count * 2
sm1_rob["indexCount"] = eye_rob_count

rob_m_tt["m_SubMeshes"] = [sm0_rob, sm1_rob]
rob_mesh_obj.save_typetree(rob_m_tt)
print("[✓] Partitioned cha_grindor_cin_rotf_00 into SubMesh 0 and SubMesh 1.")

# 5. Update Robot Materials and SMRs
MAT_ROBOT_PID = 2433515842246304279
MAT_ROBOT_EYES_PID = -4921200029808501144

# Configure MAT_ROBOT_EYES_PID (Pure Yellow Optics!)
mat_rob_eyes_obj = obj_map[MAT_ROBOT_EYES_PID]
mat_rob_eyes_tt = mat_rob_eyes_obj.read_typetree()
update_material_properties(
    mat_rob_eyes_tt,
    colors={
        "_emissive_intensity_col": {"r": 1.0, "g": 0.85, "b": 0.10, "a": 0.0},
        "_Color": {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0},
        "_base_col": {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0},
    },
    floats={"_emissive_overbright_range": 28.0, "_emissive_range": 1.0},
    texs={
        "_base_tex": -527106191474585865,
        "_normal_tex": -3094932978529403771,
        "_pbr_composite_tex": -2574972184015167263,
    }
)
mat_rob_eyes_obj.save_typetree(mat_rob_eyes_tt)
print("[✓] Vortex Robot Eyes Material tuned to Pure Yellow Optics (_emissive_intensity_col=[1.0, 0.85, 0.10]).")

# Configure MAT_ROBOT_PID (Neon Purple for sword blade, chest stripes, chest emblem!)
mat_rob_obj = obj_map[MAT_ROBOT_PID]
mat_rob_tt = mat_rob_obj.read_typetree()
update_material_properties(
    mat_rob_tt,
    colors={"_emissive_intensity_col": {"r": 0.75, "g": 0.10, "b": 1.0, "a": 0.0}},
    floats={"_emissive_overbright_range": 28.0, "_emissive_range": 1.0}
)
mat_rob_obj.save_typetree(mat_rob_tt)
print("[✓] Vortex Robot Body Material tuned to Neon Purple (_emissive_intensity_col=[0.75, 0.10, 1.0]).")

# Update Robot SMRs
for smr_pid in [-3243551817942222242, -2776875793336503958]:
    smr_obj = obj_map[smr_pid]
    smr_tt = smr_obj.read_typetree()
    smr_tt["m_Materials"] = [
        {"m_FileID": 0, "m_PathID": MAT_ROBOT_PID},
        {"m_FileID": 0, "m_PathID": MAT_ROBOT_EYES_PID},
    ]
    smr_obj.save_typetree(smr_tt)
print("[✓] Vortex Robot SMRs bound to [MAT_ROBOT_PID, MAT_ROBOT_EYES_PID].")

# 6. Save assetbundle
out_bytes = env.file.save(packer="lz4")
with open(BUNDLE_PATH, "wb") as f:
    f.write(out_bytes)
print(f"[✓] Successfully saved updated {BUNDLE_PATH} with LZ4 compression! Size: {len(out_bytes):,} bytes.")
