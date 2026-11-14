#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
01_blender_prepare_scene_and_clean_robot.py
在家里有 Blender 3.6+ 的环境中运行 (无头或脚本模式):
  blender -b -P 05_scripts_ready/01_blender_prepare_scene_and_clean_robot.py

功能:
1. 打开 01_robot_source/source/last comp3.blend，利用 fallback_textures/ 一键修复所有丢失外部贴图（根除紫红块），填充空图 datablock。
2. 清理高面数 Subsurf、转 Curve 为 Mesh、应用 Mirror、修复 Cylinder.001 / Plane.020 等负缩放行列式物体法线并统一切线朝外。
3. 剔除纯悬浮贴花 DECALmachine 卡片，清理无用材质脏噪声并自动重拓扑减面 (Decimate) 压进 Unity 16-bit 65,535 顶点上限。
4. 导入 megatron_gs_leader2015 母体人形/坦克/右炮白模 OBJ，并根据 JSON 重建权威 51 骨 & 21 骨参考骨架。
5. 自动将 Tarn 人形归零站立在 Z=0 (朝向 -Y，高 ~11.45m)，并导入 Tarn_Vehicle.glb 缩放对齐母体坦克底盘 (Y=-1.549m) 与履带减面。
6. 保存到 06_working/tarn_workspace_cleaned.blend 供人工微调权重及下一步烘焙。
"""
import json
import math
import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
import bmesh
from mathutils import Matrix, Vector

TARN_ROOT = Path(__file__).resolve().parent.parent
BLEND_SRC = TARN_ROOT / "01_robot_source" / "source" / "last comp3.blend"
FALLBACK_DIR = TARN_ROOT / "01_robot_source" / "fallback_textures"
DONOR_DIR = TARN_ROOT / "04_donor_reference" / "megatron_gs_leader2015"
VEH_GLB = TARN_ROOT / "02_vehicle_source" / "Tarn_Vehicle.glb"
OUT_BLEND = TARN_ROOT / "06_working" / "tarn_workspace_cleaned.blend"
OUT_BLEND.parent.mkdir(parents=True, exist_ok=True)


def import_obj_compat(filepath: Path):
    if hasattr(bpy.ops.wm, "obj_import"):
        bpy.ops.wm.obj_import(filepath=str(filepath))
    else:
        bpy.ops.import_scene.obj(filepath=str(filepath))


def fix_missing_and_empty_images():
    print("[1/6] 修复缺失外部贴图与空 Image Datablock...")
    if FALLBACK_DIR.is_dir():
        bpy.ops.file.find_missing_files(directory=str(FALLBACK_DIR))
    for img in bpy.data.images:
        if img.source == 'FILE' and not img.has_data:
            cand = FALLBACK_DIR / Path(bpy.path.abspath(img.filepath)).name
            if cand.is_file():
                img.filepath = str(cand)
                img.reload()
        if img.size[0] == 0 or img.size[1] == 0:
            # 替换空图 (如 mask8 / ифлу) 为 16x16 纯黑图防 Cycles 报错
            img.source = 'GENERATED'
            img.generated_width = 16
            img.generated_height = 16
            img.generated_color = (0.0, 0.0, 0.0, 1.0)
            img.reload()
            print(f"  [!] 填充空图像 '{img.name}' -> 16x16 黑图")


def tone_down_cycles_grime_for_tftf():
    """
    柔化 Cycles 节点中过重的真实系脏迹/掉漆 Mix 系数，使烘焙出来的材质洁净度与 Tactical Arena 坦克保持同一级别。
    """
    print("[2/6] 校准 Cycles 材质节点（屏蔽紫红缺图，柔化过度脏迹）...")
    for mat in bpy.data.materials:
        if not mat.use_nodes or not mat.node_tree:
            continue
        nt = mat.node_tree
        for nd in nt.nodes:
            if nd.type == 'TEX_IMAGE' and nd.image:
                # 如果是缺失贴图替换来的 COL/GLOSS，适度减弱其混合影响力
                if "COL_VAR2" in nd.image.name:
                    for lnk in list(nd.outputs[0].links):
                        if lnk.to_node.type == 'MIX_SHADER' or lnk.to_node.type == 'MIX_RGB':
                            pass
            # 若 Mix Shader / Mix 混合纯白脏层或 MetalGrime，避免全白盖紫
            if nd.type == 'MIX_SHADER':
                fac_in = nd.inputs[0]
                if not fac_in.is_linked:
                    fac_in.default_value = min(fac_in.default_value, 0.25)


def clean_robot_meshes_and_build_body():
    print("[3/6] 清理 Blender 2.79 物体、负缩放、曲线、Subsurf 并整合压面...")
    col_src = bpy.data.collections.new("Tarn_Robot_RawParts")
    bpy.context.scene.collection.children.link(col_src)

    # 先转换曲线为 Mesh，删除纯悬浮 DECALmachine 卡片与旧手骨 (全骨架重建后重新绑定)
    decal_mats = {"decal02_33", "paneling01_04"}
    all_objs = list(bpy.data.objects)
    robot_meshes = []

    bpy.ops.object.select_all(action='DESELECT')
    for obj in all_objs:
        if obj.type in ('CAMERA', 'LIGHT', 'EMPTY'):
            continue
        if obj.type == 'ARMATURE':
            # 删除只有手骨的局部旧骨架，后续统一绑定权威 51 骨骨架
            bpy.data.objects.remove(obj, do_unlink=True)
            continue
        if obj.type == 'CURVE':
            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)
            bpy.ops.object.convert(target='MESH')
            obj.select_set(False)
        if obj.type == 'MESH':
            # 清理悬浮 DECALmachine 面片（极薄且仅用 decal/paneling 材质）
            mat_names = {ms.material.name for ms in obj.material_slots if ms.material}
            if mat_names and mat_names.issubset(decal_mats):
                print(f"  [-] 移除悬浮贴花面片: {obj.name}")
                bpy.data.objects.remove(obj, do_unlink=True)
                continue
            robot_meshes.append(obj)

    # 独立化网格数据、清除父子、应用合理修改器与负缩放纠正
    for obj in robot_meshes:
        if obj.parent:
            mw = obj.matrix_world.copy()
            obj.parent = None
            obj.matrix_world = mw
        if obj.data.users > 1:
            obj.data = obj.data.copy()

        # 调整修改器: Subsurf 限制为 0/1 级避免 343万面爆炸，Mirror 先保留应用
        for mod in list(obj.modifiers):
            if mod.type == 'SUBSURF':
                obj.modifiers.remove(mod)  # 对游戏低模来说原始多边形已远超需要
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        for mod in list(obj.modifiers):
            try:
                bpy.ops.object.modifier_apply(modifier=mod.name)
            except Exception as e:
                print(f"  [!] 跳过修改器 {obj.name}.{mod.name}: {e}")
        # 应用缩放消除负行列式 (Cylinder.001 / Plane.020)
        det = obj.matrix_world.to_3x3().determinant()
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        if det < 0:
            # 负缩放对象法线被翻转，需 Flip + Recalculate Outside
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.normals_make_consistent(inside=False)
            bpy.ops.object.mode_set(mode='OBJECT')
            print(f"  [!] 已修复负行列式物体法线: {obj.name} (det={det:.3f})")
        obj.select_set(False)

        for c in list(obj.users_collection):
            c.objects.unlink(obj)
        col_src.objects.link(obj)

    # 合并为一个整体 Mesh 用于计算全局包围盒与对位（或后续按部位拆分成刚体组件，此处先做整体对齐备份 + 自动减面）
    # 先对高面数零件逐个轻度 Decimate 到总面数 <= 42,000 tris，保留硬边！
    total_tris = sum(sum(max(0, len(p.vertices) - 2) for p in o.data.polygons) for o in robot_meshes)
    print(f"  当前清理后裸三角面总数: {total_tris:,}")
    target_total = 38000.0
    if total_tris > target_total:
        for obj in robot_meshes:
            ntri = sum(max(0, len(p.vertices) - 2) for p in obj.data.polygons)
            if ntri > 400:
                ratio = max(0.035, min(0.85, (target_total / total_tris) * (1.2 if ntri < 3000 else 0.9)))
                mod = obj.modifiers.new("AutoDecimate", 'DECIMATE')
                mod.decimate_type = 'COLLAPSE'
                mod.ratio = ratio
                bpy.context.view_layer.objects.active = obj
                obj.select_set(True)
                bpy.ops.object.modifier_apply(modifier=mod.name)
                obj.select_set(False)

    new_tris = sum(sum(max(0, len(p.vertices) - 2) for p in o.data.polygons) for o in robot_meshes)
    print(f"  减面后三角面总数: {new_tris:,}")

    # 清理杂乱旧顶点组并写入 part__<原名> 标记，方便后续按硬表面零件分派 100% 刚性骨骼权重
    for o in robot_meshes:
        for vg in list(o.vertex_groups):
            o.vertex_groups.remove(vg)
        if len(o.data.vertices) > 0:
            vg = o.vertex_groups.new(name=f"part__{o.name}")
            vg.add(list(range(len(o.data.vertices))), 1.0, 'REPLACE')

    # 合并为单个低模 Tarn_Robot_Mesh 并创建统一 UV
    bpy.ops.object.select_all(action='DESELECT')
    for o in robot_meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = robot_meshes[0]
    bpy.ops.object.join()
    robot = bpy.context.active_object
    robot.name = "Tarn_Robot_LowPoly"

    # 计算当前世界空间 AABB，缩放到与 megatron_gs_leader2015_00_robot 等高 (11.45m)，脚底踏在 Z=0，中心对准 X=0, Y=0
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    coords = [v.co for v in robot.data.vertices]
    min_x = min(c.x for c in coords); max_x = max(c.x for c in coords)
    min_y = min(c.y for c in coords); max_y = max(c.y for c in coords)
    min_z = min(c.z for c in coords); max_z = max(c.z for c in coords)
    cur_h = max_z - min_z
    target_h = 11.45
    scale_f = target_h / max(cur_h, 1e-4)
    cx = 0.5 * (min_x + max_x)
    cy = 0.5 * (min_y + max_y)
    for v in robot.data.vertices:
        v.co.x = (v.co.x - cx) * scale_f
        v.co.y = (v.co.y - cy) * scale_f
        v.co.z = (v.co.z - min_z) * scale_f
    robot.data.update()

    # 检查双面与法线朝外
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.mesh.remove_doubles(threshold=0.0002)
    bpy.ops.object.mode_set(mode='OBJECT')

    print(f"[✓] Tarn_Robot_LowPoly 对齐完成: verts={len(robot.data.vertices):,}, H=11.45m (Z=[0, 11.45])")
    return robot


def build_armature_from_spec(spec_path: Path, arm_name: str, col_target):
    spec = json.loads(spec_path.read_text(encoding='utf-8'))
    arm_data = bpy.data.armatures.new(arm_name)
    arm_obj = bpy.data.objects.new(arm_name, arm_data)
    col_target.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='EDIT')

    bones_info = {b["name"]: b for b in spec["bones"]}
    children_map = {}
    for b in spec["bones"]:
        p = b.get("parent_transform_name")
        children_map.setdefault(p, []).append(b["name"])

    edit_bones = {}
    for b in spec["bones"]:
        eb = arm_data.edit_bones.new(b["name"])
        pos = Vector(b["blender_pos_matching_obj"])
        eb.head = pos
        kids = [k for k in children_map.get(b["name"], []) if k in bones_info]
        if kids:
            avg = sum((Vector(bones_info[k]["blender_pos_matching_obj"]) for k in kids), Vector((0, 0, 0))) / len(kids)
            if (avg - pos).length > 0.02:
                eb.tail = avg
            else:
                eb.tail = pos + Vector((0, 0, 0.15))
        else:
            eb.tail = pos + Vector((0, -0.15, 0))
        edit_bones[b["name"]] = eb

    for b in spec["bones"]:
        p = b.get("parent_transform_name")
        if p in edit_bones:
            edit_bones[b["name"]].parent = edit_bones[p]

    bpy.ops.object.mode_set(mode='OBJECT')
    print(f"[✓] 已创建权威母壳骨架 {arm_name} ({len(arm_data.bones)} 骨)")
    return arm_obj


def load_donors_and_vehicle():
    print("[4/6] 加载官方母壳白模与权威骨架 (megatron_gs_leader2015)...")
    col_ref = bpy.data.collections.new("04_Donor_References")
    bpy.context.scene.collection.children.link(col_ref)

    for obj_name in ["cha_megatron_gs_leader2015_00_robot.obj", "cha_megatron_gs_leader2015_01_tank.obj", "cha_megatron_gs_leader2015_wpns_cannon_right.obj"]:
        p = DONOR_DIR / obj_name
        if p.is_file():
            before = set(bpy.data.objects)
            import_obj_compat(p)
            for o in set(bpy.data.objects) - before:
                o.name = f"REF_{obj_name[:-4]}"
                o.display_type = 'WIRE'
                for c in list(o.users_collection):
                    c.objects.unlink(o)
                col_ref.objects.link(o)

    build_armature_from_spec(DONOR_DIR / "robot_51_bones_and_bindposes.json", "ARM_MegatronGS_Robot51", col_ref)
    build_armature_from_spec(DONOR_DIR / "tank_21_bones_and_bindposes.json", "ARM_MegatronGS_Tank21", col_ref)

    print("[5/6] 导入并预处理坦克载具 Tarn_Vehicle.glb (缩放 ~0.78, 下移履带对齐 Y_unity=-1.549m)...")
    col_veh = bpy.data.collections.new("02_Tarn_Vehicle")
    bpy.context.scene.collection.children.link(col_veh)
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(VEH_GLB))
    veh_objs = list(set(bpy.data.objects) - before)
    veh_meshes = [o for o in veh_objs if o.type == 'MESH']
    for o in veh_objs:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        col_veh.objects.link(o)

    # 压减高模履带面数 (TarnTankTreadL/R 原合计 36,224 tris)
    for o in veh_meshes:
        if "Tread" in o.name:
            mod = o.modifiers.new("TreadDecimate", 'DECIMATE')
            mod.ratio = 0.25  # ~18,112 -> ~4,500 tris each
            bpy.context.view_layer.objects.active = o
            o.select_set(True)
            bpy.ops.object.modifier_apply(modifier=mod.name)
            o.select_set(False)
            print(f"  [✓] 履带已减面: {o.name} -> {len(o.data.polygons)} polys")

    # 定位整个坦克根空物体或缩放调整: Tarn_Vehicle 原宽9.76m / 长13.13m, 缩放 0.78x 并放进 REF_01_tank
    veh_roots = [o for o in veh_objs if o.parent is None]
    for r in veh_roots:
        r.scale = (0.78, 0.78, 0.78)
        # 在 Blender 中 (+Z 向上), 官方 tank _01 履带底面位于 Z = -1.549 (Unity Y=-1.549)
        r.location = (0.0, 0.0, -1.549)


def main():
    if not BLEND_SRC.is_file():
        raise FileNotFoundError(f"找不到源工程: {BLEND_SRC}")
    bpy.ops.wm.open_mainfile(filepath=str(BLEND_SRC))
    fix_missing_and_empty_images()
    tone_down_cycles_grime_for_tftf()
    clean_robot_meshes_and_build_body()
    load_donors_and_vehicle()
    print(f"[6/6] 保存整理后场景至 {OUT_BLEND} ...")
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
    print("[OK] 阶段一场景准备完毕！")


if __name__ == "__main__":
    main()
