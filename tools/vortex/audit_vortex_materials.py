import bpy
import sys
import os

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

bpy.ops.wm.read_factory_settings(use_empty=True)
fbx_path = r"E:\Agent\TFTF-blender\3rd-party-models\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"
bpy.ops.import_scene.fbx(filepath=fbx_path)

mesh_names = [
    "RB_Vortex_CHARSKEL_ArmLoL.mo.dmx",
    "RB_Vortex_CHARSKEL_ArmLoR.mo.dmx",
    "RB_Vortex_CHARSKEL_Head.mo.dmx",
    "VH_Vortex_SKEL.001.dmx",
    "WEP_IonBlade_SKEL.mo_L.dmx",
    "WEP_IonBlade_SKEL.mo_R.dmx"
]

tex_dir = r"E:\Agent\TFTF-blender\3rd-party-models\transformers-fall-of-cybertron-combaticons\textures"
available_texs = {f.lower(): f for f in os.listdir(tex_dir)}

print("--- Material & Texture Mapping Check ---")
for mname in mesh_names:
    obj = bpy.data.objects.get(mname)
    if not obj: continue
    print(f"\nObject: {mname}")
    for mat_slot in obj.material_slots:
        mat = mat_slot.material
        if not mat: continue
        print(f"  Material: {mat.name}")
        # Find which textures match this material name
        mat_base = mat.name.lower().split(".")[0].replace("inst", "").replace("mat", "").strip("_")
        print(f"    Clean base name: '{mat_base}'")
        matched = []
        for tl, orig in available_texs.items():
            if mat_base in tl:
                matched.append(orig)
        print(f"    Matched textures in folder: {matched}")
