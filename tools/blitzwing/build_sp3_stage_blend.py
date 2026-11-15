import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

"""
Phase 2: Build calibrated Blender EEVEE scene (`blitzwing_sp3_stage.blend`)
and render multi-angle Contact Sheets for HITL visual audit BEFORE Phase 3 Unity baking.
"""

import json
import math
from pathlib import Path

import bpy
from mathutils import Matrix, Quaternion, Vector

TOOLS_BW = Path(r"E:\Agent\TFTF-blender\tools\blitzwing")
if str(TOOLS_BW) not in sys.path:
    sys.path.insert(0, str(TOOLS_BW))

import sp3_curves as M
import sp3_timeline as TL

ASSETS_BW = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Blitzwing")
TEX_DIR = TOOLS_BW / "atlased_textures"
MEG_51_JSON = TOOLS_BW / "megatron_51_authoritative_bindposes.json"
SCRATCH = Path(r"C:\Users\Xiangli496\.gemini\antigravity\brain\cd1292c4-7b4c-4fe9-9d42-14635924d9d4\scratch")
OUT_BLEND = SCRATCH / "blitzwing_sp3_stage.blend"
PREVIEW_DIR = SCRATCH / "sp3_preview"


# P_4x4 maps Unity (ux, uy, uz, 1) -> Blender (-ux, -uz, uy, 1)
P4 = Matrix((
    (-1.0, 0.0, 0.0, 0.0),
    ( 0.0, 0.0,-1.0, 0.0),
    ( 0.0, 1.0, 0.0, 0.0),
    ( 0.0, 0.0, 0.0, 1.0),
))
P4_T = P4.transposed()


def unity_mat_dict_to_m4(d: dict) -> Matrix:
    return Matrix((
        (d["e00"], d["e01"], d["e02"], d["e03"]),
        (d["e10"], d["e11"], d["e12"], d["e13"]),
        (d["e20"], d["e21"], d["e22"], d["e23"]),
        (d["e30"], d["e31"], d["e32"], d["e33"]),
    ))


def load_pbr_material(name: str, diff_path: Path, nm_path: Path = None, raoe_path: Path = None, tint=None):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = 0.55
    bsdf.inputs["Metallic"].default_value = 0.35
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    tex_d = nt.nodes.new("ShaderNodeTexImage")
    tex_d.image = bpy.data.images.load(str(diff_path), check_existing=True)
    tex_d.extension = 'REPEAT'

    if tint is not None:
        mix = nt.nodes.new("ShaderNodeMixRGB")
        mix.blend_type = 'MIX'
        mix.inputs["Fac"].default_value = 0.45
        mix.inputs["Color2"].default_value = tint
        nt.links.new(tex_d.outputs["Color"], mix.inputs["Color1"])
        nt.links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])
    else:
        nt.links.new(tex_d.outputs["Color"], bsdf.inputs["Base Color"])

    if nm_path and nm_path.exists():
        tex_n = nt.nodes.new("ShaderNodeTexImage")
        tex_n.image = bpy.data.images.load(str(nm_path), check_existing=True)
        tex_n.image.colorspace_settings.name = 'Non-Color'
        tex_n.extension = 'REPEAT'
        nmap = nt.nodes.new("ShaderNodeNormalMap")
        nmap.inputs["Strength"].default_value = 0.6
        nt.links.new(tex_n.outputs["Color"], nmap.inputs["Color"])
        nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])

    return mat


def assign_blitzwing_materials(mesh_obj, is_victim: bool = False):
    tint = (0.20, 0.38, 0.72, 1.0) if is_victim else None
    pfx = "Vic_" if is_victim else "BW_"
    mat_main = load_pbr_material(
        f"{pfx}Main",
        TEX_DIR / "cha_blitzwing_main_Diffuse.png",
        TEX_DIR / "cha_blitzwing_main_Normal.png",
        tint=tint,
    )
    mat_tform = load_pbr_material(
        f"{pfx}Tform",
        TEX_DIR / "cha_blitzwing_tform_misc_Diffuse.png",
        TEX_DIR / "cha_blitzwing_tform_misc_Normal.png",
        tint=tint,
    )
    me = mesh_obj.data
    for idx, m in enumerate(me.materials):
        mname = m.name if m else ""
        if "Alt_" in mname or "Tform" in mname or "Tread" in mname or "Tank" in mname or "Jet" in mname:
            me.materials[idx] = mat_tform
        else:
            me.materials[idx] = mat_main


def import_clean_fbx(fbx_name: str, prefix: str):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=str(ASSETS_BW / fbx_name))
    added = [o for o in bpy.data.objects if o not in before]
    arm = None
    mesh = None
    for o in added:
        o.name = f"{prefix}_{o.name}"
        if o.type == 'ARMATURE':
            arm = o
        elif o.type == 'MESH':
            mesh = o
    return arm, mesh


def create_ground_and_lighting():
    # Dark grid floor at Z=0 (Unity Y=0)
    bpy.ops.mesh.primitive_plane_add(size=160.0, location=(15.0, 0.0, 0.0))
    ground = bpy.context.active_object
    ground.name = "ArenaGround"
    mat_g = bpy.data.materials.new("GroundGridMat")
    mat_g.use_nodes = True
    nt = mat_g.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = 0.85
    bsdf.inputs["Specular"].default_value = 0.15
    tex_coord = nt.nodes.new("ShaderNodeTexCoord")
    checker = nt.nodes.new("ShaderNodeTexChecker")
    checker.inputs["Scale"].default_value = 40.0  # 4m tiles on 160m plane
    checker.inputs["Color1"].default_value = (0.14, 0.15, 0.18, 1.0)
    checker.inputs["Color2"].default_value = (0.20, 0.22, 0.26, 1.0)
    nt.links.new(tex_coord.outputs["Object"], checker.inputs["Vector"])
    nt.links.new(checker.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    ground.data.materials.append(mat_g)

    # Impact & Start locator markers
    for mname, upos, col in [
        ("Marker_A0_Start", (-28.70, 0.02, 0.93), (0.95, 0.75, 0.15, 1.0)),
        ("Marker_A1_Slam", (-5.11, 0.02, -2.03), (0.95, 0.20, 0.20, 1.0)),
    ]:
        bpy.ops.mesh.primitive_cylinder_add(radius=1.2, depth=0.04, location=M.u_pos_to_b(upos))
        c = bpy.context.active_object
        c.name = mname
        cm = bpy.data.materials.new(mname + "_Mat")
        cm.use_nodes = True
        cm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = col
        c.data.materials.append(cm)

    # Bright studio sky + sun + rim fill
    world = bpy.data.worlds.new("StageWorld")
    bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.28, 0.35, 0.48, 1.0)
    bg.inputs["Strength"].default_value = 1.2

    bpy.ops.object.light_add(type='SUN', location=(20.0, -20.0, 40.0))
    sun = bpy.context.active_object
    sun.name = "KeySun"
    sun.data.energy = 3.5
    sun.rotation_euler = (math.radians(42), math.radians(15), math.radians(-35))

    bpy.ops.object.light_add(type='SUN', location=(-20.0, 20.0, 25.0))
    fill = bpy.context.active_object
    fill.name = "FillSun"
    fill.data.energy = 1.6
    fill.rotation_euler = (math.radians(65), 0.0, math.radians(145))


def pose_robot_armature(arm_obj, bones_map: dict, bindpose_map: dict, frame: int):
    bpy.context.view_layer.objects.active = arm_obj
    arm_obj.location = (0.0, 0.0, 0.0)
    arm_obj.rotation_mode = 'QUATERNION'
    arm_obj.rotation_quaternion = (1.0, 0.0, 0.0, 0.0)

    # Precompute target armature-space matrices M_arm_target for all bones first
    # so pb.matrix_basis never suffers from stale parent depsgraph evaluation!
    target_arm_mats = {}
    for pb in arm_obj.pose.bones:
        bname = pb.name
        src_key = bname
        if src_key not in bones_map:
            if bname.startswith("LeftHand"):
                src_key = "LeftHand"
            elif bname.startswith("RightHand"):
                src_key = "RightHand"
            else:
                target_arm_mats[bname] = pb.bone.matrix_local.copy()
                continue
        if src_key not in bindpose_map:
            target_arm_mats[bname] = pb.bone.matrix_local.copy()
            continue

        bm_entry = bones_map[src_key]
        bp_u = bindpose_map[src_key]
        wp = Vector(bm_entry["pos"])
        qx, qy, qz, qw = bm_entry["rot"]
        w_u = Matrix.Translation(wp) @ Quaternion((qw, qx, qy, qz)).to_matrix().to_4x4()
        delta_u = w_u @ bp_u
        delta_b = P4 @ delta_u @ P4_T
        target_arm_mats[bname] = delta_b @ pb.bone.matrix_local

    # Set exact matrix_basis cleanly for each bone using parent target matrix directly
    for pb in arm_obj.pose.bones:
        b = pb.bone
        m_target = target_arm_mats[pb.name]
        if b.parent is None:
            m_basis = b.matrix_local.inverted() @ m_target
        else:
            m_parent_target = target_arm_mats[b.parent.name]
            m_rest_rel = b.parent.matrix_local.inverted() @ b.matrix_local
            m_basis = (m_parent_target @ m_rest_rel).inverted() @ m_target

        loc, rot, sca = m_basis.decompose()
        pb.location = loc
        pb.rotation_quaternion = rot
        pb.scale = sca
        pb.keyframe_insert(data_path="location", frame=frame)
        pb.keyframe_insert(data_path="rotation_quaternion", frame=frame)


def main():
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)

    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.fps = 30
    scene.frame_start = 0
    scene.frame_end = M.TOTAL_FRAMES
    scene.render.resolution_x = 640
    scene.render.resolution_y = 360
    scene.render.resolution_percentage = 100

    # Load authoritative bindposes
    meg51_raw = json.loads(MEG_51_JSON.read_text(encoding="utf-8"))["bones"]
    bindpose_map = {
        bname: unity_mat_dict_to_m4(bdata["bind_pose_matrix"])
        for bname, bdata in meg51_raw.items()
    }

    create_ground_and_lighting()

    # 1. Import Actor0 Robot, Tank, Jet + Actor1 Victim Robot
    arm_bw, mesh_bw = import_clean_fbx("blitzwing_robot.fbx", "BW_Robot")
    assign_blitzwing_materials(mesh_bw, is_victim=False)

    arm_tank, mesh_tank = import_clean_fbx("blitzwing_tank.fbx", "BW_Tank")
    assign_blitzwing_materials(mesh_tank, is_victim=False)

    arm_jet, mesh_jet = import_clean_fbx("blitzwing_jet.fbx", "BW_Jet")
    assign_blitzwing_materials(mesh_jet, is_victim=False)

    arm_vic, mesh_vic = import_clean_fbx("blitzwing_robot.fbx", "Victim_Dummy")
    assign_blitzwing_materials(mesh_vic, is_victim=True)

    # Create parent Empty containers for rigid vehicle movement in Blender
    tank_ctrl = bpy.data.objects.new("BW_Tank_Ctrl", None)
    scene.collection.objects.link(tank_ctrl)
    arm_tank.parent = tank_ctrl
    # Shift Tank slightly so mesh bottom treads (z_b=0) align cleanly with ground at slam & body center near BB
    mesh_tank.location = (0.0, 0.0, -0.35)

    jet_ctrl = bpy.data.objects.new("BW_Jet_Ctrl", None)
    scene.collection.objects.link(jet_ctrl)
    arm_jet.parent = jet_ctrl
    # Shift Jet mesh center (z_b=1.4) onto Jet_Ctrl COG pivot
    mesh_jet.location = (0.0, 1.0, -1.35)

    # Ensure quaternion rotation on armatures/pose bones & ctrls
    for obj in (tank_ctrl, jet_ctrl):
        obj.rotation_mode = 'QUATERNION'
    for arm in (arm_bw, arm_vic):
        for pb in arm.pose.bones:
            pb.rotation_mode = 'QUATERNION'

    # 2. Setup StageCamera + StageCameraInterest
    int_empty = bpy.data.objects.new("StageCameraInterest", None)
    int_empty.empty_display_type = 'SPHERE'
    int_empty.empty_display_size = 0.8
    scene.collection.objects.link(int_empty)

    cam_data = bpy.data.cameras.new("StageCamera")
    cam_data.sensor_fit = 'VERTICAL'
    cam_data.sensor_height = 24.0
    cam_data.clip_start = 0.1
    cam_data.clip_end = 500.0
    cam_obj = bpy.data.objects.new("StageCamera", cam_data)
    scene.collection.objects.link(cam_obj)
    tr_con = cam_obj.constraints.new(type='TRACK_TO')
    tr_con.target = int_empty
    tr_con.track_axis = 'TRACK_NEGATIVE_Z'
    tr_con.up_axis = 'UP_Y'
    scene.camera = cam_obj

    # Side Ortho / Overview Camera for diagnostic Contact Sheet 2
    side_data = bpy.data.cameras.new("SideOverviewCam")
    side_data.sensor_fit = 'VERTICAL'
    side_data.angle = math.radians(45.0)
    side_data.clip_end = 500.0
    side_cam = bpy.data.objects.new("SideOverviewCam", side_data)
    scene.collection.objects.link(side_cam)
    # Looking from front-right elevated (-Z_u -> +Y_b) across the whole arena
    side_cam.location = M.u_pos_to_b((-14.0, 18.0, -48.0))
    side_target = bpy.data.objects.new("SideTarget", None)
    side_target.location = M.u_pos_to_b((-12.0, 9.0, 2.0))
    scene.collection.objects.link(side_target)
    sc_con = side_cam.constraints.new(type='TRACK_TO')
    sc_con.target = side_target
    sc_con.track_axis = 'TRACK_NEGATIVE_Z'
    sc_con.up_axis = 'UP_Y'

    # 3. Synthesize and keyframe every frame
    print("[build_sp3_stage] Synthesizing timeline...")
    tl = TL.synthesize_timeline()
    frames = tl["frames"]

    for fr in frames:
        f = fr["frame"]
        mode = fr["mode"]

        # Mutually exclusive visibility on Robot / Jet / Tank
        for obj, vis in [
            (mesh_bw, mode == "robot"),
            (mesh_jet, mode == "jet"),
            (mesh_tank, mode == "tank"),
        ]:
            obj.hide_render = not vis
            obj.hide_viewport = not vis
            obj.keyframe_insert(data_path="hide_render", frame=f)
            obj.keyframe_insert(data_path="hide_viewport", frame=f)

        # Actor0 Robot pose
        if fr["a0_robot_bones"] is not None:
            pose_robot_armature(arm_bw, fr["a0_robot_bones"], bindpose_map, f)

        # Actor0 Vehicle transforms (always keyed so interpolation doesn't snap awkwardly across cuts)
        vb_loc = M.u_pos_to_b(fr["veh_pos"])
        vb_rot = M.u_quat_to_b_wxyz(fr["veh_rot"])
        jet_ctrl.location = vb_loc
        jet_ctrl.rotation_quaternion = vb_rot
        jet_ctrl.keyframe_insert(data_path="location", frame=f)
        jet_ctrl.keyframe_insert(data_path="rotation_quaternion", frame=f)

        tank_ctrl.location = vb_loc
        tank_ctrl.rotation_quaternion = vb_rot
        tank_ctrl.keyframe_insert(data_path="location", frame=f)
        tank_ctrl.keyframe_insert(data_path="rotation_quaternion", frame=f)

        # Actor1 Victim pose
        pose_robot_armature(arm_vic, fr["a1_bones"], bindpose_map, f)

        # StageCamera & Interest & FOV
        cam_obj.location = M.u_pos_to_b(fr["cam_pos"])
        cam_obj.keyframe_insert(data_path="location", frame=f)
        int_empty.location = M.u_pos_to_b(fr["int_pos"])
        int_empty.keyframe_insert(data_path="location", frame=f)
        fov_rad = math.radians(max(5.0, min(170.0, fr["fov"])))
        cam_data.lens = (cam_data.sensor_height * 0.5) / math.tan(fov_rad * 0.5)
        cam_data.keyframe_insert(data_path="lens", frame=f)

    # Use constant interpolation for visibility keyframes and linear/step cleanly on frame-sampled channels
    for obj in (mesh_bw, mesh_jet, mesh_tank):
        if obj.animation_data and obj.animation_data.action:
            for fc in obj.animation_data.action.fcurves:
                for kp in fc.keyframe_points:
                    kp.interpolation = 'CONSTANT'

    bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
    print(f"[build_sp3_stage] Saved {OUT_BLEND}")

    # 4. Render Contact Sheet frames (StageCamera + SideOverview)
    key_frames_stage = [0, 15, 34, 35, 50, 65, 85, 104, 108, 114, 118, 123, 126, 134, 138, 148, 157, 170, 178, 222]
    key_frames_side = [0, 20, 35, 50, 75, 104, 112, 118, 123, 126, 138, 148, 157, 170, 178, 222]

    scene.camera = cam_obj
    for f in key_frames_stage:
        scene.frame_set(f)
        scene.render.filepath = str(PREVIEW_DIR / f"stage_{f:03d}.png")
        bpy.ops.render.render(write_still=True)

    scene.camera = side_cam
    for f in key_frames_side:
        scene.frame_set(f)
        scene.render.filepath = str(PREVIEW_DIR / f"side_{f:03d}.png")
        bpy.ops.render.render(write_still=True)

    print(f"[build_sp3_stage] Rendered {len(key_frames_stage)} stage frames + {len(key_frames_side)} side frames to {PREVIEW_DIR}")


if __name__ == "__main__":
    main()
