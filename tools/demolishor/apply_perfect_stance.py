# -*- coding: utf-8 -*-
"""
Perfect Stance Alignment:
1. Fixes the "Marilyn Monroe" knock-knees:
   Removes artificial inward leg rotation, aligns legs in a powerful,
   straight vertical column centered at X = +/- 0.77 directly enclosing
   Ironhide's knee and ankle bone axes.
2. Fine-tunes hands to match the red circled finger bones at X = +/- 2.28 down to the millimeter.
3. 100% rigid re-weighting with strict anatomical domain filtering.
4. Injects full 80-frame athletic running cycle for visual quality inspection.
"""
import sys
import bpy
import mathutils
import math
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parent.parent.parent
PHASE1_BLEND = ROOT / "tools" / "demolishor" / "demolishor_phase1.blend"
OUTPUT_BLEND = ROOT / "tools" / "demolishor" / "demolishor_phase2_inspect.blend"

print("=== Executing Perfect Stance & Knee Centering ===")
# Start from pristine baseline in phase1
bpy.ops.wm.open_mainfile(filepath=str(PHASE1_BLEND))

mesh = bpy.data.objects.get("RB_DemolishorWeaponArm_SKEL.mo.dmx") or bpy.data.objects.get("cha_demolishor_gs_01")
arm = bpy.data.objects.get("Ironhide_Reference_Armature")

if not mesh or not arm:
    print("[!] Mesh or Armature not found!")
    sys.exit(1)

# Ensure transforms applied
bpy.context.view_layer.objects.active = mesh
bpy.ops.object.select_all(action='DESELECT')
mesh.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# 1. Clean extra vehicle objects
to_remove = ["Demolishor_ARM", "Demolishor_VH_ARM", "VH_Demolishor_SKEL.mo.dmx", "CP_DemolishorArm_SKEL.mo.dmx"]
for name in to_remove:
    obj = bpy.data.objects.get(name)
    if obj: bpy.data.objects.remove(obj, do_unlink=True)

# 2. Fix Ironhide Ghost Reference rotation
ghost = bpy.data.objects.get("Ironhide_Ghost_Reference") or bpy.data.objects.get("ironhide")
if ghost:
    ghost.rotation_euler = (0, 0, 0)
    bpy.context.view_layer.objects.active = ghost
    bpy.ops.object.select_all(action='DESELECT')
    ghost.select_set(True)
    bpy.ops.object.transform_apply(rotation=True)

# 3. Identify limb vertex groups
l_arm_vgs = [vg.index for vg in mesh.vertex_groups if any(k in vg.name for k in ["L_Arm02", "L_Arm03", "L_Arm04", "L_Elbow", "L_Finger"])]
r_arm_vgs = [vg.index for vg in mesh.vertex_groups if any(k in vg.name for k in ["R_Arm02", "R_Arm03", "R_Arm04", "R_Elbow", "R_Finger"])]
l_leg_vgs = [vg.index for vg in mesh.vertex_groups if any(k in vg.name for k in ["L_Leg", "L_Thigh", "L_Knee", "L_Toe", "L_Ankle"])]
r_leg_vgs = [vg.index for vg in mesh.vertex_groups if any(k in vg.name for k in ["R_Leg", "R_Thigh", "R_Knee", "R_Toe", "R_Ankle"])]

# 4. ARM ROTATION & CENTERING
# Rotate arms downward around shoulder to hang naturally
l_shoulder_pivot = mathutils.Vector((-2.50, -0.35, 7.15))
r_shoulder_pivot = mathutils.Vector(( 2.50, -0.35, 7.15))
arm_angle = 24.0 # degrees

rot_l_arm = mathutils.Matrix.Rotation(math.radians(-arm_angle), 4, 'Y')
rot_r_arm = mathutils.Matrix.Rotation(math.radians( arm_angle), 4, 'Y')

for v in mesh.data.vertices:
    if v.co.z <= 7.80:
        if any(g.group in l_arm_vgs and g.weight > 0.25 for g in v.groups):
            v.co = l_shoulder_pivot + (rot_l_arm @ (v.co - l_shoulder_pivot))
        elif any(g.group in r_arm_vgs and g.weight > 0.25 for g in v.groups):
            v.co = r_shoulder_pivot + (rot_r_arm @ (v.co - r_shoulder_pivot))

# Measure current hand center
l_hand_pts = [v.co for v in mesh.data.vertices if v.co.z < 5.4 and any(g.group in l_arm_vgs and g.weight > 0.4 for g in v.groups)]
if l_hand_pts:
    c_hand_x = sum(p.x for p in l_hand_pts) / len(l_hand_pts)
    # Target is -2.28
    arm_shift = -2.28 - c_hand_x
    print(f"[*] Arm hand current X: {c_hand_x:.2f}m -> Target -2.28m (Shifting arms inward by {arm_shift:.2f}m)...")
    for v in mesh.data.vertices:
        if v.co.z <= 7.80:
            if any(g.group in l_arm_vgs and g.weight > 0.25 for g in v.groups):
                v.co.x += arm_shift
                v.co.z += 0.35 # slight lift so palm encloses hand bone
            elif any(g.group in r_arm_vgs and g.weight > 0.25 for g in v.groups):
                v.co.x -= arm_shift
                v.co.z += 0.35

# 5. STRAIGHT POWERFUL LEG CENTERING (NO INWARD ROTATION, STRAIGHT COLUMN)
# Measure current knee centroid
l_knee_pts = [v.co for v in mesh.data.vertices if any(g.group in l_leg_vgs and g.weight > 0.3 for g in v.groups and "Knee" in mesh.vertex_groups[g.group].name)]
if not l_knee_pts:
    l_knee_pts = [v.co for v in mesh.data.vertices if 2.0 < v.co.z < 3.5 and any(g.group in l_leg_vgs and g.weight > 0.3 for g in v.groups)]

c_knee_x = sum(p.x for p in l_knee_pts) / len(l_knee_pts)
# Target Ironhide Knee bone is at X = -0.77
leg_shift = -0.77 - c_knee_x
print(f"[*] Knee current X: {c_knee_x:.2f}m -> Target Ironhide Knee bone X: -0.77m")
print(f"[*] Applying straight parallel shift of {leg_shift:.2f}m to legs (No knock-knees!)...")

for v in mesh.data.vertices:
    if v.co.z <= 5.00:
        if any(g.group in l_leg_vgs and g.weight > 0.25 for g in v.groups):
            v.co.x += leg_shift
        elif any(g.group in r_leg_vgs and g.weight > 0.25 for g in v.groups):
            v.co.x -= leg_shift

# Re-ground soles to Z = 0
min_z = min(v.co.z for v in mesh.data.vertices)
for v in mesh.data.vertices:
    v.co.z -= min_z
mesh.data.update()

# Measure final alignment metrics
vg_names = {vg.index: vg.name for vg in mesh.vertex_groups}
l_hand = [v.co for v in mesh.data.vertices if v.co.z < 5.4 and any(g.group in l_arm_vgs and g.weight > 0.4 for g in v.groups)]
r_hand = [v.co for v in mesh.data.vertices if v.co.z < 5.4 and any(g.group in r_arm_vgs and g.weight > 0.4 for g in v.groups)]
l_knee = [v.co for v in mesh.data.vertices if 2.0 < v.co.z < 3.5 and any(g.group in l_leg_vgs and g.weight > 0.4 for g in v.groups)]
r_knee = [v.co for v in mesh.data.vertices if 2.0 < v.co.z < 3.5 and any(g.group in r_leg_vgs and g.weight > 0.4 for g in v.groups)]
l_foot = [v.co for v in mesh.data.vertices if v.co.z < 1.2 and any(g.group in l_leg_vgs and g.weight > 0.4 for g in v.groups)]
r_foot = [v.co for v in mesh.data.vertices if v.co.z < 1.2 and any(g.group in r_leg_vgs and g.weight > 0.4 for g in v.groups)]

print("\n--- Perfect Stance Alignment Metrics vs Ironhide Bones ---")
if l_hand and r_hand:
    c_hl = sum(l_hand, mathutils.Vector()) / len(l_hand)
    c_hr = sum(r_hand, mathutils.Vector()) / len(r_hand)
    print(f"  Left Hand  : (X={c_hl.x:6.2f}, Z={c_hl.z:6.2f}) | Target Ironhide Hand Bone: (X= -2.28, Z= 5.09)")
    print(f"  Right Hand : (X={c_hr.x:6.2f}, Z={c_hr.z:6.2f}) | Target Ironhide Hand Bone: (X=  2.28, Z= 5.09)")
if l_knee and r_knee:
    c_kl = sum(l_knee, mathutils.Vector()) / len(l_knee)
    c_kr = sum(r_knee, mathutils.Vector()) / len(r_knee)
    print(f"  Left Knee  : (X={c_kl.x:6.2f}, Z={c_kl.z:6.2f}) | Target Ironhide Knee Bone: (X= -0.77, Z= 4.10)")
    print(f"  Right Knee : (X={c_kr.x:6.2f}, Z={c_kr.z:6.2f}) | Target Ironhide Knee Bone: (X=  0.77, Z= 4.10)")
if l_foot and r_foot:
    c_fl = sum(l_foot, mathutils.Vector()) / len(l_foot)
    c_fr = sum(r_foot, mathutils.Vector()) / len(r_foot)
    print(f"  Left Foot  : (X={c_fl.x:6.2f})           | Target Ironhide Foot Bone: (X= -0.77)")
    print(f"  Right Foot : (X={c_fr.x:6.2f})           | Target Ironhide Foot Bone: (X=  0.77)")

# 6. SEPARATE AND RIGID BIND WITH STRICT ANATOMY
bone_segments = {}
for b in arm.pose.bones:
    h = arm.matrix_world @ b.head
    t = arm.matrix_world @ b.tail
    bone_segments[b.name] = (h, t)

bpy.ops.mesh.separate(type='LOOSE')
parts = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH' and obj.name != "Ironhide_Ghost_Reference"]
print(f"\n[*] Separated into {len(parts)} mechanical parts")

def get_part_dominant_orig_vg(part):
    counts = {}
    for v in part.data.vertices:
        for g in v.groups:
            orig_name = vg_names.get(g.group)
            if orig_name and g.weight > 0.1:
                counts[orig_name] = counts.get(orig_name, 0.0) + g.weight
    if not counts: return "Unknown"
    return max(counts.items(), key=lambda kv: kv[1])[0]

def get_candidate_bones(orig_vg):
    if "L_Finger" in orig_vg or "L_Arm04" in orig_vg:
        return ["LeftHand"]
    if "L_Arm03" in orig_vg or "L_Elbow" in orig_vg:
        return ["LeftForeArm", "LeftArm"]
    if "L_Arm02" in orig_vg or "L_Shoulder" in orig_vg:
        return ["LeftArm", "LeftShoulder", "LeftShoulderPad"]
    if "L_Arm01" in orig_vg or "L_Clav" in orig_vg:
        return ["LeftShoulder", "Spine1"]
        
    if "R_Finger" in orig_vg or "R_Arm04" in orig_vg:
        return ["RightHand"]
    if "R_Arm03" in orig_vg or "R_Elbow" in orig_vg:
        return ["RightForeArm", "RightArm"]
    if "R_Arm02" in orig_vg or "R_Shoulder" in orig_vg:
        return ["RightArm", "RightShoulder", "RightShoulderPad"]
    if "R_Arm01" in orig_vg or "R_Clav" in orig_vg:
        return ["RightShoulder", "Spine1"]
        
    if "L_Leg04" in orig_vg or "L_Toe" in orig_vg:
        return ["LeftFoot", "LeftToeBase"]
    if "L_Leg03" in orig_vg or "L_Ankle" in orig_vg:
        return ["LeftFoot", "LeftLeg"]
    if "L_Leg02" in orig_vg or "L_Knee" in orig_vg:
        return ["LeftLeg", "LeftUpLeg"]
    if "L_Leg01" in orig_vg or "L_Thigh" in orig_vg:
        return ["LeftUpLeg"]
        
    if "R_Leg04" in orig_vg or "R_Toe" in orig_vg:
        return ["RightFoot", "RightToeBase"]
    if "R_Leg03" in orig_vg or "R_Ankle" in orig_vg:
        return ["RightFoot", "RightLeg"]
    if "R_Leg02" in orig_vg or "R_Knee" in orig_vg:
        return ["RightLeg", "RightUpLeg"]
    if "R_Leg01" in orig_vg or "R_Thigh" in orig_vg:
        return ["RightUpLeg"]
        
    if any(k in orig_vg for k in ["Head", "Neck", "Face"]):
        return ["Head", "Neck"]
    if any(k in orig_vg for k in ["Spine00", "Hips", "Pelvis"]):
        return ["Hips", "Spine"]
    if any(k in orig_vg for k in ["Spine01", "Spine02", "Lumbar", "Chest"]):
        return ["Spine", "Spine1"]
        
    return list(bone_segments.keys())

for part in parts:
    coords = [v.co for v in part.data.vertices]
    if not coords: continue
    center = part.matrix_world @ (sum(coords, mathutils.Vector()) / len(coords))
    
    orig_vg = get_part_dominant_orig_vg(part)
    candidates = get_candidate_bones(orig_vg)
    
    best_bone = None
    min_dist = float('inf')
    
    for name in candidates:
        if name not in bone_segments: continue
        h, t = bone_segments[name]
        line = t - h
        line_len_sq = line.length_squared
        if line_len_sq < 1e-6:
            dist = (center - h).length
        else:
            pt = center - h
            proj = max(0.0, min(1.0, pt.dot(line) / line_len_sq)) * line
            dist = (pt - proj).length
            
        if dist < min_dist:
            min_dist = dist
            best_bone = name
            
    if not best_bone:
        best_bone = "Hips"
        
    part.vertex_groups.clear()
    vg = part.vertex_groups.new(name=best_bone)
    vg.add([v.index for v in part.data.vertices], 1.0, 'REPLACE')

bpy.ops.object.select_all(action='DESELECT')
for p in parts: p.select_set(True)
bpy.context.view_layer.objects.active = parts[0]
bpy.ops.object.join()

joined_mesh = bpy.context.active_object
joined_mesh.name = "cha_demolishor_gs_01"
joined_mesh.parent = arm

joined_mesh.modifiers.clear()
mod = joined_mesh.modifiers.new(name="Armature", type='ARMATURE')
mod.object = arm
mod.use_vertex_groups = True
print(f"[✓] Re-joined and bound to Armature ({len(joined_mesh.data.vertices)} verts)")

# 7. ATHLETIC RUNNING CYCLE ACTION
print("=== 7. Injecting Athletic Running Cycle Animation ===")
arm.animation_data_clear()
arm.animation_data_create()
act = bpy.data.actions.new(name="TF_Running_Stride_Action")
arm.animation_data.action = act

bpy.context.scene.frame_start = 1
bpy.context.scene.frame_end = 80
bpy.context.scene.frame_current = 1

def add_rot_key(bone_name, frame, euler_deg):
    pb = arm.pose.bones.get(bone_name)
    if not pb: return
    pb.rotation_mode = 'XYZ'
    pb.rotation_euler = mathutils.Euler((math.radians(euler_deg[0]), 
                                         math.radians(euler_deg[1]), 
                                         math.radians(euler_deg[2])), 'XYZ')
    pb.keyframe_insert(data_path="rotation_euler", frame=frame)

run_bones = ["Hips", "Spine", "Spine1", 
             "LeftUpLeg", "LeftLeg", "LeftFoot", 
             "RightUpLeg", "RightLeg", "RightFoot",
             "LeftArm", "LeftForeArm", 
             "RightArm", "RightForeArm"]

for f in [1, 40, 80]:
    for b in run_bones:
        add_rot_key(b, f, (0, 0, 0))

# Frame 20: Left High Knee Stride + Right Back Push
add_rot_key("LeftUpLeg", 20, (40, 0, 0))
add_rot_key("LeftLeg", 20, (-50, 0, 0))
add_rot_key("LeftFoot", 20, (15, 0, 0))
add_rot_key("RightUpLeg", 20, (-35, 0, 0))
add_rot_key("RightLeg", 20, (-10, 0, 0))
add_rot_key("RightFoot", 20, (-20, 0, 0))
add_rot_key("Hips", 20, (5, 0, 0))
add_rot_key("Spine", 20, (8, -10, -5))
add_rot_key("RightArm", 20, (-40, -15, 0))
add_rot_key("RightForeArm", 20, (0, -45, 0))
add_rot_key("LeftArm", 20, (30, 15, 0))
add_rot_key("LeftForeArm", 20, (0, 30, 0))

# Frame 60: Right High Knee Stride + Left Back Push
add_rot_key("RightUpLeg", 60, (40, 0, 0))
add_rot_key("RightLeg", 60, (-50, 0, 0))
add_rot_key("RightFoot", 60, (15, 0, 0))
add_rot_key("LeftUpLeg", 60, (-35, 0, 0))
add_rot_key("LeftLeg", 60, (-10, 0, 0))
add_rot_key("LeftFoot", 60, (-20, 0, 0))
add_rot_key("Hips", 60, (5, 0, 0))
add_rot_key("Spine", 60, (8, 10, 5))
add_rot_key("LeftArm", 60, (-40, 15, 0))
add_rot_key("LeftForeArm", 60, (0, 45, 0))
add_rot_key("RightArm", 60, (30, -15, 0))
add_rot_key("RightForeArm", 60, (0, -30, 0))

print("[✓] 80-frame running cycle animation keyed")

# 8. Embedded GUI Text Block
gui_script_content = '''# -*- coding: utf-8 -*-
import bpy
import os

class TF_OT_ReassignPart(bpy.types.Operator):
    bl_idname = "tf.reassign_part"
    bl_label = "改绑选中的零件到目标骨骼"
    def execute(self, context):
        obj = context.active_object
        target_bone = context.scene.tf_target_bone
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "请先选中网格物体！")
            return {'CANCELLED'}
        if not target_bone:
            self.report({'ERROR'}, "请先在上方下拉框选择目标骨骼！")
            return {'CANCELLED'}
            
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_linked()
        bpy.ops.object.mode_set(mode='OBJECT')
        
        sel = [v.index for v in obj.data.vertices if v.select]
        if not sel:
            self.report({'WARNING'}, "未检测到选中的顶点！")
            return {'CANCELLED'}
            
        for vg in obj.vertex_groups: vg.remove(sel)
        if target_bone not in obj.vertex_groups: obj.vertex_groups.new(name=target_bone)
        obj.vertex_groups[target_bone].add(sel, 1.0, 'REPLACE')
        self.report({'INFO'}, f"成功将 {len(sel)} 个顶点改绑至骨骼: {target_bone}")
        return {'FINISHED'}

class TF_PT_Inspector(bpy.types.Panel):
    bl_label = "TF Mod 动作质检面板"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'TF Tools'
    def draw(self, context):
        layout = self.layout
        box1 = layout.box()
        box1.label(text="1. 奔跑与连招质检", icon='PLAY')
        row = box1.row(align=True)
        row.operator("screen.animation_play", text="播放跑步动作", icon='PLAY')
        row.operator("screen.animation_cancel", text="暂停", icon='PAUSE')
        
        box2 = layout.box()
        box2.label(text="2. 装甲纠偏(点选零件)", icon='WRENCH')
        arm = bpy.data.objects.get("Ironhide_Reference_Armature")
        if arm:
            box2.prop_search(context.scene, "tf_target_bone", arm.data, "bones", text="归属骨骼")
        box2.operator("tf.reassign_part", icon='BONE_DATA')
        
        layout.separator()
        box3 = layout.box()
        box3.label(text="3. 验收确认", icon='CHECKMARK')
        box3.operator("tf.finish_inspection", text="【质检无误，继续打包】", icon='CHECKMARK')

class TF_OT_Finish(bpy.types.Operator):
    bl_idname = "tf.finish_inspection"
    bl_label = "确认继续"
    def execute(self, context):
        flag_file = os.path.join(os.path.expanduser("~"), "tf_pass.flag")
        with open(flag_file, "w", encoding="utf-8") as f:
            f.write("OK")
        self.report({'INFO'}, f"已发出信号 ({flag_file})，AI 接管打包中...")
        return {'FINISHED'}

classes = [TF_OT_ReassignPart, TF_PT_Inspector, TF_OT_Finish]

def register():
    bpy.types.Scene.tf_target_bone = bpy.props.StringProperty(name="目标骨骼")
    for cls in classes:
        try: bpy.utils.register_class(cls)
        except Exception: pass

def unregister():
    for cls in reversed(classes):
        try: bpy.utils.unregister_class(cls)
        except Exception: pass
    if hasattr(bpy.types.Scene, "tf_target_bone"):
        del bpy.types.Scene.tf_target_bone

if __name__ == "__main__":
    register()
'''

tb = bpy.data.texts.get("tf_gui_inspector.py") or bpy.data.texts.new("tf_gui_inspector.py")
tb.clear()
tb.write(gui_script_content)
tb.use_module = True

bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT_BLEND))
print(f"[✓] Saved Perfect Stance scene to: {OUTPUT_BLEND}")
