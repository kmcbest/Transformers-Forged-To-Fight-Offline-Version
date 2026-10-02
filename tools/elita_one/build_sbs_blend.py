import json
import math
import mathutils
import bpy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
REST_JSON = ROOT / "tools" / "elita_one" / "arcee_unity_rest_matrices.json"
ANIM_JSON = ROOT / "tools" / "elita_one" / "arcee_attackLight_01.json"
HIERARCHY_JSON = ROOT / "tools" / "elita_one" / "arcee_bone_hierarchy.json"
SKIN_JSON = ROOT / "tools" / "elita_one" / "arcee_unity_verts_skin.json"
SETUP_BLEND = ROOT / "tools" / "elita_one" / "elita_one_arcee_setup.blend"
ARCEE_OBJ = ROOT / "tools" / "elita_one" / "arcee_extracted" / "arcee_robot_reference.obj"
ARCEE_TEX = ROOT / "tools" / "elita_one" / "arcee_extracted" / "cha_arcee_gs_deluxe2014_main_a.png"
ELITA_D00 = ROOT / "tools" / "elita_one" / "processed_textures" / "elita_main_diffuse.png"
ELITA_D01 = ROOT / "tools" / "elita_one" / "processed_textures" / "elita_vh_diffuse.png"
OUT_BLEND = ROOT / "tools" / "elita_one" / "elita_one_arcee_side_by_side.blend"

print("=== Building Elita One vs Arcee Side-by-Side Blend ===")

# Reset Blender
bpy.ops.wm.read_factory_settings(use_empty=True)

# 1. Load Data
with open(REST_JSON, "r", encoding="utf-8") as f:
    rest_data = json.load(f)
u_rest_map = {b["name"]: b["m"] for b in rest_data["bones"]}

with open(HIERARCHY_JSON, "r", encoding="utf-8") as f:
    hierarchy = json.load(f)

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

# 2. Build Base Armature
def create_armature(name):
    arm_data = bpy.data.armatures.new(name)
    arm_obj = bpy.data.objects.new(name, arm_data)
    bpy.context.scene.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='EDIT')

    # Add bones in hierarchy order
    edit_bones = {}
    for b in rest_data["bones"]:
        bname = b["name"]
        m_raw = b["m"]
        M_u = mathutils.Matrix((m_raw[0:4], m_raw[4:8], m_raw[8:12], m_raw[12:16]))
        M_b = C @ M_u @ C
        
        eb = arm_data.edit_bones.new(bname)
        head = M_b.translation
        eb.head = head
        # Use bone orientation for tail
        rot = M_b.to_3x3()
        eb.tail = head + rot @ mathutils.Vector((0.0, 0.08, 0.0))
        edit_bones[bname] = eb

    # Assign parents
    for bname, eb in edit_bones.items():
        pname = hierarchy.get(bname)
        if pname and pname in edit_bones:
            eb.parent = edit_bones[pname]

    bpy.ops.object.mode_set(mode='OBJECT')
    return arm_obj

print("[*] Creating Arcee Armature...")
arcee_arm = create_armature("Arcee_Armature")

print("[*] Creating Elita One Armature...")
elita_arm = create_armature("Elita_One_Armature")

# 3. Import Arcee Mesh from OBJ and bind with exact skin weights
print("[*] Importing Arcee reference mesh...")
bpy.ops.wm.obj_import(filepath=str(ARCEE_OBJ))
imported_objs = [o for o in bpy.context.selected_objects if o.type == 'MESH']
arcee_mesh = imported_objs[0]
arcee_mesh.name = "Arcee_Mesh"

# The OBJ is in Unity coordinates (Y-up, Z-forward). In Blender it needs X-90 rotation applied:
# Rotate Arcee 90 deg around X to align with (x, z, y)
bpy.ops.object.select_all(action='DESELECT')
arcee_mesh.select_set(True)
bpy.context.view_layer.objects.active = arcee_mesh
bpy.ops.transform.rotate(value=math.radians(90.0), orient_axis='X')
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# Assign official skin weights
print("[*] Assigning official skin weights to Arcee Mesh...")
arcee_mesh.vertex_groups.clear()
vg_cache = {}
for i, vinfo in enumerate(skin_data["verts"]):
    bones = vinfo["b"]
    weights = vinfo["w"]
    for bname, w in zip(bones, weights):
        if w > 0.001:
            if bname not in vg_cache:
                vg_cache[bname] = arcee_mesh.vertex_groups.new(name=bname)
            vg_cache[bname].add([i], w, 'REPLACE')

# Add Armature modifier
mod = arcee_mesh.modifiers.new(name="Armature", type='ARMATURE')
mod.object = arcee_arm
mod.use_vertex_groups = True
arcee_mesh.parent = arcee_arm

# Material for Arcee
arcee_mat = bpy.data.materials.new(name="Arcee_Official_Mat")
arcee_mat.use_nodes = True
bsdf = arcee_mat.node_tree.nodes.get("Principled BSDF")
tex_node = arcee_mat.node_tree.nodes.new(type="ShaderNodeTexImage")
tex_node.image = bpy.data.images.load(str(ARCEE_TEX))
arcee_mat.node_tree.links.new(tex_node.outputs['Color'], bsdf.inputs['Base Color'])
bsdf.inputs['Metallic'].default_value = 0.6
bsdf.inputs['Roughness'].default_value = 0.35
arcee_mesh.data.materials.clear()
arcee_mesh.data.materials.append(arcee_mat)

# 4. Import Elita One Mesh from elita_one_arcee_setup.blend
print("[*] Importing Elita One mesh from setup blend...")
with bpy.data.libraries.load(str(SETUP_BLEND), link=False) as (data_from, data_to):
    if "Elita_One_Mesh" in data_from.objects:
        data_to.objects = ["Elita_One_Mesh"]

elita_mesh = bpy.data.objects.get("Elita_One_Mesh")
bpy.context.scene.collection.objects.link(elita_mesh)

# Add Armature modifier to Elita One
elita_mesh.modifiers.clear()
mod_e = elita_mesh.modifiers.new(name="Armature", type='ARMATURE')
mod_e.object = elita_arm
mod_e.use_vertex_groups = True
elita_mesh.parent = elita_arm

# Materials for Elita One (bright & vibrant)
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
elita_mesh.data.materials.append(mat_vh)

# 5. Position Side-by-Side:
# Arcee at X = +2.6m (Viewer Left)
# Elita One at X = -2.6m (Viewer Right)
OFFSET_X = 2.6
arcee_arm.location = (OFFSET_X, 0.0, 0.0)
arcee_mesh.location = (OFFSET_X, 0.0, 0.0)

elita_arm.location = (-OFFSET_X, 0.0, 0.0)
elita_mesh.location = (-OFFSET_X, 0.0, 0.0)
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

# 7. Bake Shared Action: Agile_AttackLight_01
print(f"[*] Baking Action: Agile_AttackLight_01 ({len(anim_data['frames'])} frames)...")
action = bpy.data.actions.new(name="Agile_AttackLight_01")

arcee_arm.animation_data_create()
arcee_arm.animation_data.action = action

elita_arm.animation_data_create()
elita_arm.animation_data.action = action

# Ensure quaternion mode on all pose bones
for arm in [arcee_arm, elita_arm]:
    for pb in arm.pose.bones:
        pb.rotation_mode = 'QUATERNION'
        pb.location = (0.0, 0.0, 0.0)

hips_bone = arcee_arm.data.bones.get("Hips")
hips_rest_b = hips_bone.head if hips_bone else mathutils.Vector()

frames = anim_data["frames"]
bpy.context.scene.frame_start = 0
bpy.context.scene.frame_end = len(frames) - 1

for f_idx, f in enumerate(frames):
    frame_map = {b["name"]: b for b in f["bones"]}
    
    # Delta R in Armature space
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
            
    # Apply to pose bones
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
            pb.location = pos_anim - hips_rest_b
            pb.keyframe_insert(data_path="location", frame=f_idx)

print("[✓] Action Agile_AttackLight_01 successfully baked!")

# 8. Setup Lighting and Camera
cam_data = bpy.data.cameras.new("FrontCamera")
cam_obj = bpy.data.objects.new("FrontCamera", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)
bpy.context.scene.camera = cam_obj
# Position camera in front facing +Y
cam_obj.location = (0.0, -10.5, 4.4)
cam_obj.rotation_euler = (math.radians(82.0), 0.0, 0.0)
cam_data.lens = 42

# Lights
light_key = bpy.data.lights.new(name="KeySun", type='SUN')
light_key.energy = 3.5
light_key_obj = bpy.data.objects.new(name="KeySun", object_data=light_key)
bpy.context.scene.collection.objects.link(light_key_obj)
light_key_obj.rotation_euler = (math.radians(45.0), math.radians(20.0), math.radians(-30.0))

light_fill = bpy.data.lights.new(name="FillSun", type='SUN')
light_fill.energy = 1.8
light_fill_obj = bpy.data.objects.new(name="FillSun", object_data=light_fill)
bpy.context.scene.collection.objects.link(light_fill_obj)
light_fill_obj.rotation_euler = (math.radians(30.0), math.radians(-30.0), math.radians(150.0))

# Render settings (Workbench for fast, crisp, clean PBR visualization)
bpy.context.scene.render.engine = 'BLENDER_WORKBENCH'
bpy.context.scene.display.shading.light = 'STUDIO'
bpy.context.scene.display.shading.color_type = 'TEXTURE'
bpy.context.scene.render.resolution_x = 1920
bpy.context.scene.render.resolution_y = 1080

# Save blend file
bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
print(f"[✓] Saved side-by-side blend file to: {OUT_BLEND}")
