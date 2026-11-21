import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path
from mathutils import Quaternion, Vector, Euler
import math

FBX_SRC = Path("e:/Agent/TFTF-blender/3rd-party-models/swoop/01_master/Swoop_pbr.fbx")
OUT_IMG = Path("e:/Agent/TFTF-blender/renders/swoop/preview_hands_curl.png")
OUT_IMG.parent.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_SRC))

arm = bpy.data.objects.get("Bip001")
mesh = bpy.data.objects.get("Swoop.001")

arm.animation_data_clear()
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='POSE')
bpy.ops.pose.select_all(action='SELECT')
bpy.ops.pose.transforms_clear()

# Standard combat fist curling quaternions
finger_quats = {
    # Left hand: tight combat fist from attack01 / idle01
    'Bone_L_Finger0': (0.996808, 0.001097, -0.078611, -0.013909),
    'Bone_L_Finger01': (0.997442, -0.000001, 0.000000, 0.071480),
    'Bone_L_Finger02': (0.979345, -0.000001, -0.000001, 0.202198),
    'Bone_L_Finger1': (0.930682, -0.002064, -0.000110, 0.365824),
    'Bone_L_Finger11': (0.932585, -0.000141, -0.000004, 0.360950),
    'Bone_L_Finger12': (0.918953, 0.000194, -0.000036, 0.394366),
    'Bone_L_Finger2': (0.932293, -0.002034, -0.000154, 0.361697),
    'Bone_L_Finger21': (0.907342, 0.000050, 0.000003, 0.420392),
    'Bone_L_Finger22': (0.886585, -0.000000, 0.000000, 0.462565),
    
    # Right hand: tight combat fist
    'Bone_R_Finger0': (0.997871, 0.053770, -0.036849, 0.001986),
    'Bone_R_Finger01': (0.998401, 0.000000, 0.000000, 0.056523),
    'Bone_R_Finger02': (0.979345, 0.000000, 0.000000, 0.202198), # lock thumb
    'Bone_R_Finger1': (0.930682, -0.001720, -0.000150, 0.365824),
    'Bone_R_Finger11': (0.932585, 0.000130, -0.000000, 0.360950),
    'Bone_R_Finger12': (0.918953, 0.000027, -0.000005, 0.394366), # curl index tip
    'Bone_R_Finger2': (0.911139, -0.002332, -0.000189, 0.412092),
    'Bone_R_Finger21': (0.909270, 0.000092, 0.000001, 0.416206),
    'Bone_R_Finger22': (0.898111, -0.000071, -0.000001, 0.439770),
}

for bname, q in finger_quats.items():
    pb = arm.pose.bones.get(bname)
    if pb:
        pb.rotation_mode = 'QUATERNION'
        pb.rotation_quaternion = Quaternion(q)

bpy.ops.object.mode_set(mode='OBJECT')

# Set camera focused on hands
cam_data = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_data)
bpy.context.scene.collection.objects.link(cam)
bpy.context.scene.camera = cam

# Set camera to view both hands from front
cam.location = Vector((0.0, -1.5, -0.3))
cam.rotation_euler = Euler((math.radians(90), 0, 0), 'XYZ')

# Add sun light
light_data = bpy.data.lights.new(name="Sun", type='SUN')
light = bpy.data.objects.new(name="Sun", object_data=light_data)
bpy.context.scene.collection.objects.link(light)
light.location = Vector((0, -2, 2))
light_data.energy = 3.0

bpy.context.scene.render.resolution_x = 1024
bpy.context.scene.render.resolution_y = 512
bpy.context.scene.render.image_settings.file_format = 'PNG'
bpy.context.scene.render.filepath = str(OUT_IMG)

bpy.ops.render.render(write_still=True)
print(f"Rendered hands preview to {OUT_IMG}")
