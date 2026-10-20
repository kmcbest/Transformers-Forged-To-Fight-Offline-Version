import bpy
import json

obj_path = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\OptimusPrime\cha_optimusprime_gs_voyager2015_00.obj"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=obj_path)

obj = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]
mesh = obj.data
uv_layer = mesh.uv_layers.active.data

data = []

for poly in mesh.polygons:
    verts = [mesh.vertices[vi].co for vi in poly.vertices]
    cx = sum(v.x for v in verts) / len(verts)
    cy = sum(v.y for v in verts) / len(verts)
    cz = sum(v.z for v in verts) / len(verts)
    
    region = "OTHER"
    
    # 1. Feet
    if cy < 1.35:
        region = "FEET"
    # 2. Lower legs (shins)
    elif cy < 4.4 and abs(cx) < 1.5:
        region = "SHINS"
    # 3. Thighs
    elif cy < 5.85 and abs(cx) < 1.6:
        region = "THIGHS"
    # 4. Pelvis / Crotch
    elif cy < 6.85 and abs(cx) < 1.3:
        region = "PELVIS"
    # 5. Abdomen / Midriff grill
    elif cy < 7.7 and abs(cx) < 1.2:
        region = "MIDRIFF"
    # 6. Head
    elif cy >= 9.1 and abs(cx) < 1.1:
        if cy > 9.6 and abs(cx) < 0.35 and cz > 0.4:
            region = "EYES"
        else:
            region = "HEAD"
    # 7. Chest
    elif cy >= 7.7 and cy < 9.1 and abs(cx) < 1.8:
        # Windshield vs Cab
        if cz > 0.55 and abs(cx) < 1.1 and cy > 8.0:
            region = "WINDSHIELD"
        else:
            region = "CHEST_CAB"
    # 8. Arms & Shoulders
    else:
        if abs(cx) > 2.2 and cy < 5.8:
            region = "HANDS"
        elif abs(cx) > 1.8 and cy < 7.6:
            region = "FOREARMS"
        elif cy > 8.8 and abs(cx) > 1.3 and cz < 0.0:
            region = "SMOKESTACKS"
        else:
            region = "SHOULDERS"

    uvs = [[uv_layer[li].uv.x, uv_layer[li].uv.y] for li in poly.loop_indices]
    data.append({"region": region, "uvs": uvs})

out_json = r"E:\Agent\TFTF-blender\tools\mesh_poly_regions.json"
with open(out_json, "w") as f:
    json.dump(data, f)

print(f"Exported {len(data)} polygon regions to {out_json}")
