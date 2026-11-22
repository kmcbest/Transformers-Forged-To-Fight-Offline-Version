import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
import numpy as np
from PIL import Image

BUNDLE_PATH = r"assets_redeco/onslaught_gs.assetbundle"
print(f"[*] Loading {BUNDLE_PATH}...")
env = UnityPy.load(BUNDLE_PATH)

obj_map = {obj.path_id: obj for obj in env.objects}

# 1. Update main_tform_misc_RAOE (PID 7395759426203415672)
raoe_obj = obj_map[7395759426203415672]
diff_obj = obj_map[-5161093122092615707]

diff_img = diff_obj.read().image.convert("RGBA")
diff_np = np.array(diff_img)
raoe_img = raoe_obj.read().image.convert("RGB")
raoe_np = np.array(raoe_img)

r, g, b = diff_np[:, :, 0], diff_np[:, :, 1], diff_np[:, :, 2]
is_purple = (r > 70) & (b > 110) & (g < 80)
chest_mask = np.zeros_like(is_purple)
chest_mask[50:500, 1600:2000] = True
target_emblem = is_purple & chest_mask
painted_pixels = np.count_nonzero(target_emblem)
print(f"[✓] Onslaught robot chest emblem pixels to light up: {painted_pixels}")
raoe_np[target_emblem, 2] = 220
new_raoe_img = Image.fromarray(raoe_np)
raoe_data = raoe_obj.read()
raoe_data.image = new_raoe_img
raoe_data.save()
print("[✓] Saved updated main_tform_misc_RAOE into bundle.")

# 2. Update wpns_RAOE (PID 4293333004908690441)
wpns_raoe_obj = obj_map[4293333004908690441]
vh_diff_obj = obj_map[-600257873597148843]
vh_diff_img = vh_diff_obj.read().image.convert("RGBA")
vh_diff_np = np.array(vh_diff_img)
wpns_raoe_img = wpns_raoe_obj.read().image.convert("RGB")
wpns_raoe_np = np.array(wpns_raoe_img)

vr, vg, vb = vh_diff_np[:, :, 0], vh_diff_np[:, :, 1], vh_diff_np[:, :, 2]
v_purple = (vr > 70) & (vb > 110) & (vg < 80)
vh_mask = np.zeros_like(v_purple)
vh_mask[1130:1950, 1180:1890] = True
v_target = v_purple & vh_mask
v_painted = np.count_nonzero(v_target)
print(f"[✓] Onslaught vehicle grille emblem pixels to light up: {v_painted}")
wpns_raoe_np[v_target, 2] = 220
new_wpns_raoe_img = Image.fromarray(wpns_raoe_np)
wpns_raoe_data = wpns_raoe_obj.read()
wpns_raoe_data.image = new_wpns_raoe_img
wpns_raoe_data.save()
print("[✓] Saved updated wpns_RAOE into bundle.")

# 3. Partition Robot Mesh: cha_ironhide_cin_rotf_00 (PID 243592621990493584)
mesh_obj = obj_map[243592621990493584]
m = mesh_obj.read()
m_tt = mesh_obj.read_typetree()

ib_bytes = bytes(m.m_IndexBuffer)
ib = np.frombuffer(ib_bytes, dtype=np.uint16).reshape(-1, 3)
total_tris = len(ib)
print(f"Total triangles in cha_ironhide_cin_rotf_00: {total_tris}")

eye_tri_indices = set([5044, 5049] + list(range(5251, 5271)))
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

# Convert back to uint8 list for typetree
new_ib_bytes = new_ib.tobytes()
m_tt["m_IndexBuffer"] = list(new_ib_bytes)

# Update submeshes
orig_sm0 = m_tt["m_SubMeshes"][0]
sm0 = dict(orig_sm0)
sm0["firstByte"] = 0
sm0["indexCount"] = body_count

sm1 = dict(orig_sm0)
sm1["firstByte"] = body_count * 2
sm1["indexCount"] = eye_count

m_tt["m_SubMeshes"] = [sm0, sm1]
mesh_obj.save_typetree(m_tt)
print("[✓] Partitioned cha_ironhide_cin_rotf_00 into 2 SubMeshes.")

# 4. Update Robot SMRs: 3131805236270788271 and 7476088394338840652
MAT_ROBOT_PID = 5474742503365929845
MAT_EYES_PID = -337851165086787921
for smr_pid in [3131805236270788271, 7476088394338840652]:
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

# 5. Update Robot Material: 5474742503365929845 (Neon Purple!)
mat_robot_obj = obj_map[MAT_ROBOT_PID]
mat_robot_tt = mat_robot_obj.read_typetree()
update_material_properties(
    mat_robot_tt,
    colors={"_emissive_intensity_col": {"r": 0.75, "g": 0.10, "b": 1.0, "a": 0.0}},
    floats={"_emissive_overbright_range": 35.0, "_emissive_range": 1.0}
)
mat_robot_obj.save_typetree(mat_robot_tt)
print("[✓] Robot Material tuned to Neon Purple (_emissive_intensity_col=[0.75, 0.10, 1.0]).")

# 6. Update Eyes Material: -337851165086787921 (Yellow Optics!)
mat_eyes_obj = obj_map[MAT_EYES_PID]
mat_eyes_tt = mat_eyes_obj.read_typetree()
update_material_properties(
    mat_eyes_tt,
    colors={
        "_emissive_intensity_col": {"r": 1.0, "g": 0.85, "b": 0.10, "a": 0.0},
        "_Color": {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0},
        "_base_col": {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0},
    },
    floats={"_emissive_overbright_range": 35.0, "_emissive_range": 1.0},
    texs={
        "_base_tex": -5161093122092615707,
        "_normal_tex": 8078947162710327917,
        "_pbr_composite_tex": 7395759426203415672,
    }
)
mat_eyes_obj.save_typetree(mat_eyes_tt)
print("[✓] Eyes Material tuned to Pure Yellow Optics (_emissive_intensity_col=[1.0, 0.85, 0.10]).")

# 7. Update Vehicle Material: -304038823457699575 (Neon Purple!)
mat_veh_obj = obj_map[-304038823457699575]
mat_veh_tt = mat_veh_obj.read_typetree()
update_material_properties(
    mat_veh_tt,
    colors={"_emissive_intensity_col": {"r": 0.75, "g": 0.10, "b": 1.0, "a": 0.0}},
    floats={"_emissive_overbright_range": 35.0, "_emissive_range": 1.0}
)
mat_veh_obj.save_typetree(mat_veh_tt)
print("[✓] Vehicle Material tuned to Neon Purple (_emissive_intensity_col=[0.75, 0.10, 1.0]).")

# 8. Save assetbundle
out_bytes = env.file.save(packer="lz4")
with open(BUNDLE_PATH, "wb") as f:
    f.write(out_bytes)
print(f"[✓] Successfully saved updated {BUNDLE_PATH} with LZ4 compression! Size: {len(out_bytes):,} bytes.")
