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
    
    cls = "GREEN"
    
    # 3D spatial classification matching Toxitron reference
    if cy < 1.35:
        cls = "PURPLE" # Feet / toes
    elif cy < 4.4:
        if abs(cz) < 0.2 and abs(cx) < 0.6:
            cls = "SILVER" # Knee hydraulics
        else:
            cls = "GREEN" # Lower leg shins
    elif cy < 5.85 and abs(cx) < 1.6:
        cls = "SILVER" # Thighs
    elif cy < 6.85 and abs(cx) < 1.2:
        cls = "PURPLE" # Pelvis / groin
    elif cy < 7.7 and abs(cx) < 1.1:
        cls = "SILVER" # Abdomen grill / midriff
    elif cy >= 9.1 and abs(cx) < 1.1:
        # Head
        if cy > 9.6 and abs(cx) < 0.35 and cz > 0.4:
            cls = "YELLOW" # Optics / Crest
        else:
            cls = "PURPLE" # Helmet / faceplate
    elif cy >= 7.7 and cy < 9.1 and abs(cx) < 1.8:
        # Windshield
        if cz > 0.55 and abs(cx) < 1.1 and cy > 8.0:
            cls = "RED" # Chest windshield
        else:
            cls = "GREEN" # Cab chest armor
    else:
        # Arms
        if abs(cx) > 2.2 and cy < 5.8:
            cls = "PURPLE" # Hands
        elif abs(cx) > 1.8 and cy < 7.6:
            cls = "GREEN" # Forearms
        elif cy > 8.8 and abs(cx) > 1.3 and cz < 0.0:
            cls = "PURPLE" # Smokestacks
        else:
            cls = "GREEN" # Shoulders

    uvs = [[uv_layer[li].uv.x, uv_layer[li].uv.y] for li in poly.loop_indices]
    data.append({"cls": cls, "uvs": uvs})

out_json = r"E:\Agent\TFTF-blender\tools\mesh_poly_uvs.json"
with open(out_json, "w") as f:
    json.dump(data, f)

print(f"Exported {len(data)} polygons to {out_json}")
