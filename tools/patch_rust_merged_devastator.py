import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import os
import shutil
import copy
import UnityPy
from UnityPy.classes import PPtr, UnityTexEnv, ColorRGBA
from UnityPy.streams.EndianBinaryReader import EndianBinaryReader
from PIL import Image

char_bundle_path = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\characters_procedural_odr\character_mergecharacters_procedural.assetbundle"
bundle_in = r"E:\Agent\TFTF-blender\assets_redeco\rust_merged.assetbundle"
bundle_out_redeco = r"E:\Agent\TFTF-blender\assets_redeco\rust_merged.assetbundle"
bundle_out_apk = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\rust\rust_merged.assetbundle"

print("================================================================")
print("  Comprehensive Devastator Stage Patch: Lighting, Tex & Loop   ")
print("================================================================")

# 1. Load bundles
print("\n[1] Loading bundles...")
env = UnityPy.load(bundle_in)
bf = list(env.files.values())[0]
sf = list(bf.files.values())[0]

env_char = UnityPy.load(char_bundle_path)
sf_char = list(list(env_char.files.values())[0].files.values())[0]

# 2. Inject Dynamic Character PBR Shader
print("\n[2] Injecting Dynamic Character PBR Shader...")
char_shader_pid = -7396015257959012681
char_shader_obj = sf_char.objects[char_shader_pid]
char_shader_raw = char_shader_obj.get_raw_data()

# Find Shader type index in sf.types
shader_type_idx = None
for idx, t in enumerate(sf.types):
    if t.class_id == 48: # Shader
        shader_type_idx = idx
        break

if shader_type_idx is None:
    raise RuntimeError("Shader type (class_id=48) not found in rust_merged.assetbundle!")

# Create / overwrite shader object in sf
new_shader_obj = copy.copy(char_shader_obj)
new_shader_obj.assets_file = sf
new_shader_obj.type_id = shader_type_idx
new_shader_obj.serialized_type = sf.types[shader_type_idx]
new_shader_obj.set_raw_data(char_shader_raw)
sf.objects[char_shader_pid] = new_shader_obj

read_s = sf.objects[char_shader_pid].read()
s_name = getattr(read_s, 'm_Name', '')
if not s_name and hasattr(read_s, 'm_ParsedForm'):
    s_name = getattr(read_s.m_ParsedForm, 'm_Name', '')
print(f"  [✓] Successfully injected Shader {char_shader_pid}: '{s_name}'")

# 3. Unify resS streaming files into primary archive
print("\n[3] Unifying resS streaming resources into primary archive...")
rust_ress_name = "CAB-8047d50cb53b499f81473861dbf0f211.resS"
dev_ress_name = "CAB-173392592a09aa74156a2f75549d5a15.resS"

dev_tex_pids = [
    -7369055296425394768, # Tx_Devastator_Weapon_D
    -6954966601468800323, # Tx_Megatron_Caterpillar_D
    -952201693256237551,  # Tx_Devastator_N
    2427243559233083411,  # Tx_Megatron_Caterpillar_N
    3446589362272867144,  # Tx_Devastator_D
    4767449473672574012,  # Tx_Devastator_Weapon_N
]

if dev_ress_name in bf.files:
    rust_ress_bytes = bf.files[rust_ress_name].read()
    dev_ress_bytes = bf.files[dev_ress_name].read()
    base_offset = len(rust_ress_bytes)
    print(f"  Primary resS: {base_offset:,} bytes, Devastator resS: {len(dev_ress_bytes):,} bytes")

    combined_ress_bytes = rust_ress_bytes + dev_ress_bytes
    reader = EndianBinaryReader(combined_ress_bytes)
    reader.flags = bf.files[rust_ress_name].flags
    bf.files[rust_ress_name] = reader
    del bf.files[dev_ress_name]

    for pid in dev_tex_pids:
        tex = sf.objects[pid].read()
        orig_offset = tex.m_StreamData.offset
        tex.m_StreamData.path = f"archive:/{rust_ress_name.replace('.resS', '')}/{rust_ress_name}"
        tex.m_StreamData.offset = base_offset + orig_offset
        tex.save()
        print(f"  [✓] Updated {tex.m_Name}: offset={tex.m_StreamData.offset}, path={tex.m_StreamData.path}")
else:
    print(f"  [i] {dev_ress_name} already merged or not present in bundle.")

# 4. Configure Devastator Materials with Character Dynamic PBR
print("\n[4] Configuring Devastator Materials with Dynamic PBR...")
pbr_composite_tex_pid = 3169036710040326424

# Sample character material template for floats & colors
tmpl_char_mat = None
for pid, obj in sf_char.objects.items():
    if obj.type.name == "Material" and "3726D299" in getattr(obj.read(), "m_Name", ""):
        tmpl_char_mat = obj.read()
        break

if not tmpl_char_mat:
    raise RuntimeError("Template character material 3726D299 not found!")

mat_configs = {
    8837953495545057200: { # M_Devastator
        "name": "M_Devastator",
        "diffuse": 3446589362272867144, # Tx_Devastator_D
        "normal": -952201693256237551,  # Tx_Devastator_N
        "color": (1.65, 1.65, 1.65, 1.0),
        "emission": (0.15, 0.15, 0.15, 1.0),
    },
    -7145629621652322861: { # M_Weapon
        "name": "M_Weapon",
        "diffuse": -7369055296425394768, # Tx_Devastator_Weapon_D
        "normal": 4767449473672574012,   # Tx_Devastator_Weapon_N
        "color": (1.65, 1.65, 1.65, 1.0),
        "emission": (0.15, 0.15, 0.15, 1.0),
    },
    -2900704665952030965: { # M_Caterpillar
        "name": "M_Caterpillar",
        "diffuse": -6954966601468800323, # Tx_Megatron_Caterpillar_D
        "normal": 2427243559233083411,   # Tx_Megatron_Caterpillar_N
        "color": (1.5, 1.5, 1.5, 1.0),
        "emission": (0.12, 0.12, 0.12, 1.0),
    },
    -7231731770884373194: { # M_Symbol_Black
        "name": "M_Symbol_Black",
        "diffuse": 0,
        "normal": 0,
        "color": (0.05, 0.05, 0.05, 1.0),
        "emission": (0.0, 0.0, 0.0, 1.0),
    }
}

for m_pid, cfg in mat_configs.items():
    if m_pid in sf.objects:
        mat = sf.objects[m_pid].read()
        print(f"  Patching material '{mat.m_Name}' ({m_pid})...")
        mat.m_Shader = PPtr(m_FileID=0, m_PathID=char_shader_pid, assetsfile=sf)
        mat.m_ShaderKeywords = "EB_SECOND_DIRECTIONAL_LIGHT_ON _AO_TEX _BASE_TEX _EMISSIVE_TEX _METALLIC_TEX _MODE_CLEARCOAT _NORMAL_TEX _ROUGHNESS_TEX"
        mat.m_LightmapFlags = 5

        # Clone and customize floats from character template
        new_floats = []
        for fname, fval in tmpl_char_mat.m_SavedProperties.m_Floats:
            if fname == "_OcclusionStrength":
                new_floats.append((fname, 0.0)) # Turn off dark AO multiplier
            elif fname == "_reflectance":
                new_floats.append((fname, 0.08)) # Crisp specular edge
            elif fname == "_clearcoat_reflectance_range":
                new_floats.append((fname, 0.20)) # Boost clearcoat highlights
            else:
                new_floats.append((fname, fval))
        mat.m_SavedProperties.m_Floats = new_floats

        # Clone and customize colors from character template
        new_colors = []
        for cname, cval in tmpl_char_mat.m_SavedProperties.m_Colors:
            if cname == "_Color":
                r, g, b, a = cfg["color"]
                new_colors.append((cname, ColorRGBA(r=r, g=g, b=b, a=a)))
            elif cname == "_EmissionColor":
                er, eg, eb, ea = cfg["emission"]
                new_colors.append((cname, ColorRGBA(r=er, g=eg, b=eb, a=ea)))
            elif cname in ["_base_col", "_base_r_col", "_base_g_col", "_base_b_col"]:
                new_colors.append((cname, ColorRGBA(r=0.75, g=0.75, b=0.75, a=1.0)))
            else:
                new_colors.append((cname, cval))
        mat.m_SavedProperties.m_Colors = new_colors

        # Build TexEnvs
        new_tex_envs = []
        for k, tmpl_env in tmpl_char_mat.m_SavedProperties.m_TexEnvs:
            target_tex_pid = 0
            if k == "_base_tex":
                target_tex_pid = cfg["diffuse"]
            elif k == "_normal_tex":
                target_tex_pid = cfg["normal"]
            elif k == "_pbr_composite_tex":
                target_tex_pid = pbr_composite_tex_pid
            
            tex_env = UnityTexEnv(
                m_Offset=tmpl_env.m_Offset,
                m_Scale=tmpl_env.m_Scale,
                m_Texture=PPtr(m_FileID=0, m_PathID=target_tex_pid, assetsfile=sf)
            )
            new_tex_envs.append((k, tex_env))
        mat.m_SavedProperties.m_TexEnvs = new_tex_envs
        mat.save()
        print(f"    [✓] Upgraded to Character Dynamic PBR (diff={cfg['diffuse']}, norm={cfg['normal']}, comp={pbr_composite_tex_pid})")

# 5. Fix Animation Clip to Loop without LoopPose distortion
print("\n[5] Patching Devastator_Combine AnimationClip for clean infinite loop...")
clip_pid = -4744859319559139663
if clip_pid in sf.objects:
    clip = sf.objects[clip_pid].read()
    clip.m_WrapMode = 2 # Loop
    if hasattr(clip, "m_MuscleClip"):
        mc = clip.m_MuscleClip
        mc.m_LoopTime = True # Keep state loop enabled
        # STRICTLY DISABLE LOOP POSE BLEND:
        # Loop Pose forces end frame (combined robot) to blend with start frame (scattered vehicles),
        # causing limbs to rip apart and disjoint!
        mc.m_LoopBlend = False
        mc.m_LoopBlendOrientation = False
        mc.m_LoopBlendPositionY = False
        mc.m_LoopBlendPositionXZ = False
    clip.save()
    print(f"  [✓] AnimationClip '{clip.m_Name}' wrapMode=2, loopTime=True, loopBlend=False.")
else:
    print(f"  [!] AnimationClip {clip_pid} not found in bundle!")

# 6. Ensure Devastator GameObjects Layer 11
print("\n[6] Ensuring Devastator GameObjects are on Layer 11...")
dev_root_t_pid = 4735182709122105431
dev_gos_patched = 0

def set_layer_recursive(t_pid):
    global dev_gos_patched
    t = sf.objects[t_pid].read()
    go_pptr = t.m_GameObject
    if go_pptr.path_id in sf.objects:
        go = sf.objects[go_pptr.path_id].read()
        go.m_Layer = 11
        go.save()
        dev_gos_patched += 1
    if hasattr(t, "m_Children"):
        for c in t.m_Children:
            if c.path_id in sf.objects:
                set_layer_recursive(c.path_id)

set_layer_recursive(dev_root_t_pid)
print(f"  [✓] Set layer=11 on {dev_gos_patched} GameObjects.")

# 7. Ensure SkinnedMeshRenderers updateWhenOffscreen = True
print("\n[7] Setting SkinnedMeshRenderers updateWhenOffscreen = True...")
smr_names = ['Caterpillar', 'Devastator 1', 'Devastator_Weapon', 'Symbol_AB', 'Symbol_DC']
for pid, obj in sf.objects.items():
    if obj.type.name == "SkinnedMeshRenderer":
        smr = obj.read()
        go = smr.m_GameObject.read()
        if go.m_Name in smr_names:
            smr.m_UpdateWhenOffscreen = True
            smr.save()
print("  [✓] SMRs updateWhenOffscreen set to True.")

# 8. Clean missing MonoBehaviour
print("\n[8] Cleaning missing MonoBehaviour on Devastator_Colossus...")
dev_colossus_t = sf.objects[dev_root_t_pid].read()
dev_colossus_go = dev_colossus_t.m_GameObject.read()
clean_comp_pairs = []
for cp in dev_colossus_go.m_Component:
    if cp.component.path_id in sf.objects:
        c_type = sf.objects[cp.component.path_id].type.name
        if c_type == "MonoBehaviour":
            continue
        clean_comp_pairs.append(cp)
dev_colossus_go.m_Component = clean_comp_pairs
dev_colossus_go.save()

# 9. Pack and Save
print("\n[9] Packing AssetBundle with LZ4...")
saved_bytes = env.file.save(packer="lz4")
print(f"  [✓] Packed size: {len(saved_bytes):,} bytes ({len(saved_bytes)/(1024*1024):.2f} MB)")

# 10. Write to target paths
for dest in [bundle_out_redeco, bundle_out_apk]:
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "wb") as f:
        f.write(saved_bytes)
    print(f"  [✓] Deployed to {dest}")

# 11. Rigorous Verification
print("\n[10] Performing Rigorous Verification on Deployed Bundle...")
ver_env = UnityPy.load(saved_bytes)
ver_sf = list(list(ver_env.files.values())[0].files.values())[0]

# Verify Shader
ver_s = ver_sf.objects[char_shader_pid].read()
s_name_v = getattr(ver_s, 'm_Name', '') or getattr(ver_s.m_ParsedForm, 'm_Name', '')
assert "SECOND_DIRECTIONAL_LIGHT" in s_name_v, f"Unexpected shader name: {s_name_v}"
print(f"  [✓] Verified Shader: '{s_name_v}'")

# Verify Animation Clip
ver_clip = ver_sf.objects[clip_pid].read()
assert ver_clip.m_WrapMode == 2, f"WrapMode is {ver_clip.m_WrapMode}, expected 2"
assert ver_clip.m_MuscleClip.m_LoopTime == True, f"LoopTime is {ver_clip.m_MuscleClip.m_LoopTime}, expected True"
assert ver_clip.m_MuscleClip.m_LoopBlend == False, f"LoopBlend is {ver_clip.m_MuscleClip.m_LoopBlend}, expected False"
print(f"  [✓] Verified AnimationClip: wrapMode={ver_clip.m_WrapMode}, loopTime={ver_clip.m_MuscleClip.m_LoopTime}, loopBlend={ver_clip.m_MuscleClip.m_LoopBlend}")

# Verify All Textures
for pid in dev_tex_pids:
    tex_v = ver_sf.objects[pid].read()
    img_v = tex_v.image
    assert img_v.size[0] > 0 and img_v.size[1] > 0
    print(f"  [✓] Verified Texture '{tex_v.m_Name}': {img_v.size}, {img_v.mode}")

print("\nAll Devastator stage patches and verifications passed 100% successfully!")
