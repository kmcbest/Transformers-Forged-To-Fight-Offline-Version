import sys
import UnityPy
import zlib

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

UM_PATH = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\ultramagnus_gs_leader_odr\ultramagnus_gs_leader.assetbundle"
PROC_PATH = r"E:\Agent\TFTF-blender\assets_netflix\character_anim_procedural.assetbundle"


def main():
    env = UnityPy.load(UM_PATH)
    penv = UnityPy.load(PROC_PATH)

    # 1. Submeshes of _00 and _01
    for o in env.objects:
        if o.type.name == "Mesh":
            tt = o.read_typetree()
            name = tt.get("m_Name", "")
            if name in ("cha_ultramagnus_gs_leader_00", "cha_ultramagnus_gs_leader_01"):
                print(f"\nMesh '{name}' totalVerts={tt['m_VertexData']['m_VertexCount']} submeshes={len(tt['m_SubMeshes'])}:")
                for idx, sm in enumerate(tt["m_SubMeshes"]):
                    lb = sm.get("localAABB", {})
                    c = lb.get("m_Center", {})
                    e = lb.get("m_Extent", {})
                    print(
                        f"  submesh[{idx}]: firstByte={sm['firstByte']} indexCount={sm['indexCount']} "
                        f"firstVertex={sm['firstVertex']} vertexCount={sm['vertexCount']} "
                        f"center=({c.get('x',0):.2f},{c.get('y',0):.2f},{c.get('z',0):.2f}) "
                        f"extent=({e.get('x',0):.2f},{e.get('y',0):.2f},{e.get('z',0):.2f})"
                    )

    # 2. Check CRC32 hashes of UltraMagnus _01 bones against AnimationClip bindings
    bones_01 = [
        "Reference", "Reference/COG", "Reference/COG/BodyBase", "Reference/COG/BodyBase/Trailer",
        "Reference/COG/BodyBase/chop1_torso_center", "Reference/COG/BodyBase/chop2_head_center",
        "Reference/COG/BodyBase/chop2_hip_center", "Reference/COG/BodyBase/chop1_backpack_main_center",
        "Reference/COG/BodyBase/Trailer/chop1_shoulder_side_left",
        "Reference/COG/BodyBase/Trailer/chop1_shoulder_side_left/chop1_shoulder_missile1_left",
        "Reference/COG/BodyBase/Trailer/chop1_shoulder_side_right",
        "Reference/COG/chop1_wheel_front_left_turn",
        "", "character_model", "transformed", "Hips", "Reference/Hips",
    ]
    # Also compute Unity Animator.StringToHash (wait: Animator path hash uses CRC32? Let's verify!)
    hash_to_name = {}
    for p in bones_01:
        hash_to_name[zlib.crc32(p.encode("utf-8")) & 0xFFFFFFFF] = p

    for src_name, src in [("UM", env), ("PROC", penv)]:
        for o in src.objects:
            if o.type.name == "AnimationClip":
                tt = o.read_typetree()
                name = tt.get("m_Name", "")
                if any(k in name.lower() for k in ("attackheavy_transformed", "levelup_vehicle_idle_transformed", "ultramagnus_gs_attackspecial_03_transformed")):
                    gcb = tt.get("m_ClipBindingConstant", {}).get("genericBindings", [])
                    uniq_paths = []
                    seen = set()
                    for b in gcb:
                        ph = b.get("path", 0)
                        if ph not in seen:
                            seen.add(ph)
                            uniq_paths.append(ph)
                    print(f"\n[{src_name}] Clip '{name}' unique animated path hashes ({len(uniq_paths)}):")
                    for ph in uniq_paths[:20]:
                        print(f"  pathHash={ph:10d} -> {hash_to_name.get(ph, '?')}")


if __name__ == "__main__":
    main()
