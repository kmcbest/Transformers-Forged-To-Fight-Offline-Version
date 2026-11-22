import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
import math
from mathutils import Vector, Matrix
import json
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
FBX_PATH = r"O:\agent\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"
DONOR_JSON = ROOT / "3rd-party-models" / "BlastOff" / "00_donor_reference" / "donor_summary.json"
TEX_DIR = ROOT / "3rd-party-models" / "BlastOff" / "02_textures"

BLASTOFF_MESH_NAMES = [
    "RB_Blastoff_CHARSKEL_Head.001.dmx",
    "RB_Blastoff_CHARSKEL_ArmLoL.001.dmx",
    "RB_Blastoff_CHARSKEL_ArmLoR.001.dmx",
    "RB_BlastoffWing_STAT.001.dmx",
    "RB_BlastoffWing_STAT.dmx",
]

ROBOT_UV_MAP = {
    "RB_Blastoff_Chest_Cust_MatINST":    (0.5,   0.0,   0.5,  0.5),   # (0, 0, 1024, 1024)
    "RB_Blastoff_Legs_Cust_MatINST":     (0.5,   0.0,   0.5,  0.0),   # (0, 1024, 1024, 1024)
    "RB_Blastoff_Head_Cust_MatINST":     (0.25,  0.5,   0.25, 0.75),  # (1024, 0, 512, 512)
    "RB_Blastoff_ArmLo_Cust_MatINST":    (0.25,  0.75,  0.25, 0.75),  # (1536, 0, 512, 512)
    "RB_Blastoff_ArmUp_Cust_MatINST":    (0.25,  0.5,   0.25, 0.5),   # (1024, 512, 512, 512)
    "VH_Blastoff_Cust_MatINST":          (0.25,  0.75,  0.25, 0.5),   # (1536, 512, 512, 512)
    "TR_FactionLogo_Mat_INST.001":       (0.125, 0.5,   0.125, 0.375), # (1024, 1280, 256, 256)
}

def remap_uvs_clean(obj, uv_map, default_box=(0.5, 0.0, 0.5, 0.5)):
    uv_layer = obj.data.uv_layers.active
    if not uv_layer:
        return
    mat_slots = [slot.material.name if slot.material else "" for slot in obj.material_slots]
    for poly in obj.data.polygons:
        mname = mat_slots[poly.material_index] if poly.material_index < len(mat_slots) else ""
        u_sc, u_off, v_sc, v_off = uv_map.get(mname, default_box)
        pts = []
        for li in poly.loop_indices:
            uv = uv_layer.data[li].uv
            ux = 0.5 if (not math.isfinite(uv.x) or abs(uv.x) > 10.0) else uv.x
            vy = 0.5 if (not math.isfinite(uv.y) or abs(uv.y) > 10.0) else uv.y
            pts.append((li, ux, vy))
        mu = sum(p[1] for p in pts) / len(pts)
        mv = sum(p[2] for p in pts) / len(pts)
        du = math.floor(mu)
        dv = math.floor(mv)
        for li, ux, vy in pts:
            u_loc = min(0.994, max(0.006, ux - du))
            v_loc = min(0.994, max(0.006, vy - dv))
            uv_layer.data[li].uv = (u_loc * u_sc + u_off, v_loc * v_sc + v_off)
    obj.data.update()

def make_blastoff_preview_material(name, prefix):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    ta = nt.nodes.new("ShaderNodeTexImage")
    ta.image = bpy.data.images.load(str(TEX_DIR / f"{prefix}_Diffuse.png"))
    nt.links.new(ta.outputs["Color"], bsdf.inputs["Base Color"])

    tn = nt.nodes.new("ShaderNodeTexImage")
    tn.image = bpy.data.images.load(str(TEX_DIR / f"{prefix}_Normal_unity.png"))
    tn.image.colorspace_settings.name = "Non-Color"
    nmap = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(tn.outputs["Color"], nmap.inputs["Color"])
    nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])

    tem = nt.nodes.new("ShaderNodeTexImage")
    tem.image = bpy.data.images.load(str(TEX_DIR / f"{prefix}_Emission.png"))
    nt.links.new(tem.outputs["Color"], bsdf.inputs["Emission"])
    bsdf.inputs["Emission Strength"].default_value = 2.0
    bsdf.inputs["Roughness"].default_value = 0.55
    bsdf.inputs["Metallic"].default_value = 0.25
    return mat

def load_megatronus_bones():
    import numpy as np
    donor = json.loads(DONOR_JSON.read_text(encoding="utf-8"))
    mesh_00 = donor["meshes"]["cha_megatronus_gs_kabam_00"]
    avatar_tos = donor["avatars"]["cha_megatronus_gs_kabam_00Avatar"]["tos"]
    pos_b = {}
    for idx, (h, bp) in enumerate(zip(mesh_00["boneHashes"], mesh_00["bindposes"])):
        mat = np.array([
            [bp["e00"], bp["e01"], bp["e02"], bp["e03"]],
            [bp["e10"], bp["e11"], bp["e12"], bp["e13"]],
            [bp["e20"], bp["e21"], bp["e22"], bp["e23"]],
            [bp["e30"], bp["e31"], bp["e32"], bp["e33"]],
        ])
        inv_mat = np.linalg.inv(mat)
        upos = inv_mat[:3, 3]
        bname = avatar_tos.get(str(h), f"bone_{idx}").split("/")[-1]
        pos_b[bname] = Vector((-float(upos[0]), -float(upos[2]), float(upos[1])))
    return pos_b

def pose_segment_world(arm_obj, bone_name, child_name, target_head_w, target_tail_w, thickness_scale=1.0, preserve_length=False):
    bpy.context.view_layer.update()
    pb = arm_obj.pose.bones[bone_name]
    w_old = arm_obj.matrix_world @ pb.matrix
    p_head_old = (arm_obj.matrix_world @ pb.head).copy()
    if child_name and child_name in arm_obj.pose.bones:
        p_tail_old = (arm_obj.matrix_world @ arm_obj.pose.bones[child_name].head).copy()
    else:
        p_tail_old = (arm_obj.matrix_world @ pb.tail).copy()

    v_old = p_tail_old - p_head_old
    v_new = target_tail_w - target_head_w
    if v_old.length < 1e-4 or v_new.length < 1e-4:
        return

    q_rot = v_old.rotation_difference(v_new)
    s_len = 1.0 if preserve_length else (v_new.length / v_old.length)
    s_len = max(0.2, min(5.0, s_len))

    d = v_old.normalized()
    S = Matrix.Identity(3) * thickness_scale
    for r in range(3):
        for c in range(3):
            S[r][c] += (s_len - thickness_scale) * d[r] * d[c]

    R_new = q_rot.to_matrix() @ S @ w_old.to_3x3()
    M_new_w = R_new.to_4x4()
    M_new_w.translation = target_head_w
    pb.matrix = arm_obj.matrix_world.inverted() @ M_new_w
    bpy.context.view_layer.update()

def pb_head_w(arm_obj, bname):
    bpy.context.view_layer.update()
    return arm_obj.matrix_world @ arm_obj.pose.bones[bname].head

bpy.ops.wm.read_factory_settings(use_empty=True)
meg_pos = load_megatronus_bones()
bpy.ops.import_scene.fbx(filepath=FBX_PATH)

arm = bpy.data.objects.get("Blast-off_ARM")
robot_objs = [bpy.data.objects[n] for n in BLASTOFF_MESH_NAMES if n in bpy.data.objects]

keep_objs = set(robot_objs) | {arm}
for o in list(bpy.data.objects):
    if o not in keep_objs:
        bpy.data.objects.remove(o, do_unlink=True)

arm.location.y += 10.0118
for obj in robot_objs:
    obj.location.y += 10.0118

R_z90 = Matrix.Rotation(math.radians(-90), 4, 'Z')
arm.matrix_world = R_z90 @ arm.matrix_world
for obj in robot_objs:
    obj.matrix_world = R_z90 @ obj.matrix_world
bpy.context.view_layer.update()

bpy.ops.object.select_all(action="DESELECT")
for obj in robot_objs:
    obj.select_set(True)
arm.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

for obj in robot_objs:
    remap_uvs_clean(obj, ROBOT_UV_MAP)

SCALE_BLASTOFF = 2.2928
arm.scale = (SCALE_BLASTOFF, SCALE_BLASTOFF, SCALE_BLASTOFF)
for obj in robot_objs:
    obj.scale = (SCALE_BLASTOFF, SCALE_BLASTOFF, SCALE_BLASTOFF)
bpy.ops.object.select_all(action="DESELECT")
for obj in robot_objs:
    obj.select_set(True)
arm.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# Attach Armature modifier
for obj in robot_objs:
    arm_mod = obj.modifiers.get("Armature")
    if not arm_mod:
        arm_mod = obj.modifiers.new("Armature", "ARMATURE")
    arm_mod.object = arm

# Pose mode:
bpy.ops.object.select_all(action="DESELECT")
arm.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode="POSE")

# DO NOT SQUASH PELVIS OR SPINE!
# ONLY ALIGN LEGS TO FLOOR / MEGATRONUS STANCE
for side, sgn in (("L", 1.0), ("R", -1.0)):
    meg_side = "Left" if side == "L" else "Right"
    h_p = pb_head_w(arm, f"bip_hip_{side}")
    k_t = Vector((0.8965 * sgn, meg_pos[f"{meg_side}Leg"].y, meg_pos[f"{meg_side}Leg"].z))
    f_t = Vector((0.8965 * sgn, meg_pos[f"{meg_side}Foot"].y, meg_pos[f"{meg_side}Foot"].z))
    t_t = Vector((0.8965 * sgn, meg_pos[f"{meg_side}ToeBase"].y, meg_pos[f"{meg_side}ToeBase"].z))
    pose_segment_world(arm, f"bip_hip_{side}", f"bip_knee_{side}", Vector((0.8965 * sgn, h_p.y, h_p.z)), k_t, thickness_scale=0.96, preserve_length=False)
    pose_segment_world(arm, f"bip_knee_{side}", f"bip_foot_{side}", k_t, f_t, thickness_scale=0.96, preserve_length=False)
    pose_segment_world(arm, f"bip_foot_{side}", f"bip_toe_{side}", f_t, t_t, thickness_scale=0.96, preserve_length=True)

# Ground via evaluated mesh min_z
bpy.ops.object.mode_set(mode="OBJECT")
deps = bpy.context.evaluated_depsgraph_get()
min_z = 999.0
for obj in robot_objs:
    ev = obj.evaluated_get(deps)
    em = ev.to_mesh()
    for v in em.vertices:
        wz = (ev.matrix_world @ v.co).z
        if wz < min_z:
            min_z = wz
    ev.to_mesh_clear()

arm.location.z -= min_z
for obj in robot_objs:
    obj.location.z -= min_z
bpy.context.view_layer.update()

# Pose Arms to Megatronus rest arms
bpy.ops.object.select_all(action="DESELECT")
arm.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode="POSE")

for side, sgn in (("L", 1.0), ("R", -1.0)):
    meg_side = "Left" if side == "L" else "Right"
    ua_name = f"bip_upperArm_{side}"
    la_name = f"bip_lowerArm_{side}"
    h_name = f"bip_hand_{side}"

    ua_h = pb_head_w(arm, ua_name)
    wri_t = meg_pos[f"{meg_side}Hand"].copy()
    elb_t = meg_pos[f"{meg_side}ForeArm"].copy()
    arm_t = meg_pos[f"{meg_side}Arm"].copy()

    # Align arm down into natural rest pose
    pose_segment_world(arm, ua_name, la_name, Vector((arm_t.x, ua_h.y, arm_t.z)), elb_t, thickness_scale=0.96, preserve_length=False)
    pose_segment_world(arm, la_name, h_name, elb_t, wri_t, thickness_scale=0.96, preserve_length=False)

bpy.ops.object.mode_set(mode="OBJECT")
bpy.ops.object.select_all(action="DESELECT")
for obj in robot_objs:
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    for m in list(obj.modifiers):
        if m.type == "ARMATURE":
            bpy.ops.object.modifier_apply(modifier=m.name)

bpy.context.view_layer.objects.active = robot_objs[0]
bpy.ops.object.join()
robot_mesh = bpy.context.view_layer.objects.active
robot_mesh.name = "cha_blastoff_robot_natural"

mat = make_blastoff_preview_material("mat_test", "cha_blastoff_main")
robot_mesh.data.materials.clear()
robot_mesh.data.materials.append(mat)

# Render comparison camera view focusing on Upper Torso & Head
cam_data = bpy.data.cameras.new("TestCam")
cam_obj = bpy.data.objects.new("TestCam", cam_data)
bpy.context.collection.objects.link(cam_obj)
cam_data.lens = 50.0
cam_obj.location = Vector((0.0, -14.0, 9.5))
cam_obj.rotation_euler = (math.radians(88), 0, 0)
bpy.context.scene.camera = cam_obj

light_data = bpy.data.lights.new("Sun", type='SUN')
light_data.energy = 3.5
light_obj = bpy.data.objects.new("Sun", light_data)
bpy.context.collection.objects.link(light_obj)
light_obj.rotation_euler = (math.radians(45), math.radians(25), 0)

# Add a fill light
fill_data = bpy.data.lights.new("Fill", type='SUN')
fill_data.energy = 2.0
fill_obj = bpy.data.objects.new("Fill", fill_data)
bpy.context.collection.objects.link(fill_obj)
fill_obj.rotation_euler = (math.radians(45), math.radians(-45), 0)

bpy.context.scene.render.resolution_x = 1280
bpy.context.scene.render.resolution_y = 1080
out_img = str(ROOT / "renders" / "blastoff" / "test_natural_chest_head.png")
bpy.context.scene.render.filepath = out_img
bpy.ops.render.render(write_still=True)
print(f"[✓] Rendered {out_img}")
