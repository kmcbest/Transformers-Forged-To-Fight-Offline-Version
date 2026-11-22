import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
import zipfile
import tempfile
import os

# 1. Load source VH_Vortex_SKEL.001.dmx AND prepared cha_vortex_gs_01
bpy.ops.wm.read_factory_settings(use_empty=True)
with zipfile.ZipFile(r"O:\agent\transformers-fall-of-cybertron-combaticons.zip", "r") as z:
    tmp_dir = tempfile.mkdtemp()
    fbx_name = "source/transformers fall of cybertron convaticons .fbx"
    z.extract(fbx_name, tmp_dir)
    bpy.ops.import_scene.fbx(filepath=os.path.join(tmp_dir, fbx_name))

src = bpy.data.objects.get("VH_Vortex_SKEL.001.dmx")
sm = src.data
suv = sm.uv_layers.active

# Check front windshield / cockpit area (in Blender FBX: nose is +X, X in [0.2..2.5], |Y|<1.0, Z in [1.2..2.6])
print("=== Source VH_Vortex_SKEL.001.dmx Front Windshield/Cockpit Polygons (X in [0.2..2.5], Z > 1.4) ===")
mat_counts = {}
for p in sm.polygons:
    if 0.2 < p.center.x < 2.5 and p.center.z > 1.4 and abs(p.center.y) < 1.0:
        mi = p.material_index
        mname = sm.materials[mi].name
        mat_counts[mname] = mat_counts.get(mname, 0) + 1
print("Material breakdown in cockpit front region:", mat_counts)

# Print UV samples for Mat[1] (VH_VortexBase_MAT) vs Mat[2] (TR_Test_Mat_INST) in cockpit front
for target_mat in ["VH_VortexBase_MAT", "TR_Test_Mat_INST"]:
    print(f"\nSample polys of '{target_mat}' in cockpit front:")
    shown = 0
    for p in sm.polygons:
        if sm.materials[p.material_index].name == target_mat and 0.2 < p.center.x < 2.5 and p.center.z > 1.4:
            uvs = [(round(suv.data[li].uv.x, 3), round(suv.data[li].uv.y, 3)) for li in p.loop_indices]
            print(f"  Poly {p.index}: center=({p.center.x:.2f},{p.center.y:.2f},{p.center.z:.2f}), n=({p.normal.x:.2f},{p.normal.y:.2f},{p.normal.z:.2f}), uvs={uvs}")
            shown += 1
            if shown >= 12:
                break

# Check how vortex_vh_prepared.fbx compares on polygons 0..20 and 440..460
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Vortex\vortex_vh_prepared.fbx")
prep = bpy.data.objects.get("cha_vortex_gs_01")
pm = prep.data
puv = pm.uv_layers.active
print(f"\n=== Prepared cha_vortex_gs_01 vs Source VH_Vortex_SKEL.001.dmx ===")
print(f"Source polys: {len(sm.polygons)}? Wait already cleared. Comparing polys 440..450:")
for idx in [0, 4, 445, 446, 447, 448, 500]:
    p = pm.polygons[idx]
    uvs = [(round(puv.data[li].uv.x, 3), round(puv.data[li].uv.y, 3)) for li in p.loop_indices]
    print(f"  Prep Poly {idx}: center=({p.center.x:.2f},{p.center.y:.2f},{p.center.z:.2f}), uvs={uvs}")
