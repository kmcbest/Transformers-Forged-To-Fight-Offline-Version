import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
import numpy as np

BUNDLE_PATH = r"assets_redeco/brawl_gs.assetbundle"
print(f"[*] Loading {BUNDLE_PATH}...")
env = UnityPy.load(BUNDLE_PATH)

obj_map = {obj.path_id: obj for obj in env.objects}

# 1. Partition Robot Mesh: cha_brawl_gs_00 (PID 8927022796776742380)
mesh_obj = obj_map[8927022796776742380]
m = mesh_obj.read()
m_tt = mesh_obj.read_typetree()

ib_bytes = bytes(m.m_IndexBuffer)
ib = np.frombuffer(ib_bytes, dtype=np.uint16).reshape(-1, 3)
total_tris = len(ib)
print(f"Total triangles in cha_brawl_gs_00: {total_tris}")

eye_tri_indices = set([290, 291, 292, 293, 318, 320, 321, 326, 329, 330, 331, 332, 333, 339, 343, 390, 392, 394])
print(f"Eye triangles count: {len(eye_tri_indices)}")

body_tris = [ib[i] for i in range(total_tris) if i not in eye_tri_indices]
eye_tris = [ib[i] for i in range(total_tris) if i in eye_tri_indices]

body_ib = np.array(body_tris, dtype=np.uint16).flatten()
eye_ib = np.array(eye_tris, dtype=np.uint16).flatten()
new_ib = np.concatenate([body_ib, eye_ib])

body_count = len(body_ib)
eye_count = len(eye_ib)
print(f"SubMesh 0 (Body): {body_count} indices ({body_count//3} tris)")
print(f"SubMesh 1 (Eyes): {eye_count} indices ({eye_count//3} tris)")

new_ib_bytes = new_ib.tobytes()
m_tt["m_IndexBuffer"] = list(new_ib_bytes)

orig_sm0 = m_tt["m_SubMeshes"][0]
sm0 = dict(orig_sm0)
sm0["firstByte"] = 0
sm0["indexCount"] = body_count

sm1 = dict(orig_sm0)
sm1["firstByte"] = body_count * 2
sm1["indexCount"] = eye_count

m_tt["m_SubMeshes"] = [sm0, sm1]
mesh_obj.save_typetree(m_tt)
print("[✓] Partitioned cha_brawl_gs_00 into 2 SubMeshes.")

# 2. Update Robot SMRs: -1713043385139994820 and 6657504797783083318
MAT_ROBOT_PID = 2758279787216392959
MAT_EYES_PID = -7854615674899395621
for smr_pid in [-1713043385139994820, 6657504797783083318]:
    smr_obj = obj_map[smr_pid]
    smr_tt = smr_obj.read_typetree()
    smr_tt["m_Materials"] = [
        {"m_FileID": 0, "m_PathID": MAT_ROBOT_PID},
        {"m_FileID": 0, "m_PathID": MAT_EYES_PID},
    ]
    smr_obj.save_typetree(smr_tt)
print(f"[✓] Updated Robot SMRs to reference [MAT_ROBOT_PID, MAT_EYES_PID].")

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

# 3. Update Robot Material: 2758279787216392959 (Neon Purple!)
mat_robot_obj = obj_map[MAT_ROBOT_PID]
mat_robot_tt = mat_robot_obj.read_typetree()
update_material_properties(
    mat_robot_tt,
    colors={"_emissive_intensity_col": {"r": 0.75, "g": 0.10, "b": 1.0, "a": 0.0}},
    floats={"_emissive_overbright_range": 24.0, "_emissive_range": 1.0}
)
mat_robot_obj.save_typetree(mat_robot_tt)
print("[✓] Robot Material tuned to Neon Purple (_emissive_intensity_col=[0.75, 0.10, 1.0]).")

# 4. Update Eyes Material: -7854615674899395621 (Pure Yellow Optics!)
mat_eyes_obj = obj_map[MAT_EYES_PID]
mat_eyes_tt = mat_eyes_obj.read_typetree()
update_material_properties(
    mat_eyes_tt,
    colors={
        "_emissive_intensity_col": {"r": 1.0, "g": 0.85, "b": 0.10, "a": 0.0},
        "_Color": {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0},
        "_base_col": {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0},
    },
    floats={"_emissive_overbright_range": 24.0, "_emissive_range": 1.0},
    texs={
        "_base_tex": 7575930771601290721,
        "_normal_tex": 42717178677652158,
        "_pbr_composite_tex": -8652859075577142890,
    }
)
mat_eyes_obj.save_typetree(mat_eyes_tt)
print("[✓] Eyes Material tuned to Pure Yellow Optics (_emissive_intensity_col=[1.0, 0.85, 0.10]).")

# 5. Update Tank Material: -8143696719442631496 (Neon Purple!)
mat_tank_obj = obj_map[-8143696719442631496]
mat_tank_tt = mat_tank_obj.read_typetree()
update_material_properties(
    mat_tank_tt,
    colors={"_emissive_intensity_col": {"r": 0.75, "g": 0.10, "b": 1.0, "a": 0.0}},
    floats={"_emissive_overbright_range": 24.0, "_emissive_range": 1.0}
)
mat_tank_obj.save_typetree(mat_tank_tt)
print("[✓] Tank Material tuned to Neon Purple (_emissive_intensity_col=[0.75, 0.10, 1.0]).")

# 6. Save assetbundle
out_bytes = env.file.save(packer="lz4")
with open(BUNDLE_PATH, "wb") as f:
    f.write(out_bytes)
print(f"[✓] Successfully saved updated {BUNDLE_PATH} with LZ4 compression! Size: {len(out_bytes):,} bytes.")
