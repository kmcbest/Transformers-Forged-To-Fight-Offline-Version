import math
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import bpy

TARN_ROOT = Path(r"E:\Agent\TFTF-blender\3rd-party-models\Tarn")
OUT_DIR = TARN_ROOT / "06_working" / "robot_baked_raw"
OUT_DIR.mkdir(parents=True, exist_ok=True)
IMG_SIZE = 2048


def ensure_clean_uv(obj):
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)

    # Ensure existing source UV stays active_render so Image Texture & TexCoord.UV sample source coords!
    orig_uv = next((u for u in obj.data.uv_layers if u.name != "UV_TFTF_Main"), None)
    if orig_uv is not None:
        orig_uv.active_render = True
        print(f"[*] Keeping source UV '{orig_uv.name}' as active_render during bake")

    uv_name = "UV_TFTF_Main"
    if uv_name in obj.data.uv_layers:
        obj.data.uv_layers.remove(obj.data.uv_layers[uv_name])
    uv = obj.data.uv_layers.new(name=uv_name)
    # Bake target ONLY needs uv_layers.active = UV_TFTF_Main; keep orig_uv.active_render = True!
    obj.data.uv_layers.active = uv
    if orig_uv is not None:
        orig_uv.active_render = True

    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(
        angle_limit=math.radians(80.0),
        island_margin=0.004,
        area_weight=0.0,
        correct_aspect=True,
        scale_to_bounds=False,
    )
    bpy.ops.object.mode_set(mode="OBJECT")
    print(f"[✓] Created clean non-overlapping UV '{uv_name}' ({IMG_SIZE}x{IMG_SIZE})")


def optimize_robot_topology_for_unity_16bit(obj):
    """
    Smooth hard/flat facet splits (use_smooth + 52deg autosmooth) and selectively decimate
    heavy torso/shoulder/leg geometry while 100% preserving Hands (30 fingers) and Head/Mask,
    guaranteeing Unity GPU split-vertex count stays ~36k-44k (safely << 65,535 16-bit limit).
    """
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)

    prot_name = "__PROT_HIGH__"
    if prot_name in obj.vertex_groups:
        obj.vertex_groups.remove(obj.vertex_groups[prot_name])
    prot_vg = obj.vertex_groups.new(name=prot_name)

    keep_exact = {
        "part__Plane.000", "part__Plane.001", "part__Plane.002", "part__Plane.003",
        "part__Plane.050", "part__Cube.008", "part__Cube.028", "part__Cube.029",
        "part__Cylinder.040", "part__Sphere.001", "part__Sphere.003",
        "part__Cylinder.001", "part__Cylinder.002",
    }
    keep_idx = {
        vg.index for vg in obj.vertex_groups
        if vg.name.startswith(("handL__", "handR__")) or vg.name in keep_exact
    }
    for vi, v in enumerate(obj.data.vertices):
        if any(g.group in keep_idx and g.weight > 0.05 for g in v.groups):
            prot_vg.add([vi], 1.0, "REPLACE")

    for p in obj.data.polygons:
        p.use_smooth = True
    obj.data.use_auto_smooth = True
    obj.data.auto_smooth_angle = math.radians(52.0)

    mod = obj.modifiers.new("Unity16BitDec", "DECIMATE")
    mod.decimate_type = "COLLAPSE"
    mod.ratio = 0.36
    mod.vertex_group = prot_name
    mod.invert_vertex_group = True
    mod.use_collapse_triangulate = True
    bpy.ops.object.modifier_apply(modifier=mod.name)

    if prot_name in obj.vertex_groups:
        obj.vertex_groups.remove(obj.vertex_groups[prot_name])

    n_tris = sum(max(0, len(p.vertices) - 2) for p in obj.data.polygons)
    print(f"[✓] Optimized Tarn topology for Unity 16-bit: verts={len(obj.data.vertices):,}, polys={len(obj.data.polygons):,}, tris={n_tris:,}")


def make_bake_image(name, colorspace="sRGB"):
    if name in bpy.data.images:
        bpy.data.images.remove(bpy.data.images[name])
    img = bpy.data.images.new(
        name=name, width=IMG_SIZE, height=IMG_SIZE, alpha=False, float_buffer=False
    )
    img.colorspace_settings.name = colorspace
    return img


def attach_bake_target_to_all_materials(obj, img):
    for slot in obj.material_slots:
        mat = slot.material
        if not mat or not mat.use_nodes:
            continue
        nt = mat.node_tree
        for n in list(nt.nodes):
            if n.name == "__TFTF_BAKE_TARGET__":
                nt.nodes.remove(n)
        tex_node = nt.nodes.new("ShaderNodeTexImage")
        tex_node.name = "__TFTF_BAKE_TARGET__"
        tex_node.image = img
        for n in nt.nodes:
            n.select = False
        tex_node.select = True
        nt.nodes.active = tex_node


def detach_bake_target_from_all_materials(obj):
    for slot in obj.material_slots:
        mat = slot.material
        if not mat or not mat.use_nodes:
            continue
        nt = mat.node_tree
        for n in list(nt.nodes):
            if n.name == "__TFTF_BAKE_TARGET__":
                nt.nodes.remove(n)


def configure_cycles():
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 16
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.use_denoising = False
    scene.render.bake.margin = 6
    scene.render.bake.use_clear = True
    scene.render.bake.normal_space = "TANGENT"
    scene.render.bake.normal_r = "POS_X"
    scene.render.bake.normal_g = "POS_Y"
    scene.render.bake.normal_b = "POS_Z"
    print(f"[*] Cycles Bake Device: {scene.cycles.device} (forced CPU; HIP kernel 10.3 not bundled)")


def bake_pass(obj, bake_type, filename, colorspace="Non-Color", pass_filter=None, samples=16):
    scene = bpy.context.scene
    scene.cycles.samples = samples
    img = make_bake_image(f"bake_{filename}", colorspace=colorspace)
    attach_bake_target_to_all_materials(obj, img)
    scene.cycles.bake_type = bake_type
    if pass_filter is not None:
        scene.render.bake.use_pass_direct = "DIRECT" in pass_filter
        scene.render.bake.use_pass_indirect = "INDIRECT" in pass_filter
        scene.render.bake.use_pass_color = "COLOR" in pass_filter
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.ops.object.bake(type=bake_type)
    out_p = OUT_DIR / filename
    img.filepath_raw = str(out_p)
    img.file_format = "PNG"
    img.save()
    # Assert non-zero baked buffer immediately
    import numpy as np
    arr = np.asarray(img.pixels[:], dtype=np.float32)
    nz = float((arr > 0.005).mean()) * 100.0
    print(f"[✓] Baked {out_p.name} ({IMG_SIZE}x{IMG_SIZE}, {bake_type}, samples={samples}, nz={nz:.2f}%, max={float(arr.max()):.3f})")
    detach_bake_target_from_all_materials(obj)


def bake_albedo_bypass_metallic(obj, filename):
    """
    In Cycles, DIFFUSE COLOR outputs (0,0,0) on Metallic=1.0 Principled BSDF or Glossy BSDF!
    Temporarily set Metallic=0.0 on all Principled BSDFs and replace Glossy BSDF with
    Diffuse BSDF (preserving Color & Normal inputs), bake DIFFUSE (COLOR only), then restore.
    """
    saved_metallic = []
    saved_glossy = []

    for slot in obj.material_slots:
        mat = slot.material
        if not mat or not mat.use_nodes:
            continue
        nt = mat.node_tree
        for n in list(nt.nodes):
            if n.type == "BSDF_PRINCIPLED":
                m_in = n.inputs.get("Metallic")
                if m_in:
                    src = m_in.links[0].from_socket if m_in.is_linked else None
                    val = float(m_in.default_value)
                    saved_metallic.append((nt, m_in, src, val))
                    for lk in list(m_in.links):
                        nt.links.remove(lk)
                    m_in.default_value = 0.0
            elif n.type == "BSDF_GLOSSY":
                # Swap Glossy -> temporary Diffuse BSDF preserving incoming Color/Normal and outgoing links
                diff = nt.nodes.new("ShaderNodeBsdfDiffuse")
                diff.name = f"__TMP_DIFF_{n.name}"
                col_in = n.inputs.get("Color")
                nrm_in = n.inputs.get("Normal")
                col_src = col_in.links[0].from_socket if (col_in and col_in.is_linked) else None
                nrm_src = nrm_in.links[0].from_socket if (nrm_in and nrm_in.is_linked) else None
                if col_src:
                    nt.links.new(col_src, diff.inputs["Color"])
                elif col_in:
                    diff.inputs["Color"].default_value = tuple(col_in.default_value)
                if nrm_src:
                    nt.links.new(nrm_src, diff.inputs["Normal"])
                out_targets = []
                for lk in list(n.outputs[0].links):
                    to_s = lk.to_socket
                    out_targets.append(to_s)
                    nt.links.remove(lk)
                    nt.links.new(diff.outputs[0], to_s)
                saved_glossy.append((nt, n, diff, out_targets))

    try:
        bake_pass(obj, "DIFFUSE", filename, colorspace="sRGB", pass_filter={"COLOR"}, samples=16)
    finally:
        for nt, n, diff, out_targets in saved_glossy:
            for to_sock in out_targets:
                for lk in list(to_sock.links):
                    nt.links.remove(lk)
                nt.links.new(n.outputs[0], to_sock)
            nt.nodes.remove(diff)
        for nt, m_in, src, val in saved_metallic:
            if src is not None:
                nt.links.new(src, m_in)
            m_in.default_value = val


def bake_metallic_via_emit(obj, filename):
    """
    Build a Mix-Shader-aware scalar emission graph mirroring each material's Mix Shader
    tree so blended scratched-paint materials produce exact per-pixel Metallic values!
    """
    saved_outputs = []
    temp_nodes_by_nt = []

    for slot in obj.material_slots:
        mat = slot.material
        if not mat or not mat.use_nodes:
            continue
        nt = mat.node_tree
        out_node = next(
            (n for n in nt.nodes if n.type == "OUTPUT_MATERIAL" and n.is_active_output),
            next((n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"), None),
        )
        if not out_node or not out_node.inputs[0].is_linked:
            continue
        orig_src = out_node.inputs[0].links[0].from_socket
        saved_outputs.append((nt, out_node, orig_src))
        created = []
        cache = {}

        def build_metal_socket(shader_sock):
            node = shader_sock.node
            if node in cache:
                return cache[node]
            if node.type == "MIX_SHADER":
                fac_in = node.inputs[0]
                s1 = node.inputs[1].links[0].from_socket if node.inputs[1].is_linked else None
                s2 = node.inputs[2].links[0].from_socket if node.inputs[2].is_linked else None
                m1 = build_metal_socket(s1) if s1 else None
                m2 = build_metal_socket(s2) if s2 else None
                mix_em = nt.nodes.new("ShaderNodeMixShader")
                created.append(mix_em)
                if fac_in.is_linked:
                    nt.links.new(fac_in.links[0].from_socket, mix_em.inputs[0])
                else:
                    mix_em.inputs[0].default_value = fac_in.default_value
                if m1:
                    nt.links.new(m1, mix_em.inputs[1])
                if m2:
                    nt.links.new(m2, mix_em.inputs[2])
                cache[node] = mix_em.outputs[0]
                return mix_em.outputs[0]
            em = nt.nodes.new("ShaderNodeEmission")
            created.append(em)
            if node.type == "BSDF_PRINCIPLED":
                m_in = node.inputs.get("Metallic")
                if m_in and m_in.is_linked:
                    nt.links.new(m_in.links[0].from_socket, em.inputs[0])
                elif m_in:
                    v = float(m_in.default_value)
                    em.inputs[0].default_value = (v, v, v, 1.0)
                else:
                    em.inputs[0].default_value = (0.0, 0.0, 0.0, 1.0)
            elif node.type == "BSDF_GLOSSY":
                em.inputs[0].default_value = (1.0, 1.0, 1.0, 1.0)
            else:
                em.inputs[0].default_value = (0.0, 0.0, 0.0, 1.0)
            cache[node] = em.outputs[0]
            return em.outputs[0]

        metal_sock = build_metal_socket(orig_src)
        nt.links.new(metal_sock, out_node.inputs[0])
        temp_nodes_by_nt.append((nt, created))

    try:
        bake_pass(obj, "EMIT", filename, colorspace="Non-Color", samples=16)
    finally:
        for nt, out_node, orig_src in saved_outputs:
            nt.links.new(orig_src, out_node.inputs[0])
        for nt, created in temp_nodes_by_nt:
            for n in created:
                nt.nodes.remove(n)


def main():
    robot = bpy.data.objects.get("Tarn_Robot_LowPoly")
    if not robot:
        raise RuntimeError("Missing Tarn_Robot_LowPoly in scene!")

    # Hide everything else from Cycles render/bake so other objects never cast AO shadows onto Tarn!
    for o in bpy.data.objects:
        if o.type in ("MESH", "CURVE", "SURFACE", "META", "FONT"):
            o.hide_render = (o != robot)
    robot.hide_viewport = False
    robot.hide_render = False

    # Ensure Material.005 (robot eyes behind DJD mask) emits crisp crimson-red regardless of viewing angle
    for slot in robot.material_slots:
        m = slot.material
        if m and m.name.startswith("Material.005") and m.use_nodes:
            nt = m.node_tree
            out_n = next((n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"), None)
            if out_n:
                em = nt.nodes.new("ShaderNodeEmission")
                em.name = "__EYE_CRIMSON_EMIT__"
                em.inputs["Color"].default_value = (1.0, 0.04, 0.07, 1.0)
                em.inputs["Strength"].default_value = 3.0
                nt.links.new(em.outputs[0], out_n.inputs[0])
                print(f"[✓] Forced bright crimson-red eye emission on {m.name}")

    optimize_robot_topology_for_unity_16bit(robot)
    ensure_clean_uv(robot)
    configure_cycles()

    bake_albedo_bypass_metallic(robot, "tarn_robot_albedo.png")
    bake_pass(robot, "NORMAL", "tarn_robot_normal_std.png", colorspace="Non-Color", samples=16)
    bake_pass(robot, "ROUGHNESS", "tarn_robot_roughness.png", colorspace="Non-Color", samples=16)
    bake_pass(robot, "AO", "tarn_robot_ao.png", colorspace="Non-Color", samples=16)
    bake_pass(robot, "EMIT", "tarn_robot_emission.png", colorspace="sRGB", samples=8)
    bake_metallic_via_emit(robot, "tarn_robot_metallic.png")

    # Wait: should we keep UV_TFTF_Main as UV0 cleanly in a separate baked blend or overwrite?
    # Save a separate tarn_workspace_baked.blend with clean single UV_TFTF_Main while keeping tarn_workspace_cleaned.blend untouched!
    # Cleanly remove old UV layers other than UV_TFTF_Main (guard attribute edge cases like '.vs*')
    bpy.context.view_layer.objects.active = robot
    for idx in range(len(robot.data.uv_layers) - 1, -1, -1):
        uv = robot.data.uv_layers[idx]
        if uv.name != "UV_TFTF_Main":
            try:
                robot.data.uv_layers.remove(uv)
            except Exception as e:
                print(f"[i] Could not remove UV layer '{uv.name}': {e}")
    if "UV_TFTF_Main" in robot.data.uv_layers:
        robot.data.uv_layers["UV_TFTF_Main"].active = True
        robot.data.uv_layers["UV_TFTF_Main"].active_render = True

    baked_blend = TARN_ROOT / "06_working" / "tarn_workspace_baked.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(baked_blend))
    print(f"[OK] Baked all 2048x2048 passes and saved {baked_blend}!")


if __name__ == "__main__":
    main()
