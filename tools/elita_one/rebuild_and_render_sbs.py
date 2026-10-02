import json
import math
import mathutils
import bpy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
FBX_PATH = ROOT / "3rd-party-models" / "transformers-galatic-trials-elita-one" / "source" / "Elita_One.fbx"
REST_JSON = ROOT / "tools" / "elita_one" / "arcee_unity_rest_matrices.json"
ANIM_JSON = ROOT / "tools" / "elita_one" / "arcee_attackLight_01.json"
HIERARCHY_JSON = ROOT / "tools" / "elita_one" / "arcee_bone_hierarchy.json"
ARCEE_FULL_MESH = ROOT / "tools" / "elita_one" / "arcee_full_mesh.json"
ARCEE_TEX = ROOT / "tools" / "elita_one" / "arcee_extracted" / "cha_arcee_gs_deluxe2014_main_a.png"
ELITA_D00 = ROOT / "tools" / "elita_one" / "processed_textures" / "elita_main_diffuse.png"
ELITA_D01 = ROOT / "tools" / "elita_one" / "processed_textures" / "elita_vh_diffuse.png"
OUT_BLEND = ROOT / "tools" / "elita_one" / "elita_one_arcee_side_by_side.blend"
OUT_DIR = Path(r"C:\Users\Xiangli496\.gemini\antigravity\brain\db8b7cf0-602b-4ceb-a715-2db112ce44ce")

print("=== Building Side-by-Side with Rigorous Arm Alignment & Fixed Mapping ===")
bpy.ops.wm.read_factory_settings(use_empty=True)

# 1. Load Metadata
with open(HIERARCHY_JSON, "r", encoding="utf-8") as f:
    hierarchy = json.load(f)

with open(REST_JSON, "r", encoding="utf-8") as f:
    rest_data = json.load(f)
u_rest_map = {b["name"]: b["m"] for b in rest_data["bones"]}

with open(ANIM_JSON, "r", encoding="utf-8") as f:
    anim_data = json.load(f)

with open(ARCEE_FULL_MESH, "r", encoding="utf-8") as f:
    arcee_mesh_data = json.load(f)

# Load base bone mapping and apply critical fixes
with open(ROOT / "tools" / "elita_one" / "elita_to_arcee_mapping.json", "r", encoding="utf-8") as f:
    bone_mapping = json.load(f)

# FIX CRITICAL WHEEL & ARM SOCKET MAPPINGS
# Lower wheels are on Upper Arms, NOT Forearms!
bone_mapping["l_lower_cover_wheel_skin"] = "LeftArm"
bone_mapping["l_lower_wheel_skin"] = "LeftArm"
bone_mapping["l_lower_wheel_skin_end"] = "LeftArm"
bone_mapping["r_lower_cover_wheel_skin"] = "RightArm"
bone_mapping["r_lower_wheel_skin"] = "RightArm"
bone_mapping["r_lower_wheel_skin_end"] = "RightArm"

# Lower arm pistons stay on ForeArm
bone_mapping["l_piston_lower_arm_start_skin"] = "LeftForeArm"
bone_mapping["l_piston_lower_arm_start_skin_end"] = "LeftForeArm"
bone_mapping["r_piston_lower_arm_start_skin"] = "RightForeArm"
bone_mapping["r_piston_lower_arm_start_skin_end"] = "RightForeArm"

# Hip pistons stay rigidly inside Hips (prevents rods poking out)
for p_name in [
    "l_piston_leg_end_01_skin", "l_piston_leg_end_01_skin_end",
    "l_piston_leg_end_02_skin", "l_piston_leg_end_02_skin_end",
    "r_piston_leg_end_01_skin", "r_piston_leg_end_01_skin_end",
    "r_piston_leg_end_02_skin", "r_piston_leg_end_02_skin_end",
    "l_cover_hips_skin", "r_cover_hips_skin"
]:
    bone_mapping[p_name] = "Hips"

# Shoulder pistons anchor rigidly to Spine1 (chest) like Demolishor's collar
bone_mapping["l_shoulder_pistons_skin"] = "Spine1"
bone_mapping["l_shoulder_pistons_skin_end"] = "Spine1"
bone_mapping["r_shoulder_pistons_skin"] = "Spine1"
bone_mapping["r_shoulder_pistons_skin_end"] = "Spine1"

# Feet heel FX transforms are not deform bones, map to Feet
bone_mapping["l_foot_heel_skin"] = "LeftFoot"
bone_mapping["l_foot_heel_skin_end"] = "LeftFoot"
bone_mapping["r_foot_heel_skin"] = "RightFoot"
bone_mapping["r_foot_heel_skin_end"] = "RightFoot"

C = mathutils.Matrix((
    (1, 0, 0, 0),
    (0, 0, 1, 0),
    (0, 1, 0, 0),
    (0, 0, 0, 1)
))

# 2. Build Base 63-Bone Armature
def create_armature(name):
    arm_data = bpy.data.armatures.new(name)
    arm_obj = bpy.data.objects.new(name, arm_data)
    bpy.context.scene.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='EDIT')

    edit_bones = {}
    for b in rest_data["bones"]:
        bname = b["name"]
        if bname in edit_bones:
            continue
        m_raw = b["m"]
        M_u = mathutils.Matrix((m_raw[0:4], m_raw[4:8], m_raw[8:12], m_raw[12:16]))
        M_b = C @ M_u @ C
        
        eb = arm_data.edit_bones.new(bname)
        eb.head = M_b.translation
        eb.tail = M_b.translation + mathutils.Vector((0.0, 0.08, 0.0))
        edit_bones[bname] = eb

    for bname, eb in edit_bones.items():
        eb.use_connect = False
        pname = hierarchy.get(bname)
        if pname and pname in edit_bones:
            eb.parent = edit_bones[pname]

    bpy.ops.object.mode_set(mode='OBJECT')
    return arm_obj

print("[*] Creating 63-bone Armatures...")
arcee_arm = create_armature("Arcee_Armature")
elita_arm = create_armature("Elita_One_Armature")

# 3. Construct Arcee Mesh from Unity Ground-Truth Data
print("[*] Constructing Arcee Mesh from Unity ground-truth data...")
b_verts = [(v["x"], v["z"], v["y"]) for v in arcee_mesh_data["vertices"]]
raw_tris = arcee_mesh_data["triangles"]
b_faces = [(raw_tris[i], raw_tris[i+1], raw_tris[i+2]) for i in range(0, len(raw_tris), 3)]

a_mesh_data = bpy.data.meshes.new("Arcee_Mesh_Data")
a_mesh_data.from_pydata(b_verts, [], b_faces)
a_mesh_data.update()

arcee_mesh = bpy.data.objects.new("Arcee_Mesh", a_mesh_data)
bpy.context.scene.collection.objects.link(arcee_mesh)

uv_layer = a_mesh_data.uv_layers.new(name="UVMap")
for poly in a_mesh_data.polygons:
    for loop_idx in poly.loop_indices:
        v_idx = a_mesh_data.loops[loop_idx].vertex_index
        ve = arcee_mesh_data["vertices"][v_idx]
        uv_layer.data[loop_idx].uv = (ve["u"], ve["v"])

for i, ve in enumerate(arcee_mesh_data["vertices"]):
    for we in ve["weights"]:
        bname = we["bone"]
        w = we["weight"]
        if w > 0.001:
            vg = arcee_mesh.vertex_groups.get(bname) or arcee_mesh.vertex_groups.new(name=bname)
            vg.add([i], w, 'REPLACE')

mod_a = arcee_mesh.modifiers.new(name="Armature", type='ARMATURE')
mod_a.object = arcee_arm
mod_a.use_vertex_groups = True
arcee_mesh.parent = arcee_arm

arcee_mat = bpy.data.materials.new(name="Arcee_Mat")
arcee_mat.use_nodes = True
bsdf_a = arcee_mat.node_tree.nodes.get("Principled BSDF")
tex_a = arcee_mat.node_tree.nodes.new(type="ShaderNodeTexImage")
tex_a.image = bpy.data.images.load(str(ARCEE_TEX))
arcee_mat.node_tree.links.new(tex_a.outputs['Color'], bsdf_a.inputs['Base Color'])
bsdf_a.inputs['Metallic'].default_value = 0.6
bsdf_a.inputs['Roughness'].default_value = 0.35
arcee_mesh.data.materials.append(arcee_mat)

# 4. Import Elita One from FBX with Precise Alignment
print("[*] Importing Elita One FBX...")
bpy.ops.import_scene.fbx(filepath=str(FBX_PATH))

fbx_arm = bpy.data.objects.get("SK_CH_11")
elita_mesh = bpy.data.objects.get("SK_CH_11.001")

# Remove extra objects (vehicle, icospheres)
for o in list(bpy.context.scene.collection.objects):
    if o.name not in ["Arcee_Armature", "Elita_One_Armature", "Arcee_Mesh", "SK_CH_11", "SK_CH_11.001"]:
        bpy.data.objects.remove(o, do_unlink=True)

# Mathematical transform matrix (+90° Z rotation, 1.09365x scale)
scale_s = 8.840 / 8.083
M_transform = mathutils.Matrix.Rotation(math.radians(90.0), 4, 'Z') @ mathutils.Matrix.Scale(scale_s, 4)

fbx_arm.data.transform(M_transform)
elita_mesh.data.transform(M_transform)

# Posing FBX Armature to rotate A-pose arms inward by 21.2°
print("[*] Adjusting Elita One A-pose arms inward to match Arcee rest pose...")
bpy.context.view_layer.objects.active = fbx_arm
bpy.ops.object.mode_set(mode='POSE')

l_sh = fbx_arm.data.bones.get("l_upperarm_skin").head_local
r_sh = fbx_arm.data.bones.get("r_upperarm_skin").head_local
l_wr = fbx_arm.data.bones.get("l_hand_skin").head_local
r_wr = fbx_arm.data.bones.get("r_hand_skin").head_local

target_l_wrist = mathutils.Vector((-1.2848, -0.0372, 4.2729))
target_r_wrist = mathutils.Vector(( 1.2848, -0.0372, 4.2729))

v_l_curr = l_wr - l_sh
v_l_targ = target_l_wrist - l_sh
q_l = v_l_curr.rotation_difference(v_l_targ)

v_r_curr = r_wr - r_sh
v_r_targ = target_r_wrist - r_sh
q_r = v_r_curr.rotation_difference(v_r_targ)

pb_l = fbx_arm.pose.bones.get("l_upperarm_skin")
pb_r = fbx_arm.pose.bones.get("r_upperarm_skin")

R_l_rest = fbx_arm.data.bones.get("l_upperarm_skin").matrix_local.to_3x3()
q_l_local = (R_l_rest.inverted() @ q_l.to_matrix() @ R_l_rest).to_quaternion()
pb_l.rotation_quaternion = q_l_local

R_r_rest = fbx_arm.data.bones.get("r_upperarm_skin").matrix_local.to_3x3()
q_r_local = (R_r_rest.inverted() @ q_r.to_matrix() @ R_r_rest).to_quaternion()
pb_r.rotation_quaternion = q_r_local

# Clench Left and Right fists cleanly so rest mesh has natural clenched fists matching Arcee
rot_curl_l01 = mathutils.Euler((0.0, 0.0, math.radians(75.0))).to_quaternion()
rot_curl_l02 = mathutils.Euler((0.0, 0.0, math.radians(85.0))).to_quaternion()
rot_curl_l03 = mathutils.Euler((0.0, 0.0, math.radians(75.0))).to_quaternion()

for f_base in ["l_index", "l_middle", "l_ring", "l_pinky"]:
    pb1 = fbx_arm.pose.bones.get(f"{f_base}_01_skin")
    pb2 = fbx_arm.pose.bones.get(f"{f_base}_02_skin")
    pb3 = fbx_arm.pose.bones.get(f"{f_base}_03_skin")
    if pb1: pb1.rotation_quaternion = rot_curl_l01
    if pb2: pb2.rotation_quaternion = rot_curl_l02
    if pb3: pb3.rotation_quaternion = rot_curl_l03

pb_lt1 = fbx_arm.pose.bones.get("l_thumb_01_skin")
pb_lt2 = fbx_arm.pose.bones.get("l_thumb_02_skin")
pb_lt3 = fbx_arm.pose.bones.get("l_thumb_03_skin")
if pb_lt1: pb_lt1.rotation_quaternion = mathutils.Euler((math.radians(20.0), math.radians(45.0), math.radians(-35.0))).to_quaternion()
if pb_lt2: pb_lt2.rotation_quaternion = mathutils.Euler((0.0, 0.0, math.radians(-70.0))).to_quaternion()
if pb_lt3: pb_lt3.rotation_quaternion = mathutils.Euler((0.0, 0.0, math.radians(-50.0))).to_quaternion()

rot_curl_r01 = mathutils.Euler((0.0, 0.0, math.radians(-75.0))).to_quaternion()
rot_curl_r02 = mathutils.Euler((0.0, 0.0, math.radians(-85.0))).to_quaternion()
rot_curl_r03 = mathutils.Euler((0.0, 0.0, math.radians(-75.0))).to_quaternion()

for f_base in ["r_index", "r_middle", "r_ring", "r_pinky"]:
    pb1 = fbx_arm.pose.bones.get(f"{f_base}_01_skin")
    pb2 = fbx_arm.pose.bones.get(f"{f_base}_02_skin")
    pb3 = fbx_arm.pose.bones.get(f"{f_base}_03_skin")
    if pb1: pb1.rotation_quaternion = rot_curl_r01
    if pb2: pb2.rotation_quaternion = rot_curl_r02
    if pb3: pb3.rotation_quaternion = rot_curl_r03

pb_rt1 = fbx_arm.pose.bones.get("r_thumb_01_skin")
pb_rt2 = fbx_arm.pose.bones.get("r_thumb_02_skin")
pb_rt3 = fbx_arm.pose.bones.get("r_thumb_03_skin")
if pb_rt1: pb_rt1.rotation_quaternion = mathutils.Euler((math.radians(-20.0), math.radians(-45.0), math.radians(35.0))).to_quaternion()
if pb_rt2: pb_rt2.rotation_quaternion = mathutils.Euler((0.0, 0.0, math.radians(70.0))).to_quaternion()
if pb_rt3: pb_rt3.rotation_quaternion = mathutils.Euler((0.0, 0.0, math.radians(50.0))).to_quaternion()

bpy.context.view_layer.update()
bpy.ops.object.mode_set(mode='OBJECT')

# Apply armature deformation to mesh to bake the aligned arm rest pose
bpy.context.view_layer.objects.active = elita_mesh
mod_orig = None
for m in elita_mesh.modifiers:
    if m.type == 'ARMATURE':
        mod_orig = m
        break

if mod_orig:
    bpy.ops.object.modifier_apply(modifier=mod_orig.name)
    print("[✓] Applied arm pose deformation cleanly into Elita One mesh geometry!")

# Remove fbx_arm
bpy.data.objects.remove(fbx_arm, do_unlink=True)

elita_mesh.name = "Elita_One_Mesh"
elita_mesh.parent = None
elita_mesh.matrix_world = mathutils.Matrix.Identity(4)

# Remap vertex groups
print("[*] Remapping Elita One vertex groups to 63 Arcee bones...")
remapped_weights = {v.index: {} for v in elita_mesh.data.vertices}
for v in elita_mesh.data.vertices:
    for g in v.groups:
        orig_name = elita_mesh.vertex_groups[g.group].name
        target_bone = bone_mapping.get(orig_name)
        if target_bone:
            remapped_weights[v.index][target_bone] = remapped_weights[v.index].get(target_bone, 0.0) + g.weight

elita_mesh.vertex_groups.clear()
new_vgs = {}
for b in rest_data["bones"]:
    bname = b["name"]
    if bname not in new_vgs:
        new_vgs[bname] = elita_mesh.vertex_groups.new(name=bname)

for v_idx, w_dict in remapped_weights.items():
    if not w_dict: continue
    top_4 = sorted(w_dict.items(), key=lambda kv: kv[1], reverse=True)[:4]
    sum_w = sum(w for _, w in top_4)
    if sum_w > 0:
        for bname, w in top_4:
            norm_w = w / sum_w
            if norm_w > 0.001 and bname in new_vgs:
                new_vgs[bname].add([v_idx], norm_w, 'REPLACE')

mod_e = elita_mesh.modifiers.new(name="Armature", type='ARMATURE')
mod_e.object = elita_arm
mod_e.use_vertex_groups = True
elita_mesh.parent = elita_arm

# Elita One Materials (Bright PBR)
mat_main = bpy.data.materials.new(name="Elita_Main_Mat")
mat_main.use_nodes = True
bsdf_m = mat_main.node_tree.nodes.get("Principled BSDF")
tex_m = mat_main.node_tree.nodes.new(type="ShaderNodeTexImage")
tex_m.image = bpy.data.images.load(str(ELITA_D00))
mat_main.node_tree.links.new(tex_m.outputs['Color'], bsdf_m.inputs['Base Color'])
bsdf_m.inputs['Metallic'].default_value = 0.5
bsdf_m.inputs['Roughness'].default_value = 0.35

mat_vh = bpy.data.materials.new(name="Elita_Vehicle_Mat")
mat_vh.use_nodes = True
bsdf_v = mat_vh.node_tree.nodes.get("Principled BSDF")
tex_v = mat_vh.node_tree.nodes.new(type="ShaderNodeTexImage")
tex_v.image = bpy.data.images.load(str(ELITA_D01))
mat_vh.node_tree.links.new(tex_v.outputs['Color'], bsdf_v.inputs['Base Color'])
bsdf_v.inputs['Metallic'].default_value = 0.5
bsdf_v.inputs['Roughness'].default_value = 0.35

elita_mesh.data.materials.clear()
elita_mesh.data.materials.append(mat_main)
elita_mesh.data.materials.append(mat_main)
elita_mesh.data.materials.append(mat_vh)
print(f"[✓] Elita One Mesh ready ({len(elita_mesh.data.vertices)} vertices).")

# 5. Position Side-by-Side:
OFFSET_X = 2.6
arcee_arm.location = (OFFSET_X, 0.0, 0.0)
arcee_mesh.location = (0.0, 0.0, 0.0)

elita_arm.location = (-OFFSET_X, 0.0, 0.0)
elita_mesh.location = (0.0, 0.0, 0.0)
bpy.context.view_layer.update()

# 6. Precompute Hierarchy Order and Rest Orientations
def get_hierarchy_order(armature):
    order = []
    def traverse(b):
        order.append(b.name)
        for child in b.children:
            traverse(child)
    for root in [b for b in armature.data.bones if b.parent is None]:
        traverse(root)
    return order

order = get_hierarchy_order(arcee_arm)
R_rest_unity = {}
R_rest_blender = {}
for bname in order:
    bone = arcee_arm.data.bones.get(bname)
    if bname in u_rest_map and bone:
        m_raw = u_rest_map[bname]
        M_u = mathutils.Matrix((m_raw[0:4], m_raw[4:8], m_raw[8:12], m_raw[12:16]))
        M_conv = C @ M_u @ C
        R_rest_unity[bname] = M_conv.to_3x3().normalized()
        R_rest_blender[bname] = bone.matrix_local.to_3x3().normalized()

# 7. Bake Action: Agile_AttackLight_01
print(f"[*] Baking Action: Agile_AttackLight_01 ({len(anim_data['frames'])} frames)...")
action = bpy.data.actions.new(name="Agile_AttackLight_01")

arcee_arm.animation_data_clear()
arcee_arm.animation_data_create()
arcee_arm.animation_data.action = action

elita_arm.animation_data_clear()
elita_arm.animation_data_create()
elita_arm.animation_data.action = action

for arm in [arcee_arm, elita_arm]:
    for pb in arm.pose.bones:
        pb.rotation_mode = 'QUATERNION'
        pb.location = (0.0, 0.0, 0.0)

frames = anim_data["frames"]
bpy.context.scene.frame_start = 0
bpy.context.scene.frame_end = len(frames) - 1

hips_u_rest = mathutils.Matrix((u_rest_map["Hips"][0:4], u_rest_map["Hips"][4:8], u_rest_map["Hips"][8:12], u_rest_map["Hips"][12:16]))
hips_rest_conv = (C @ hips_u_rest @ C).translation

for f_idx, f in enumerate(frames):
    frame_map = {b["name"]: b for b in f["bones"]}
    
    delta_R = {}
    for bname in order:
        if bname in frame_map and bname in R_rest_unity:
            m_raw = frame_map[bname]["m"]
            M_u = mathutils.Matrix((m_raw[0:4], m_raw[4:8], m_raw[8:12], m_raw[12:16]))
            M_conv = C @ M_u @ C
            R_anim = M_conv.to_3x3().normalized()
            delta_R[bname] = R_anim @ R_rest_unity[bname].inverted()
        else:
            delta_R[bname] = mathutils.Matrix.Identity(3)
            
    for bname in order:
        bone = arcee_arm.data.bones.get(bname)
        if not bone: continue
        R_b = R_rest_blender.get(bname, bone.matrix_local.to_3x3().normalized())
        
        if bone.parent and bone.parent.name in delta_R:
            delta_rel = delta_R[bone.parent.name].inverted() @ delta_R[bname]
        else:
            delta_rel = delta_R[bname]
            
        Q_mat = R_b.inverted() @ delta_rel @ R_b
        q = Q_mat.to_quaternion()
        
        for arm in [arcee_arm, elita_arm]:
            pb = arm.pose.bones.get(bname)
            if pb:
                pb.rotation_quaternion = q
                pb.keyframe_insert(data_path="rotation_quaternion", frame=f_idx)
        
        if bname == "Hips" and "Hips" in frame_map:
            m_raw = frame_map["Hips"]["m"]
            M_u = mathutils.Matrix((m_raw[0:4], m_raw[4:8], m_raw[8:12], m_raw[12:16]))
            M_conv = C @ M_u @ C
            pos_anim = M_conv.translation
            loc_delta = pos_anim - hips_rest_conv
            for arm in [arcee_arm, elita_arm]:
                pb = arm.pose.bones.get("Hips")
                if pb:
                    pb.location = loc_delta
                    pb.keyframe_insert(data_path="location", frame=f_idx)

print("[✓] Baked Agile_AttackLight_01 successfully!")

# 8. Setup Lighting and Camera
cam_data = bpy.data.cameras.new("FrontCam")
cam_obj = bpy.data.objects.new("FrontCam", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)
bpy.context.scene.camera = cam_obj
cam_obj.location = (0.0, 18.5, 4.4)
cam_data.lens = 32
cam_obj.rotation_euler = (math.radians(90.0), 0.0, math.radians(180.0))

light_key = bpy.data.lights.new(name="KeySun", type='SUN')
light_key.energy = 4.0
light_key_obj = bpy.data.objects.new(name="KeySun", object_data=light_key)
bpy.context.scene.collection.objects.link(light_key_obj)
light_key_obj.rotation_euler = (math.radians(135.0), math.radians(15.0), math.radians(25.0))

light_fill = bpy.data.lights.new(name="FillSun", type='SUN')
light_fill.energy = 2.5
light_fill_obj = bpy.data.objects.new(name="FillSun", object_data=light_fill)
bpy.context.scene.collection.objects.link(light_fill_obj)
light_fill_obj.rotation_euler = (math.radians(120.0), math.radians(-15.0), math.radians(-25.0))

bpy.context.scene.render.engine = 'BLENDER_WORKBENCH'
bpy.context.scene.display.shading.light = 'STUDIO'
bpy.context.scene.display.shading.color_type = 'TEXTURE'
bpy.context.scene.render.resolution_x = 1920
bpy.context.scene.render.resolution_y = 1080

bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
print(f"[✓] Saved side-by-side blend file to {OUT_BLEND}")

# Check vertex displacement in Frame 0
bpy.context.scene.frame_set(0)
bpy.context.view_layer.update()
depsgraph = bpy.context.evaluated_depsgraph_get()
elita_eval = elita_mesh.evaluated_get(depsgraph)
mesh_eval = elita_eval.to_mesh()

displacements = []
for i in range(len(elita_mesh.data.vertices)):
    p_rest = elita_mesh.data.vertices[i].co
    p_eval = mesh_eval.vertices[i].co
    dist = (p_eval - p_rest).length
    vgs = [(elita_mesh.vertex_groups[g.group].name, round(g.weight, 2)) for g in elita_mesh.data.vertices[i].groups if g.weight > 0.05]
    displacements.append((dist, i, p_rest, p_eval, vgs))

displacements.sort(key=lambda x: x[0], reverse=True)
print(f"\nTop 10 largest vertex displacements in Frame 0 after alignment:")
for dist, idx, rest, eval_p, vgs in displacements[:10]:
    print(f"Dist={dist:6.2f}m | Vert {idx:5d} | Rest=({rest.x:5.2f}, {rest.y:5.2f}, {rest.z:5.2f}) | Eval=({eval_p.x:5.2f}, {eval_p.y:5.2f}, {eval_p.z:5.2f}) | VGs={vgs}")

elita_eval.to_mesh_clear()

# 9. Render Keyframes: 0 (Guard), 6 (Windup), 11 (Jab Strike), 18 (Recovery)
render_frames = [0, 6, 11, 18]
render_names = [
    "preview_elita_arcee_frame00_guard.png",
    "preview_elita_arcee_frame06_windup.png",
    "preview_elita_arcee_frame11_jab_strike.png",
    "preview_elita_arcee_frame18_recovery.png"
]

for f, name in zip(render_frames, render_names):
    bpy.context.scene.frame_set(f)
    bpy.context.view_layer.update()
    out_path = OUT_DIR / name
    bpy.context.scene.render.filepath = str(out_path)
    bpy.ops.render.render(write_still=True)
    print(f"[✓] Rendered frame {f} -> {name}")

print("=== Successfully Built and Rendered Side-by-Side Validation! ===")
