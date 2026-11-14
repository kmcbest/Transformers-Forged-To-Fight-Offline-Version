#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
02_blender_bake_robot_pbr.py
在家里有 Blender 3.6+ 环境中运行:
  blender -b 06_working/tarn_workspace_cleaned.blend -P 05_scripts_ready/02_blender_bake_robot_pbr.py

功能:
1. 为合并降面后的 Tarn_Robot_LowPoly (需先确保 < 65,535 顶点) 自动生成不重叠的统一游戏 UV (`UV_TFTF_Main`, margin=0.006)。
2. 配置 Cycles Bake，分别烘焙出 1024x1024 原生通道贴图到 06_working/robot_baked_raw/:
   - tarn_robot_albedo.png     (Diffuse Color pass, 无光照阴影视差)
   - tarn_robot_normal_std.png (Tangent Space Normal)
   - tarn_robot_roughness.png  (Roughness)
   - tarn_robot_ao.png         (Ambient Occlusion)
   - tarn_robot_emission.png   (Emission)
   - tarn_robot_metallic.png   (将 Principled BSDF Metallic 引脚临时接至 Emission 精确烘出物理金属遮罩!)
注意: 若工作台保留了高清高模与低模双份结构，可在下方改成 Selected-to-Active 烘焙高模细节到低模。
"""
import math
import sys
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

TARN_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = TARN_ROOT / "06_working" / "robot_baked_raw"
OUT_DIR.mkdir(parents=True, exist_ok=True)
IMG_SIZE = 1024


def ensure_clean_uv(obj):
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)

    uv_name = "UV_TFTF_Main"
    if uv_name not in obj.data.uv_layers:
        obj.data.uv_layers.new(name=uv_name)
    obj.data.uv_layers.active = obj.data.uv_layers[uv_name]

    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(
        angle_limit=math.radians(66.0),
        island_margin=0.006,
        area_weight=0.0,
        correct_aspect=True,
        scale_to_bounds=False,
    )
    bpy.ops.object.mode_set(mode='OBJECT')
    print(f"[✓] 已创建非重叠统一烘焙 UV: {uv_name} ({IMG_SIZE}x{IMG_SIZE})")


def make_bake_image(name, colorspace='sRGB'):
    if name in bpy.data.images:
        bpy.data.images.remove(bpy.data.images[name])
    img = bpy.data.images.new(name=name, width=IMG_SIZE, height=IMG_SIZE, alpha=False, float_buffer=False)
    img.colorspace_settings.name = colorspace
    return img


def attach_bake_target_to_all_materials(obj, img):
    target_nodes = []
    for slot in obj.material_slots:
        mat = slot.material
        if not mat or not mat.use_nodes:
            continue
        nt = mat.node_tree
        for n in list(nt.nodes):
            if n.name == "__TFTF_BAKE_TARGET__":
                nt.nodes.remove(n)
        tex_node = nt.nodes.new('ShaderNodeTexImage')
        tex_node.name = "__TFTF_BAKE_TARGET__"
        tex_node.image = img
        for n in nt.nodes:
            n.select = False
        tex_node.select = True
        nt.nodes.active = tex_node
        target_nodes.append((nt, tex_node))
    return target_nodes


def configure_cycles():
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 16
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.bake_type = 'DIFFUSE'
    scene.render.bake.margin = 4
    scene.render.bake.use_clear = True
    # 尝试使用 GPU（若不可用自动退回 CPU）
    try:
        prefs = bpy.context.preferences.addons['cycles'].preferences
        for dt in ('OPTIX', 'CUDA', 'HIP'):
            try:
                prefs.compute_device_type = dt
                prefs.get_devices()
                if any(d.type == dt for d in prefs.devices):
                    scene.cycles.device = 'GPU'
                    break
            except Exception:
                pass
    except Exception:
        scene.cycles.device = 'CPU'
    print(f"[*] Cycles Bake Device: {scene.cycles.device}")


def bake_pass(obj, bake_type, filename, colorspace='Non-Color', pass_filter=None):
    img = make_bake_image(f"bake_{filename}", colorspace=colorspace)
    attach_bake_target_to_all_materials(obj, img)
    scene = bpy.context.scene
    scene.cycles.bake_type = bake_type
    if pass_filter is not None:
        scene.render.bake.use_pass_direct = ('DIRECT' in pass_filter)
        scene.render.bake.use_pass_indirect = ('INDIRECT' in pass_filter)
        scene.render.bake.use_pass_color = ('COLOR' in pass_filter)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.ops.object.bake(type=bake_type)
    out_p = OUT_DIR / filename
    img.filepath_raw = str(out_p)
    img.file_format = 'PNG'
    img.save()
    print(f"[✓] 烘焙保存: {out_p.name}")


def bake_metallic_via_emit(obj, filename):
    """
    Blender Cycles 没有直接独立的 'METALLIC' 烘焙通道；
    临时将 Principled BSDF Metallic 引脚路由至临时 Emission 输出烘焙 EMIT，并在完成后还原节点连接。
    """
    saved_links = []
    for slot in obj.material_slots:
        mat = slot.material
        if not mat or not mat.use_nodes:
            continue
        nt = mat.node_tree
        out_node = next((n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL' and n.is_active_output), None)
        if not out_node:
            out_node = next((n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL'), None)
        if not out_node or not out_node.inputs[0].is_linked:
            continue
        orig_link = out_node.inputs[0].links[0]
        saved_links.append((nt, out_node, orig_link.from_socket))

        # 收集所有 Principled BSDF 金属输入，若只有 1 个则直接透传；多个 Mix 简化取主链首值或平均
        bsdfs = [n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED']
        em = nt.nodes.new('ShaderNodeEmission')
        em.name = "__TMP_METAL_EMIT__"
        if bsdfs:
            m_in = bsdfs[0].inputs.get('Metallic')
            if m_in and m_in.is_linked:
                nt.links.new(m_in.links[0].from_socket, em.inputs[0])
            elif m_in:
                v = m_in.default_value
                em.inputs[0].default_value = (v, v, v, 1.0)
        else:
            em.inputs[0].default_value = (0.2, 0.2, 0.2, 1.0)
        nt.links.new(em.outputs[0], out_node.inputs[0])

    try:
        bake_pass(obj, 'EMIT', filename, colorspace='Non-Color')
    finally:
        for nt, out_node, src_sock in saved_links:
            nt.links.new(src_sock, out_node.inputs[0])
            tmp = nt.nodes.get("__TMP_METAL_EMIT__")
            if tmp:
                nt.nodes.remove(tmp)


def clean_temp_uv_keep_only_tftf(obj):
    # 删除其它杂乱 UV 层并仅保留 UV_TFTF_Main 作为主 UV0 导出
    for uv in list(obj.data.uv_layers):
        if uv.name != "UV_TFTF_Main":
            obj.data.uv_layers.remove(uv)


def main():
    robot = bpy.data.objects.get("Tarn_Robot_LowPoly")
    if not robot:
        raise RuntimeError("场景中找不到 Tarn_Robot_LowPoly，请先运行 01 脚本！")
    ensure_clean_uv(robot)
    configure_cycles()

    # 若需烘纯色无光照反照率，先烘焙 DIFFUSE (仅 COLOR)
    bake_pass(robot, 'DIFFUSE', "tarn_robot_albedo.png", colorspace='sRGB', pass_filter={'COLOR'})
    bake_pass(robot, 'NORMAL', "tarn_robot_normal_std.png", colorspace='Non-Color')
    bake_pass(robot, 'ROUGHNESS', "tarn_robot_roughness.png", colorspace='Non-Color')
    bake_pass(robot, 'AO', "tarn_robot_ao.png", colorspace='Non-Color')
    bake_pass(robot, 'EMIT', "tarn_robot_emission.png", colorspace='sRGB')
    bake_metallic_via_emit(robot, "tarn_robot_metallic.png")

    clean_temp_uv_keep_only_tftf(robot)
    bpy.ops.wm.save_mainfile()
    print("[OK] 人形 PBR 全通道 Cycles 烘焙完成！下一步请运行 03_unify_tarn_textures.py。")


if __name__ == "__main__":
    main()
