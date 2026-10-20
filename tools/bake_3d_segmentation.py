import bpy
import numpy as np
from PIL import Image, ImageDraw

obj_path = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\OptimusPrime\cha_optimusprime_gs_voyager2015_00.obj"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=obj_path)

obj = [o for o in bpy.context.scene.objects if o.type == 'MESH'][0]
mesh = obj.data

width = 1024
height = 1024

# Create segmentation image
seg_img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
draw = ImageDraw.Draw(seg_img)

uv_layer = mesh.uv_layers.active.data

# Classification colors (R, G, B)
# 1: ACID_GREEN (Chest, Forearms, Lower Legs, Biceps) -> (178, 224, 24)
# 2: POISON_PURPLE (Head, Hands, Feet, Pelvis, Smokestacks) -> (88, 24, 69)
# 3: GUNMETAL_SILVER (Thighs, Midriff, Hydraulics) -> (140, 145, 150)
# 4: WINDSHIELD_RED (Chest windows) -> (180, 20, 20)
# 5: OPTICS_YELLOW (Eyes) -> (255, 230, 0)

poly_classes = {}

for poly in mesh.polygons:
    # 3D centroid of polygon
    verts = [mesh.vertices[vi].co for vi in poly.vertices]
    cx = sum(v.x for v in verts) / len(verts)
    cy = sum(v.y for v in verts) / len(verts)
    cz = sum(v.z for v in verts) / len(verts)
    
    cls = "GREEN" # default
    
    # Feet
    if cy < 1.35:
        cls = "PURPLE" # Feet / toes
    # Lower legs
    elif cy < 4.4:
        # Check if it's the knee joint or back mechanics
        if abs(cz) < 0.2 and abs(cx) < 0.6:
            cls = "SILVER"
        else:
            cls = "GREEN"
    # Thighs
    elif cy < 5.85 and abs(cx) < 1.6:
        cls = "SILVER" # Thighs / inner mechanics
    # Pelvis
    elif cy < 6.85 and abs(cx) < 1.2:
        cls = "PURPLE" # Pelvis / groin
    # Abdomen / Midriff grill
    elif cy < 7.7 and abs(cx) < 1.1:
        cls = "SILVER" # Midriff grill / radiator
    # Head & Neck
    elif cy >= 9.1 and abs(cx) < 1.1:
        if cy > 9.6 and abs(cx) < 0.4 and cz > 0.4:
            cls = "YELLOW" # Optics / Crest
        else:
            cls = "PURPLE" # Helmet / faceplate
    # Chest
    elif cy >= 7.7 and cy < 9.1 and abs(cx) < 1.8:
        # Check if windshield (front facing, positive Z)
        if cz > 0.55 and abs(cx) < 1.1 and cy > 8.0:
            cls = "RED" # Windshield
        else:
            cls = "GREEN" # Cab chest armor
    # Arms / Shoulders
    else:
        # Hands
        if abs(cx) > 2.2 and cy < 5.8:
            cls = "PURPLE" # Hands
        # Forearms
        elif abs(cx) > 1.8 and cy < 7.6:
            cls = "GREEN" # Forearms
        # Shoulders / Smokestacks
        elif cy > 8.8 and abs(cx) > 1.3 and cz < 0.0:
            cls = "PURPLE" # Smokestacks
        else:
            cls = "GREEN" # Shoulders / biceps

    # Get UV polygon coordinates
    uvs = [uv_layer[li].uv for li in poly.loop_indices]
    pts = [(int(round(u * (width - 1))), int(round((1.0 - v) * (height - 1)))) for u, v in uvs]
    
    color_map = {
        "GREEN": (185, 230, 25, 255),
        "PURPLE": (80, 25, 85, 255),
        "SILVER": (145, 150, 155, 255),
        "RED": (180, 20, 25, 255),
        "YELLOW": (255, 225, 0, 255)
    }
    
    if len(pts) >= 3:
        draw.polygon(pts, fill=color_map[cls])

out_mask = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Toxitron\toxitron_3d_segmentation.png"
seg_img.save(out_mask)
print(f"Successfully baked 3D segmentation map to {out_mask}")
