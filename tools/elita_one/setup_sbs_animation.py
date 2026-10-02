import json
import math
import mathutils
import bpy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
SETUP_BLEND = ROOT / "tools" / "elita_one" / "elita_one_arcee_setup.blend"
REST_JSON = ROOT / "tools" / "elita_one" / "arcee_unity_rest_matrices.json"
ANIM_JSON = ROOT / "tools" / "elita_one" / "arcee_attackLight_01.json"
HIERARCHY_JSON = ROOT / "tools" / "elita_one" / "arcee_bone_hierarchy.json"
SKIN_JSON = ROOT / "tools" / "elita_one" / "arcee_unity_verts_skin.json"
ARCEE_TEX = ROOT / "tools" / "elita_one" / "arcee_extracted" / "cha_arcee_gs_deluxe2014_main_a.png"
ELITA_D00 = ROOT / "tools" / "elita_one" / "processed_textures" / "elita_main_diffuse.png"
ELITA_D01 = ROOT / "tools" / "elita_one" / "processed_textures" / "elita_vh_diffuse.png"
OUT_BLEND = ROOT / "tools" / "elita_one" / "elita_one_arcee_side_by_side.blend"
OUT_DIR = Path(r"C:\Users\Xiangli496\.gemini\antigravity\brain\db8b7cf0-602b-4ceb-a715-2db112ce44ce")

print("=== Setting up Side-by-Side Animation Blend ===")
bpy.ops.wm.open_mainfile(filepath=str(SETUP_BLEND))

arcee_arm = bpy.data.objects.get("Arcee_Armature")
arcee_mesh = bpy.data.objects.get("Arcee_Ghost_Reference")
elita_arm = bpy.data.objects.get("Elita_One_Armature")
elita_mesh = bpy.data.objects.get("Elita_One_Mesh")

with open(HIERARCHY_JSON, "r", encoding="utf-8") as f:
    hierarchy = json.load(f)

with open(REST_JSON, "r", encoding="utf-8") as f:
    rest_data = json.load(f)
u_rest_map = {b["name"]: b["m"] for b in rest_data["bones"]}

with open(ANIM_JSON, "r", encoding="utf-8") as f:
    anim_data = json.load(f)

with open(SKIN_JSON, "r", encoding="utf-8") as f:
    skin_data = json.load(f)

C = mathutils.Matrix((
    (1, 0, 0, 0),
    (0, 0, 1, 0),
    (0, 1, 0, 0),
    (0, 0, 0, 1)
))

# 1. Setup Bone Parents on both Armatures
for arm_obj in [arcee_arm, elita_arm]:
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='EDIT')
    for eb in arm_obj.data.edit_bones:
        eb.use_connect = False
        pname = hierarchy.get(eb.name)
        if pname and pname in arm_obj.data.edit_bones:
            eb.parent = arm_obj.data.edit_bones[pname]
    bpy.ops.object.mode_set(mode='OBJECT')

print("[✓] Configured bone hierarchy on both armatures.")

# 2. Skin and Texture Arcee
arcee_mesh.name = "Arcee_Mesh"
arcee_mesh.vertex_groups.clear()
vg_cache = {}
for i, vinfo in enumerate(skin_data["verts"]):
    for bname, w in zip(vinfo["b"], vinfo["w"]):
        if w > 0.001:
            if bname not in vg_cache:
                vg_cache[bname] = arcee_mesh.vertex_groups.new(name=bname)
            vg_cache[bname].add([i], w, 'REPLACE')

arcee_mesh.modifiers.clear()
mod_a = arcee_mesh.modifiers.new(name="Armature", type='ARMATURE')
mod_a.object = arcee_arm
mod_a.use_vertex_groups = True
arcee_mesh.parent = arcee_arm
arcee_mesh.matrix_parent_inverse = mathutils.Matrix.Identity(4)

# Material for Arcee
arcee_mat = bpy.data.materials.new(name="Arcee_Official_Mat")
arcee_mat.use_nodes = True
bsdf_a = arcee_mat.node_tree.nodes.get("Principled BSDF")
tex_a = arcee_mat.node_tree.nodes.new(type="ShaderNodeTexImage")
tex_a.image = bpy.data.images.load(str(ARCEE_TEX))
arcee_mat.node_tree.links.new(tex_a.outputs['Color'], bsdf_a.inputs['Base Color'])
bsdf_a.inputs['Metallic'].default_value = 0.6
bsdf_a.inputs['Roughness'].default_value = 0.35
arcee_mesh.data.materials.clear()
arcee_mesh.data.materials.append(arcee_mat)
print("[✓] Bound Arcee mesh with 100% official skin and textures.")

# 3. Textures for Elita One
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
elita_mesh.data.materials.append(mat_main) # BlackGlass uses main
elita_mesh.data.materials.append(mat_vh)
print("[✓] Applied bright PBR materials to Elita One.")

# 4. Precompute Rest Orientations
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

# 5. Bake Action: Agile_AttackLight_01
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

hips_bone = arcee_arm.data.bones.get("Hips")
# Unity rest hips pos
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
        pb = arcee_arm.pose.bones.get(bname)
        if not pb:
            continue
        bone = arcee_arm.data.bones.get(bname)
        R_b = R_rest_blender.get(bname, bone.matrix_local.to_3x3().normalized())
        
        if bone.parent and bone.parent.name in delta_R:
            delta_rel = delta_R[bone.parent.name].inverted() @ delta_R[bname]
        else:
            delta_rel = delta_R[bname]
            
        Q_mat = R_b.inverted() @ delta_rel @ R_b
        q = Q_mat.to_quaternion()
        pb.rotation_quaternion = q
        pb.keyframe_insert(data_path="rotation_quaternion", frame=f_idx)
        
        # Hips root translation delta
        if bname == "Hips" and "Hips" in frame_map:
            m_raw = frame_map["Hips"]["m"]
            M_u = mathutils.Matrix((m_raw[0:4], m_raw[4:8], m_raw[8:12], m_raw[12:16]))
            M_conv = C @ M_u @ C
            pos_anim = M_conv.translation
            pb.location = pos_anim - hips_rest_conv
            pb.keyframe_insert(data_path="location", frame=f_idx)

print("[✓] Baked Agile_AttackLight_01 successfully!")

# 6. Adjust Camera to frame both characters perfectly
cam = bpy.data.objects.get("FrontCam")
if cam:
    cam.location = (0.0, -14.0, 4.4)
    cam.data.lens = 38
    cam.rotation_euler = (math.radians(90.0), 0.0, 0.0)

# Workbench display settings
bpy.context.scene.render.engine = 'BLENDER_WORKBENCH'
bpy.context.scene.display.shading.light = 'STUDIO'
bpy.context.scene.display.shading.color_type = 'TEXTURE'
bpy.context.scene.render.resolution_x = 1920
bpy.context.scene.render.resolution_y = 1080

# Save blend
bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
print(f"[✓] Saved side-by-side blend to {OUT_BLEND}")

# Render keyframes
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

print("=== Side-by-Side Build and Render Completed Successfully! ===")
