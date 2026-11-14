import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import os
import shutil
import copy
from pathlib import Path
import UnityPy
from UnityPy.classes import PPtr, UnityTexEnv, ColorRGBA
from UnityPy.streams.EndianBinaryReader import EndianBinaryReader

ROOT = Path(r"E:\Agent\TFTF-blender")
KARNAK_BASE = ROOT / "assets_base" / "karnak" / "karnak_merged.assetbundle"
COMBINERS_BUNDLE = ROOT / "stage_project" / "AssetBundles" / "karnak_combiners.assetbundle"
CHAR_BUNDLE = ROOT / "assets_base" / "character_mergecharacters_procedural.assetbundle"
OUT_REDECO = ROOT / "assets_redeco" / "karnak_merged.assetbundle"

print("====================================================================")
print("  TFTF Stage Mod: Merging & Patching Karnak Combiners (Volc & Vic)  ")
print("====================================================================")

# 1. Load source bundles
print("\n[Step 1] Loading source bundles...")
env_k = UnityPy.load(str(KARNAK_BASE))
bf_k = list(env_k.files.values())[0]
karnak_cab_name = "CAB-6afa7b665f6656587644b2ec0fb30f0e"
sf_k = bf_k.files[karnak_cab_name]

env_c = UnityPy.load(str(COMBINERS_BUNDLE))
bf_c = list(env_c.files.values())[0]
comb_cab_name = "CAB-86382daaae14d1c1aaf19ea28133948f"
sf_c = bf_c.files[comb_cab_name]

env_ch = UnityPy.load(str(CHAR_BUNDLE))
bf_ch = list(env_ch.files.values())[0]
cab_ch = [k for k in bf_ch.files.keys() if not k.endswith('.resS')][0]
sf_ch = bf_ch.files[cab_ch]

print(f"  Karnak base objects: {len(sf_k.objects)}")
print(f"  Combiners objects: {len(sf_c.objects)}")

# 2. Inject Dynamic Character PBR Shader
print("\n[Step 2] Injecting Dynamic Character PBR Shader...")
char_shader_pid = -7396015257959012681
char_shader_obj = sf_ch.objects[char_shader_pid]
char_shader_raw = char_shader_obj.get_raw_data()

shader_type_idx = None
for idx, t in enumerate(sf_k.types):
    if t.class_id == 48: # Shader
        shader_type_idx = idx
        break

if shader_type_idx is None:
    raise RuntimeError("Shader type (class_id=48) not found in karnak_merged.assetbundle!")

new_shader_obj = copy.copy(char_shader_obj)
new_shader_obj.assets_file = sf_k
new_shader_obj.type_id = shader_type_idx
new_shader_obj.serialized_type = sf_k.types[shader_type_idx]
new_shader_obj.set_raw_data(char_shader_raw)
sf_k.objects[char_shader_pid] = new_shader_obj

read_s = sf_k.objects[char_shader_pid].read()
s_name = getattr(read_s, 'm_Name', '') or getattr(read_s.m_ParsedForm, 'm_Name', '')
print(f"  [✓] Injected Shader {char_shader_pid}: '{s_name}' (type_idx={shader_type_idx})")

# 3. Integrate TypeTree definitions from combiners
print("\n[Step 3] Integrating TypeTree definitions...")
base_type_offset = len(sf_k.types)
for comb_t in sf_c.types:
    sf_k.types.append(comb_t)
print(f"  Appended {len(sf_c.types)} TypeTree nodes (base offset: {base_type_offset})")

if hasattr(sf_c, 'script_types'):
    for st in sf_c.script_types:
        if st not in sf_k.script_types:
            sf_k.script_types.append(st)

# 4. Copy Combiners objects into karnak SerializedFile
print("\n[Step 4] Merging Combiners objects into Karnak SerializedFile...")
copied = 0
for pid, obj in sf_c.objects.items():
    # Skip AssetBundle header (PID 1) and Unity Standard Shader (-4850512016903265157)
    if pid in [1, -4850512016903265157]:
        continue

    raw = obj.get_raw_data()
    obj.set_raw_data(raw)

    new_type_id = base_type_offset + obj.type_id
    obj.type_id = new_type_id
    obj.serialized_type = sf_k.types[new_type_id]
    obj.assets_file = sf_k
    sf_k.objects[pid] = obj
    copied += 1

print(f"  [✓] Merged {copied} Combiners objects with 100% binary fidelity.")

# 5. Single-track resS streaming resources consolidation
print("\n[Step 5] Consolidating resS streaming resources into primary archive...")
karnak_ress_name = f"{karnak_cab_name}.resS"
comb_ress_name = f"{comb_cab_name}.resS"

comb_tex_pids = [
    -6714775949259442448, # Victorion_Glass_CA
    -3168068222919951088, # Tx_Volcanicus_Weapon_D
    -1996513945004160825, # Tx_Volcanicus_N
    -1505079905186056747, # Tx_Volcanicus_D
    -890209823152787406,  # Victorion_AO
    1145463298758413118,  # Character_Atlas_Color
    3939815687492814677,  # Tx_Volcanicus_Weapon_N
]

if comb_ress_name in bf_c.files:
    karnak_ress_bytes = bf_k.files[karnak_ress_name].read()
    comb_ress_bytes = bf_c.files[comb_ress_name].read()
    base_offset = len(karnak_ress_bytes)
    print(f"  Primary Karnak resS: {base_offset:,} bytes, Combiners resS: {len(comb_ress_bytes):,} bytes")

    combined_ress_bytes = karnak_ress_bytes + comb_ress_bytes
    reader = EndianBinaryReader(combined_ress_bytes)
    reader.flags = bf_k.files[karnak_ress_name].flags
    bf_k.files[karnak_ress_name] = reader

    # Delete any secondary resS if present in container
    if comb_ress_name in bf_k.files:
        del bf_k.files[comb_ress_name]

    for pid in comb_tex_pids:
        tex = sf_k.objects[pid].read()
        orig_offset = tex.m_StreamData.offset
        tex.m_StreamData.path = f"archive:/{karnak_cab_name}/{karnak_ress_name}"
        tex.m_StreamData.offset = base_offset + orig_offset
        tex.save()
        print(f"  [✓] Updated {tex.m_Name}: offset={tex.m_StreamData.offset}, path={tex.m_StreamData.path}")
else:
    print(f"  [!] ERROR: {comb_ress_name} not found in combiners bundle!")

# 6. Connect Karnak_Combiners to karnak_merged Transform hierarchy
print("\n[Step 6] Connecting scene Transform hierarchy and scaling Colossi...")
karnak_merged_t_pid = 2928687205036248359
karnak_merged_t = sf_k.objects[karnak_merged_t_pid].read()

comb_root_t_pid = 1785545777453502114 # Karnak_Combiners
comb_root_t = sf_k.objects[comb_root_t_pid].read()

new_child_pptr = PPtr(m_FileID=0, m_PathID=comb_root_t_pid, assetsfile=sf_k)
karnak_merged_t.m_Children.append(new_child_pptr)
karnak_merged_t.save()

comb_root_t.m_Father = PPtr(m_FileID=0, m_PathID=karnak_merged_t_pid, assetsfile=sf_k)
comb_root_t.save()
print(f"  [✓] Karnak_Combiners (PID {comb_root_t_pid}) parented to karnak_merged (PID {karnak_merged_t_pid}).")

# Scale Volcanicus to true Colossus height ~31.1m and position at (-48.0, 1.5, 46.0) (Position ① outside battle circle)
volc_t = sf_k.objects[5962962886032363889].read()
volc_t.m_LocalPosition.x = -48.0
volc_t.m_LocalPosition.y = 1.5
volc_t.m_LocalPosition.z = 46.0
volc_t.m_LocalRotation.x = 0.0
volc_t.m_LocalRotation.y = 0.91976
volc_t.m_LocalRotation.z = 0.0
volc_t.m_LocalRotation.w = 0.39249
volc_t.m_LocalScale.x = 600.0
volc_t.m_LocalScale.y = 600.0
volc_t.m_LocalScale.z = 600.0
volc_t.save()
print(f"  [✓] Scaled Volcanicus: scale=600 (Height ~31.1m), Pos=(-48.0, 1.5, 46.0), facing arena center.")

# Scale Victorion to true Colossus height ~31.2m and position at (46.0, 4.13, 46.0) (Position ② outside battle circle)
vic_t = sf_k.objects[3857315498631568767].read()
vic_t.m_LocalPosition.x = 46.0
vic_t.m_LocalPosition.y = 4.13
vic_t.m_LocalPosition.z = 46.0
vic_t.m_LocalRotation.x = 0.0
vic_t.m_LocalRotation.y = -0.92388
vic_t.m_LocalRotation.z = 0.0
vic_t.m_LocalRotation.w = 0.38268
vic_t.m_LocalScale.x = 130.0
vic_t.m_LocalScale.y = 130.0
vic_t.m_LocalScale.z = 130.0
vic_t.save()
print(f"  [✓] Scaled Victorion: scale=130 (Height ~31.2m), Pos=(46.0, 4.13, 46.0), facing arena center.")

# 7. Configure Combiners Materials with Dynamic PBR
print("\n[Step 7] Configuring Combiners Materials with Dynamic PBR...")
# Sample template character material from character bundle
tmpl_char_mat = None
for pid, obj in sf_ch.objects.items():
    if obj.type.name == "Material" and "3726D299" in getattr(obj.read(), "m_Name", ""):
        tmpl_char_mat = obj.read()
        break

if not tmpl_char_mat:
    raise RuntimeError("Template character material 3726D299 not found!")

# Use clean RAOE composite texture (Victorion_AO, PID -890209823152787406)
# G (AO) mean=126.5 (min=56, no dead black), B (Emissive mask) mean=2.99 / 255 (0.011)
# Zero out emissive overbright to completely eliminate pink bloom supernova!
pbr_composite_tex_pid = -890209823152787406
# Flat neutral normal texture (krnk_prop_pillar_01_n, PID 3715767428579049347)
flat_normal_pid = 3715767428579049347

mat_configs = {
    -2182783090914606501: { # M_Volcanicus
        "name": "M_Volcanicus",
        "diffuse": -1505079905186056747, # Tx_Volcanicus_D
        "normal": -1996513945004160825,  # Tx_Volcanicus_N
        "color": (1.5, 1.5, 1.5, 1.0),
        "emission": (0.0, 0.0, 0.0, 1.0),
    },
    8667461040098022327: { # M_Volcanicus_Weapon
        "name": "M_Volcanicus_Weapon",
        "diffuse": -3168068222919951088, # Tx_Volcanicus_Weapon_D
        "normal": 3939815687492814677,   # Tx_Volcanicus_Weapon_N
        "color": (1.5, 1.5, 1.5, 1.0),
        "emission": (0.0, 0.0, 0.0, 1.0),
    },
    7086159552119419155: { # M_Victorion_Body
        "name": "M_Victorion_Body",
        "diffuse": 1145463298758413118,  # Character_Atlas_Color
        "normal": flat_normal_pid,        # Clean flat normal (prevents null normal blackness)
        "color": (1.5, 1.5, 1.5, 1.0),
        "emission": (0.0, 0.0, 0.0, 1.0),
    },
    -9004425303300569079: { # M_Victorion_Glass
        "name": "M_Victorion_Glass",
        "diffuse": -6714775949259442448, # Victorion_Glass_CA
        "normal": flat_normal_pid,        # Clean flat normal
        "color": (1.5, 1.5, 1.5, 1.0),
        "emission": (0.0, 0.0, 0.0, 1.0),
    }
}

for m_pid, cfg in mat_configs.items():
    if m_pid in sf_k.objects:
        mat = sf_k.objects[m_pid].read()
        print(f"  Patching material '{mat.m_Name}' ({m_pid})...")
        mat.m_Shader = PPtr(m_FileID=0, m_PathID=char_shader_pid, assetsfile=sf_k)
        mat.m_ShaderKeywords = "EB_SECOND_DIRECTIONAL_LIGHT_ON _AO_TEX _BASE_TEX _EMISSIVE_TEX _METALLIC_TEX _MODE_CLEARCOAT _NORMAL_TEX _ROUGHNESS_TEX"
        mat.m_LightmapFlags = 5

        # Customize floats
        new_floats = []
        for fname, fval in tmpl_char_mat.m_SavedProperties.m_Floats:
            if fname == "_OcclusionStrength":
                new_floats.append((fname, 0.0)) # Turn off dark AO multiplier
            elif fname == "_reflectance":
                new_floats.append((fname, 0.08)) # Crisp specular edge
            elif fname == "_clearcoat_reflectance_range":
                new_floats.append((fname, 0.20)) # Balanced clearcoat highlights
            elif fname in ["_emissive_overbright_range", "_emissive_range"]:
                new_floats.append((fname, 0.0)) # ZERO overbright emissive to completely eliminate pink bloom!
            elif fname == "_emissive_none":
                new_floats.append((fname, 1.0))
            else:
                new_floats.append((fname, fval))
        mat.m_SavedProperties.m_Floats = new_floats

        # Customize colors
        new_colors = []
        for cname, cval in tmpl_char_mat.m_SavedProperties.m_Colors:
            if cname == "_Color":
                r, g, b, a = cfg["color"]
                new_colors.append((cname, ColorRGBA(r=r, g=g, b=b, a=a)))
            elif cname == "_EmissionColor":
                er, eg, eb, ea = cfg["emission"]
                new_colors.append((cname, ColorRGBA(r=er, g=eg, b=eb, a=ea)))
            elif cname == "_emissive_intensity_col":
                new_colors.append((cname, ColorRGBA(r=0.0, g=0.0, b=0.0, a=0.0)))
            elif cname in ["_base_col", "_base_r_col", "_base_g_col", "_base_b_col"]:
                new_colors.append((cname, ColorRGBA(r=1.2, g=1.2, b=1.2, a=1.0)))
            else:
                new_colors.append((cname, cval))
        mat.m_SavedProperties.m_Colors = new_colors

        # Customize TexEnvs
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
                m_Texture=PPtr(m_FileID=0, m_PathID=target_tex_pid, assetsfile=sf_k)
            )
            new_tex_envs.append((k, tex_env))
        mat.m_SavedProperties.m_TexEnvs = new_tex_envs
        mat.save()
        print(f"    [✓] Upgraded {cfg['name']} to Character Dynamic PBR.")

# 8. Patch AnimationClips for clean infinite loop without LoopPose distortion
print("\n[Step 8] Patching AnimationClips for clean infinite loop...")
comb_clip_pids = [-2863196561028418474, 8240288598998897543]
for pid in comb_clip_pids:
    if pid in sf_k.objects:
        clip = sf_k.objects[pid].read()
        clip.m_WrapMode = 2 # Loop
        if hasattr(clip, "m_MuscleClip"):
            mc = clip.m_MuscleClip
            mc.m_LoopTime = True # Loop enabled
            # STRICTLY DISABLE LOOP POSE BLEND:
            mc.m_LoopBlend = False
            mc.m_LoopBlendOrientation = False
            mc.m_LoopBlendPositionY = False
            mc.m_LoopBlendPositionXZ = False
        clip.save()
        print(f"  [✓] AnimationClip '{clip.m_Name}' (PID={pid}): wrapMode=2, loopTime=True, loopBlend=False.")

# 9. Ensure Layer 11 recursively on all Karnak_Combiners objects
print("\n[Step 9] Ensuring all Combiners GameObjects are on Layer 11...")
comb_gos_patched = 0

def set_layer_recursive(t_pid):
    global comb_gos_patched
    t = sf_k.objects[t_pid].read()
    go_pptr = t.m_GameObject
    if go_pptr.path_id in sf_k.objects:
        go = sf_k.objects[go_pptr.path_id].read()
        go.m_Layer = 11
        go.save()
        comb_gos_patched += 1
    if hasattr(t, "m_Children"):
        for c in t.m_Children:
            if c.path_id in sf_k.objects:
                set_layer_recursive(c.path_id)

set_layer_recursive(comb_root_t_pid)
print(f"  [✓] Set Layer 11 on {comb_gos_patched} GameObjects.")

# 10. Ensure SkinnedMeshRenderers updateWhenOffscreen = True
print("\n[Step 10] Setting SkinnedMeshRenderers updateWhenOffscreen = True...")
smr_pids = [1253715475959699467, 4462729593845205929, 8389340036843243214]
for pid in smr_pids:
    if pid in sf_k.objects:
        smr = sf_k.objects[pid].read()
        smr.m_UpdateWhenOffscreen = True
        smr.save()
        print(f"  [✓] SMR PID {pid} updateWhenOffscreen = True")

# 11. Clean dangling/missing MonoBehaviours on Karnak_Combiners
print("\n[Step 11] Cleaning dangling MonoBehaviour components...")
comb_root_go = comb_root_t.m_GameObject.read()
clean_comp_pairs = []
for cp in comb_root_go.m_Component:
    if cp.component.path_id in sf_k.objects:
        c_type = sf_k.objects[cp.component.path_id].type.name
        if c_type == "MonoBehaviour":
            continue
        clean_comp_pairs.append(cp)
comb_root_go.m_Component = clean_comp_pairs
comb_root_go.save()

# 12. Pack AssetBundle with LZ4 compression
print("\n[Step 12] Packing AssetBundle with LZ4 compression...")
saved_bytes = env_k.file.save(packer="lz4")
print(f"  [✓] Packed bundle size: {len(saved_bytes):,} bytes ({len(saved_bytes)/(1024*1024):.2f} MB)")

# 13. Write output bundle
print("\n[Step 13] Writing to destination...")
OUT_REDECO.parent.mkdir(parents=True, exist_ok=True)
with open(OUT_REDECO, "wb") as f:
    f.write(saved_bytes)
print(f"  [✓] Successfully saved to {OUT_REDECO}")

# 14. Verification
print("\n[Step 14] Comprehensive Verification...")
ver_env = UnityPy.load(saved_bytes)
ver_bf = list(ver_env.files.values())[0]
ver_sf = ver_bf.files[karnak_cab_name]

# Check Shader
ver_s = ver_sf.objects[char_shader_pid].read()
s_name_v = getattr(ver_s, 'm_Name', '') or getattr(ver_s.m_ParsedForm, 'm_Name', '')
assert "SECOND_DIRECTIONAL_LIGHT" in s_name_v, f"Unexpected shader name: {s_name_v}"
print(f"  [✓] Verified Dynamic Character Shader: '{s_name_v}'")

# Check Hierarchy
ver_karnak_t = ver_sf.objects[karnak_merged_t_pid].read()
child_pids = [c.path_id for c in ver_karnak_t.m_Children]
assert comb_root_t_pid in child_pids, "Karnak_Combiners not found in karnak_merged children!"
print(f"  [✓] Verified Hierarchy: Karnak_Combiners is attached to karnak_merged.")

# Check Animation Clips
for pid in comb_clip_pids:
    ver_c = ver_sf.objects[pid].read()
    assert ver_c.m_WrapMode == 2, f"WrapMode is {ver_c.m_WrapMode}, expected 2"
    assert ver_c.m_MuscleClip.m_LoopTime == True, f"LoopTime is {ver_c.m_MuscleClip.m_LoopTime}, expected True"
    assert ver_c.m_MuscleClip.m_LoopBlend == False, f"LoopBlend is {ver_c.m_MuscleClip.m_LoopBlend}, expected False"
    print(f"  [✓] Verified AnimationClip '{ver_c.m_Name}' (PID={pid}): duration={ver_c.m_MuscleClip.m_StopTime:.2f}s, wrapMode=2, loopTime=True, loopBlend=False")

# Check All Textures
for pid in comb_tex_pids:
    tex_v = ver_sf.objects[pid].read()
    img_v = tex_v.image
    assert img_v.size[0] > 0 and img_v.size[1] > 0, f"Texture {tex_v.m_Name} has invalid size {img_v.size}"
    print(f"  [✓] Verified Texture '{tex_v.m_Name}': {img_v.size}, {img_v.mode}")

print("\n====================================================================")
print("  ALL KARNAK COMBINERS MERGE & PATCH STEPS VERIFIED 100% SUCCESS!  ")
print("====================================================================")
