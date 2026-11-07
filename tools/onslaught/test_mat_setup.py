import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
import os
from pathlib import Path

fbx_path = r"E:\Agent\TFTF-blender\3rd-party-models\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"
tex_dir = Path(r"E:\Agent\TFTF-blender\3rd-party-models\transformers-fall-of-cybertron-combaticons\textures")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

# Dictionary defining exact texture filenames for each material pattern
mat_texture_defs = {
    "RB_Onslaught_ArmLo_Cust_E_Mat_INST": {
        "diffuse": "rb_onslaught_armlo_cust_e_mat_inst.jpg",
        "normal": "rb_onslaught_armlo_cust_n.jpg",
        "emission": "rb_onslaught_armlo_cust_e.jpg"
    },
    "RB_Onslaught_ArmUp_Cust_E_Mat_INST": {
        "diffuse": "rb_onslaught_armup_cust_e_mat_inst.jpg",
        "normal": "rb_onslaught_armup_cust_n.jpg",
        "emission": None
    },
    "RB_Onslaught_Chest_Cust_E_Mat_INST": {
        "diffuse": "rb_onslaught_chest_cust_e_mat_inst.jpg",
        "normal": "rb_onslaught_chest_cust_n.jpg",
        "emission": "rb_onslaught_chest_cust_e.jpg"
    },
    "RB_Onslaught_Head_Cust_E_Mat_INST": {
        "diffuse": "rb_onslaught_head_cust_e_mat_inst.jpg",
        "normal": "rb_onslaught_head_cust_n.jpg",
        "emission": "rb_onslaught_head_cust_e.jpg"
    },
    "RB_Onslaught_Legs_Cust_E_Mat_INST": {
        "diffuse": "rb_onslaught_legs_cust_e_mat_inst.jpg",
        "normal": "rb_onslaught_legs_cust_n.jpg",
        "emission": "rb_onslaught_legs_cust_e.jpg"
    },
    "RB_Onslaught_Wheel_Cust_E_Mat_INST": {
        "diffuse": "rb_onslaught_wheel_cust_e_mat_inst.jpg",
        "normal": "rb_onslaught_wheel_cust_n.jpg",
        "emission": "rb_onslaught_wheel_cust_e.jpg"
    },
    "VH_Onslaught_NormSpec_Cust_E_Mat_INST": {
        "diffuse": "vh_onslaught_normspec_cust_e_mat_inst.jpg",
        "normal": "vh_onslaught_normspec_cust_n.jpg",
        "emission": "vh_onslaught_normspec_cust_e.jpg"
    },
    "VH_Interior_MAT": {
        "diffuse": "vh_interior_mat.jpg",
        "normal": "vh_interior_n.jpg",
        "emission": None
    },
    "TR_FactionLogo_Mat_INST": {
        "diffuse": "DecepticonLogo.png",
        "normal": None,
        "emission": None
    },
    "WEP_HeavyMG_MATINST": {
        "diffuse": "wep_heavymg_matinst.jpg",
        "normal": "wep_heavymg_matinst_n.jpg",
        "emission": "wep_heavymg_matinst_e.jpg"
    },
    "WEP_RocketLauncher_MATINST": {
        "diffuse": "wep_rocketlauncher_matinst.jpg",
        "normal": "wep_rocketlauncher_n.jpg",
        "emission": "wep_rocketlauncher_e.jpg"
    },
    "RB_ArmUp_Cust_MatINST_INST": {
        "diffuse": "rb_armup_cust_matinst_inst.jpg",
        "normal": "rb_armup_cust_matinst_n.jpg",
        "emission": None
    }
}

def setup_material_nodes(mat, tex_info):
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()
    
    # Create Principled BSDF and Output
    output_node = nodes.new(type='ShaderNodeOutputMaterial')
    output_node.location = (400, 0)
    
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    links.new(bsdf.outputs['BSDF'], output_node.inputs['Surface'])
    
    # 1. Diffuse / Base Color
    if tex_info.get("diffuse"):
        d_path = tex_dir / tex_info["diffuse"]
        if d_path.exists():
            tex_img = nodes.new(type='ShaderNodeTexImage')
            tex_img.image = bpy.data.images.load(str(d_path))
            tex_img.location = (-400, 200)
            links.new(tex_img.outputs['Color'], bsdf.inputs['Base Color'])
            if tex_info["diffuse"].endswith(".png"):
                links.new(tex_img.outputs['Alpha'], bsdf.inputs['Alpha'])
                mat.blend_method = 'CLIP'
    
    # 2. Normal Map
    if tex_info.get("normal"):
        n_path = tex_dir / tex_info["normal"]
        if n_path.exists():
            norm_img = nodes.new(type='ShaderNodeTexImage')
            norm_img.image = bpy.data.images.load(str(n_path))
            norm_img.image.colorspace_settings.name = 'Non-Color'
            norm_img.location = (-600, -200)
            
            norm_map = nodes.new(type='ShaderNodeNormalMap')
            norm_map.location = (-300, -200)
            links.new(norm_img.outputs['Color'], norm_map.inputs['Color'])
            links.new(norm_map.outputs['Normal'], bsdf.inputs['Normal'])
            
    # 3. Emission
    if tex_info.get("emission"):
        e_path = tex_dir / tex_info["emission"]
        if e_path.exists():
            emis_img = nodes.new(type='ShaderNodeTexImage')
            emis_img.image = bpy.data.images.load(str(e_path))
            emis_img.location = (-400, -500)
            if 'Emission Color' in bsdf.inputs:
                links.new(emis_img.outputs['Color'], bsdf.inputs['Emission Color'])
            elif 'Emission' in bsdf.inputs:
                links.new(emis_img.outputs['Color'], bsdf.inputs['Emission'])
            if 'Emission Strength' in bsdf.inputs:
                bsdf.inputs['Emission Strength'].default_value = 1.0

# Apply to all materials in scene that match our definitions
configured_count = 0
for mat in bpy.data.materials:
    m_name = mat.name
    matched_def = None
    for pattern, defs in mat_texture_defs.items():
        if pattern.lower() in m_name.lower():
            matched_def = defs
            break
    if matched_def:
        setup_material_nodes(mat, matched_def)
        configured_count += 1
        print(f"Configured material: {m_name} -> {matched_def['diffuse']}")

print(f"\nTotal materials successfully hooked to textures: {configured_count}")
