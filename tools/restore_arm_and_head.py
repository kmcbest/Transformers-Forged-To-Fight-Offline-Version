import bpy
import mathutils
import math
from pathlib import Path

ROOT = Path("tools/demolishor")
BLEND_PATH = ROOT / "demolishor_phase2_inspect.blend"
SOURCE_FBX = Path("3rd-party-models/transformers-fall-of-cybertron-demolishor/source/transformers fall of cybertron Demolishor.fbx").resolve()

bpy.ops.wm.open_mainfile(filepath=str(BLEND_PATH))

mesh = bpy.data.objects.get("cha_demolishor_gs_01")
arm = bpy.data.objects.get("Ironhide_Reference_Armature")

print("=== 1. Restoring Natural Head Position ===")
# Head was shifted up by +0.36 Z and +0.24 Y in v5
head_vgs = [vg.index for vg in mesh.vertex_groups if any(k in vg.name.lower() for k in ["head", "face", "jaw"])]
head_verts = [v for v in mesh.data.vertices if any(g.group in head_vgs for g in v.groups)]
print(f"Lowering {len(head_verts)} head vertices back into neck socket...")
for v in head_verts:
    v.co.z -= 0.35
    v.co.y -= 0.20

mesh.data.update()

print("=== 2. Importing Missing Right Forearm Armor (CP_DemolishorArm) ===")
# Import CP arm from original FBX
bpy.ops.import_scene.fbx(filepath=str(SOURCE_FBX))
cp_mesh = bpy.data.objects.get("CP_DemolishorArm_SKEL.mo.dmx")
if not cp_mesh:
    print("[!] Error: CP_DemolishorArm not found in FBX!")
else:
    print(f"[✓] Found CP_DemolishorArm with {len(cp_mesh.data.vertices)} vertices")
    
    # Remove all extra imported objects
    for obj in list(bpy.data.objects):
        if obj not in [mesh, arm, cp_mesh] and obj.name != "Ironhide_Ghost_Reference" and obj.type in ['ARMATURE', 'MESH']:
            bpy.data.objects.remove(obj, do_unlink=True)
            
    # Unparent and clear modifiers
    cp_mesh.parent = None
    cp_mesh.modifiers.clear()
    
    # Step A: Scale 1.775 and Rotate +90 deg around Z
    cp_mesh.scale = (1.775, 1.775, 1.775)
    cp_mesh.rotation_euler = (0, 0, math.radians(90))
    bpy.context.view_layer.objects.active = cp_mesh
    bpy.ops.object.select_all(action='DESELECT')
    cp_mesh.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    
    # Step B: Apply Arm Angle (18 deg Y around r_shoulder_pivot) + 0.30 Z lift
    r_shoulder_pivot = mathutils.Vector(( 2.50, -0.35, 7.15))
    rot_r_arm = mathutils.Matrix.Rotation(math.radians( 18.0), 4, 'Y')
    
    for v in cp_mesh.data.vertices:
        v.co = r_shoulder_pivot + (rot_r_arm @ (v.co - r_shoulder_pivot))
        v.co.z += 0.30
        
    cp_mesh.data.update()
    
    # Assign material from mesh
    if mesh.data.materials:
        cp_mesh.data.materials.clear()
        cp_mesh.data.materials.append(mesh.data.materials[0])
        
    # Map all vertex groups of CP to "RightForeArm" with 1.0 weight
    cp_mesh.vertex_groups.clear()
    r_fa_vg = cp_mesh.vertex_groups.new(name="RightForeArm")
    r_fa_vg.add(list(range(len(cp_mesh.data.vertices))), 1.0, 'REPLACE')
    
    # Ensure mesh is active, select both and JOIN!
    bpy.ops.object.select_all(action='DESELECT')
    mesh.select_set(True)
    cp_mesh.select_set(True)
    bpy.context.view_layer.objects.active = mesh
    bpy.ops.object.join()
    print("[✓] Successfully joined Right Forearm Armor to Demolishor!")

# Re-link armature modifier
mesh = bpy.context.view_layer.objects.active
for m in mesh.modifiers:
    if m.type == 'ARMATURE':
        m.object = arm

bpy.context.scene.frame_current = 0
bpy.ops.wm.save_mainfile(filepath=str(BLEND_PATH))
print(f"[✓] Saved updated blend file to {BLEND_PATH}")
