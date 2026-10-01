# -*- coding: utf-8 -*-
"""
Phase 2 & Phase 2.5: Rigid Weighting Algorithm & Dynamic Inspection GUI.
Implements the exact SOP from 《硬表面角色“借壳”绑定与自动化打包管线SKILL.html》:
1. Separate mesh into LOOSE parts.
2. Centroid distance to bone line segment projection -> 100% rigid weight assignment.
3. Re-join parts, mount Armature modifier.
4. Inject test animation action (dynamic combat motion test).
5. Inject interactive GUI: TF Tools sidebar (animation play/pause, part reassign, pass flag).
"""
import sys
import os
from pathlib import Path
import bpy
from mathutils import Vector, Euler
import math

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parent.parent
DEMO_DIR = ROOT / "tools" / "demolishor"
INPUT_BLEND = DEMO_DIR / "demolishor_phase1.blend"
OUTPUT_BLEND = DEMO_DIR / "demolishor_phase2_inspect.blend"

print("=== Phase 2: Rigid Weighting & GUI Injection ===")
bpy.ops.wm.open_mainfile(filepath=str(INPUT_BLEND))

arm_obj = bpy.data.objects.get("Ironhide_Reference_Armature")
if not arm_obj:
    print("[!] Ironhide_Reference_Armature not found!")
    sys.exit(1)

# Find target mesh: prefer object with 'RB_' or largest vertex count (excluding ghost reference)
mesh_objs = [o for o in bpy.data.objects if o.type == 'MESH' and o.name != "Ironhide_Ghost_Reference"]
# Sort by vertex count descending
mesh_objs.sort(key=lambda o: len(o.data.vertices), reverse=True)

if not mesh_objs:
    print("[!] Target mesh not found!")
    sys.exit(1)

target_mesh = mesh_objs[0]
print(f"[*] Target mesh: '{target_mesh.name}' ({len(target_mesh.data.vertices)} vertices)")

# Clean modifiers and parents from target mesh
target_mesh.parent = None
target_mesh.modifiers.clear()

# Remove unused source objects and armatures to keep scene pristine
to_remove = []
for o in bpy.data.objects:
    if o != target_mesh and o.name != "Ironhide_Reference_Armature" and o.name != "Ironhide_Ghost_Reference":
        to_remove.append(o)
for o in to_remove:
    bpy.data.objects.remove(o, do_unlink=True)

# Apply any transforms on target mesh
bpy.context.view_layer.objects.active = target_mesh
bpy.ops.object.select_all(action='DESELECT')
target_mesh.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# 1. Separate into LOOSE parts
print("[*] Separating mesh into loose mechanical parts...")
bpy.ops.mesh.separate(type='LOOSE')
parts = [obj for obj in bpy.context.selected_objects if obj.type == 'MESH' and obj.name != "Ironhide_Ghost_Reference"]
print(f"[✓] Separated into {len(parts)} individual mechanical parts")

# 2. Cache bone line segments in world coordinates
bone_segments = []
for b in arm_obj.pose.bones:
    h = arm_obj.matrix_world @ b.head
    t = arm_obj.matrix_world @ b.tail
    bone_segments.append((b.name, h, t))

# 3. Centroid distance to line segment -> 100% rigid weight assignment
print("[*] Assigning 100% rigid weights based on part centroids...")
for part in parts:
    coords = [v.co for v in part.data.vertices]
    if not coords:
        continue
    # Center in world space
    center = part.matrix_world @ (sum(coords, Vector()) / len(coords))
    
    best_bone = None
    min_dist = float('inf')
    
    for name, h, t in bone_segments:
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
            
    part.vertex_groups.clear()
    vg = part.vertex_groups.new(name=best_bone)
    vg.add([v.index for v in part.data.vertices], 1.0, 'REPLACE')

# 4. Re-join all parts into single mesh
print("[*] Re-joining mechanical parts...")
bpy.ops.object.select_all(action='DESELECT')
for p in parts:
    p.select_set(True)
bpy.context.view_layer.objects.active = parts[0]
bpy.ops.object.join()

joined_mesh = bpy.context.active_object
joined_mesh.name = "cha_demolishor_gs_01"
joined_mesh.parent = arm_obj

mod = joined_mesh.modifiers.new(name="Armature", type='ARMATURE')
mod.object = arm_obj
mod.use_vertex_groups = True
print(f"[✓] Rigid binding complete! Final mesh: {joined_mesh.name} ({len(joined_mesh.data.vertices)} vertices)")

# 5. Inject Dynamic Test Animation for visual inspection (Phase 2.5)
print("[*] Injecting combat test animation frames on Armature...")
arm_obj.animation_data_create()
act = bpy.data.actions.new(name="TF_Combat_Test_Action")
arm_obj.animation_data.action = act

# Animate key bones: Torso swing, Arm swing, Knee bend across 60 frames
bpy.context.scene.frame_start = 1
bpy.context.scene.frame_end = 60

def key_bone_rot(bone_name, frame, euler_rot):
    pbone = arm_obj.pose.bones.get(bone_name)
    if not pbone: return
    pbone.rotation_mode = 'XYZ'
    pbone.rotation_euler = euler_rot
    pbone.keyframe_insert(data_path="rotation_euler", frame=frame)

# Neutral at frame 1 & 60
for bname in ["waist_cin", "L_shoulder_cin", "R_shoulder_cin", "L_forearm_cin", "R_forearm_cin", "L_thigh_cin", "R_thigh_cin"]:
    key_bone_rot(bname, 1, Euler((0, 0, 0), 'XYZ'))
    key_bone_rot(bname, 60, Euler((0, 0, 0), 'XYZ'))

# Dynamic punch / twist at frame 30
key_bone_rot("waist_cin", 30, Euler((0, math.radians(20), math.radians(15)), 'XYZ'))
key_bone_rot("R_shoulder_cin", 30, Euler((math.radians(-40), math.radians(30), math.radians(60)), 'XYZ'))
key_bone_rot("R_forearm_cin", 30, Euler((math.radians(-60), 0, 0), 'XYZ'))
key_bone_rot("L_shoulder_cin", 30, Euler((math.radians(20), math.radians(-10), math.radians(-30)), 'XYZ'))
key_bone_rot("L_thigh_cin", 30, Euler((math.radians(25), 0, 0), 'XYZ'))
key_bone_rot("R_thigh_cin", 30, Euler((math.radians(-20), 0, 0), 'XYZ'))

print("[✓] Dynamic test animation keyed (Frame 1-60)")

# 6. Inject UI Script as Embedded Text in Blend File
gui_script_content = '''# -*- coding: utf-8 -*-
import bpy
import os

class TF_OT_ReassignPart(bpy.types.Operator):
    bl_idname = "tf.reassign_part"
    bl_label = "改绑选中的零件到目标骨骼"
    bl_description = "将当前选中的机械装甲零件顶点100%硬重定向至所选目标骨骼"
    
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
            
        for vg in obj.vertex_groups:
            vg.remove(sel)
            
        if target_bone not in obj.vertex_groups:
            obj.vertex_groups.new(name=target_bone)
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
        box1.label(text="1. 动画连招测试", icon='PLAY')
        row = box1.row(align=True)
        row.operator("screen.animation_play", text="播放动作", icon='PLAY')
        row.operator("screen.animation_cancel", text="暂停", icon='PAUSE')
        
        box2 = layout.box()
        box2.label(text="2. 装甲纠偏(点选乱飞零件)", icon='WRENCH')
        arm = bpy.data.objects.get("Ironhide_Reference_Armature")
        if arm:
            box2.prop_search(context.scene, "tf_target_bone", arm.data, "bones", text="归属骨骼")
        else:
            box2.label(text="[!] 未找到基准骨架", icon='ERROR')
        box2.operator("tf.reassign_part", icon='BONE_DATA')
        
        layout.separator()
        box3 = layout.box()
        box3.label(text="3. 验收确认", icon='CHECKMARK')
        box3.operator("tf.finish_inspection", text="【质检无误，继续打包】", icon='CHECKMARK')

class TF_OT_Finish(bpy.types.Operator):
    bl_idname = "tf.finish_inspection"
    bl_label = "确认继续"
    bl_description = "生成验收通过信号，通知 AI 自动化启动贴图烘焙与 Unity 编译"
    
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
        try:
            bpy.utils.register_class(cls)
        except Exception:
            pass

def unregister():
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass
    if hasattr(bpy.types.Scene, "tf_target_bone"):
        del bpy.types.Scene.tf_target_bone

if __name__ == "__main__":
    register()
'''

text_block = bpy.data.texts.new("tf_gui_inspector.py")
text_block.write(gui_script_content)
text_block.use_module = True

# Register classes immediately in current session
exec(gui_script_content)
print("[✓] Dynamically registered TF Tools UI panel and operators")

# Save inspection scene
OUTPUT_BLEND.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT_BLEND))
print(f"\n[✓] Successfully generated inspection scene: {OUTPUT_BLEND}")
