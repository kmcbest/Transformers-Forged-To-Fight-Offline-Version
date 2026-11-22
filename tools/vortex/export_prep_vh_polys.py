import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy, zipfile, tempfile, os, json

# 1. Export Source poly 3D centers + UVs + mat_idx
bpy.ops.wm.read_factory_settings(use_empty=True)
with zipfile.ZipFile(r"O:\agent\transformers-fall-of-cybertron-combaticons.zip", "r") as z:
    tmp_dir = tempfile.mkdtemp()
    fbx_name = "source/transformers fall of cybertron convaticons .fbx"
    z.extract(fbx_name, tmp_dir)
    bpy.ops.import_scene.fbx(filepath=os.path.join(tmp_dir, fbx_name))

src = bpy.data.objects.get("VH_Vortex_SKEL.001.dmx")
sm = src.data
suv = sm.uv_layers.active

# Prepared vortex_vh_prepared.fbx has the exact same polygon order as Source (checked: 0 loop UV diff!)
# AND prepared is ALREADY scaled/oriented to TFTF space! Let's export prepared poly centers & source mat_idx!
src_mats = [p.material_index for p in sm.polygons]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Vortex\vortex_vh_prepared.fbx")
prep = bpy.data.objects.get("cha_vortex_gs_01")
pm = prep.data
puv = pm.uv_layers.active

prep_data = []
for p in pm.polygons:
    c = p.center
    # Blender (x, y, z) -> Unity (-x, z, -y) or (x, z, y)? Check v171!
    # Prep v6329 (Logo): (0.8307, 1.2642, 3.3288) -> HEAD v171: (0.8665, 3.3918, 1.2602)!
    # Notice: Unity X ≈ Prep X + 0.036, Unity Y ≈ Prep Z + 0.063, Unity Z ≈ Prep Y - 0.004!
    prep_data.append({
        "idx": p.index,
        "mat_idx": src_mats[p.index],
        "center": [float(c.x), float(c.y), float(c.z)],
        "uvs": [[float(puv.data[li].uv.x), float(puv.data[li].uv.y)] for li in p.loop_indices],
    })

with open(r"e:\Agent\TFTF-blender\tools\vortex\diag\prep_vh_polys.json", "w", encoding="utf-8") as f:
    json.dump(prep_data, f)
print(f"Exported {len(prep_data)} prepared polys with source mat_idx!")
