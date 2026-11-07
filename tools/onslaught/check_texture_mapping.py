import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

fbx_path = r"E:\Agent\TFTF-blender\3rd-party-models\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"
tex_dir = Path(r"E:\Agent\TFTF-blender\3rd-party-models\transformers-fall-of-cybertron-combaticons\textures")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

onslaught_objs = [
    # Armatures
    "Onslaught_ARM",
    "Onslaught_VH_ARM",
    # Robot meshes
    "RB_Onslaught_CHARSKEL_ArmLoL.mo.dmx",
    "RB_Onslaught_CHARSKEL_ArmLoR.mo.dmx",
    "RB_Onslaught_CHARSKEL_CapL.mo.dmx",
    "RB_Onslaught_CHARSKEL_CapR.mo.dmx",
    "RB_Onslaught_CHARSKEL_Chest.mo.dmx",
    "RB_Onslaught_CHARSKEL_Head.mo.dmx",
    "RB_Onslaught_CHARSKEL_Legs.mo.dmx",
    "RB_Onslaught_STAT_Wheel.mo.005.dmx",
    "RB_Onslaught_STAT_Wheel.mo.006.dmx",
    "RB_Onslaught_STAT_Wheel.mo.007.dmx",
    "RB_Onslaught_STAT_Wheel.mo.008.dmx",
    # Weapons
    "RB_HeavyMGL_SKEL.mo.dmx",
    "RB_HeavyMGR_SKEL.mo.dmx",
    "RB_RocketLauncherL_SKEL.mo.dmx",
    "RB_RocketLauncherR_SKEL.mo.dmx",
    # Vehicle
    "VH.dmx",
]

materials_used = set()
for oname in onslaught_objs:
    obj = bpy.data.objects.get(oname)
    if obj and obj.type == 'MESH':
        for slot in obj.material_slots:
            if slot.material:
                materials_used.add(slot.material.name)

print("=== MATERIALS USED BY ONSLAUGHT (ALL PARTS) ===")
for m in sorted(materials_used):
    print(f"- {m}")

# Now match materials to textures in tex_dir
all_tex_files = {f.name.lower(): f for f in tex_dir.glob("*")}

print("\n=== TEXTURE MATCHING ===")
mat_to_tex = {}
for mat_name in sorted(materials_used):
    print(f"\nMaterial: {mat_name}")
    # Normalize mat name
    # e.g. RB_Onslaught_ArmLo_Cust_E_Mat_INST -> rb_onslaught_armlo_cust
    # Base variations:
    # diffuse: _mat_inst, _mat, .png/.jpg
    # normal: _n
    # emission: _e
    m_clean = mat_name.lower().split('.')[0] # remove .001 etc
    matched = []
    for tf_lower, tf_path in all_tex_files.items():
        # Check if tf_lower is related to m_clean
        # E.g. m_clean is 'rb_onslaught_armlo_cust_e_mat_inst' -> file is 'rb_onslaught_armlo_cust_e_mat_inst.jpg'
        if m_clean in tf_lower or tf_lower.replace(".jpg", "").replace(".png", "") in m_clean:
            matched.append(tf_path.name)
        elif "tr_factionlogo" in m_clean and "decepticon" in tf_lower:
            matched.append(tf_path.name)
        elif "rocketlauncher" in m_clean and "rocketlauncher" in tf_lower:
            matched.append(tf_path.name)
        elif "heavymg" in m_clean and "heavymg" in tf_lower:
            matched.append(tf_path.name)
        elif "vh_interior" in m_clean and "vh_interior" in tf_lower:
            matched.append(tf_path.name)
        elif "vh_onslaught" in m_clean and "vh_onslaught" in tf_lower:
            matched.append(tf_path.name)
            
    print(f"  Matched textures: {matched}")
    mat_to_tex[mat_name] = matched
