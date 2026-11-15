import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path("e:/Agent/TFTF-blender/assets_redeco/blitzwing_gs.assetbundle")
if not bundle_path.exists():
    print(f"Error: {bundle_path} does not exist!")
    sys.exit(1)

env = UnityPy.load(str(bundle_path))
obj_map = {o.path_id: o for o in env.objects}

print("=== INSPECTING TANK IN BLITZWING ASSETBUNDLE ===")

# Tank SMR PIDs: Showcase=2138194849323017337, Combat=4626197738286450028
for name, smr_pid in [("Showcase Tank SMR", 2138194849323017337), ("Combat Tank SMR", 4626197738286450028)]:
    if smr_pid not in obj_map:
        print(f"ERROR: {name} PID {smr_pid} not found in bundle!")
        continue
    smr = obj_map[smr_pid].read_typetree()
    go_pid = smr["m_GameObject"]["m_PathID"]
    go = obj_map[go_pid].read_typetree() if go_pid in obj_map else None
    mesh_pid = smr["m_Mesh"]["m_PathID"]
    mesh = obj_map[mesh_pid].read_typetree() if mesh_pid in obj_map else None
    
    print(f"\n--- {name} (PID {smr_pid}) ---")
    print(f"  GameObject PID: {go_pid}, Name: {go.get('m_Name') if go else 'N/A'}, Active: {go.get('m_IsActive') if go else 'N/A'}")
    print(f"  SMR Enabled: {smr.get('m_Enabled')}")
    print(f"  Materials: {smr.get('m_Materials')}")
    print(f"  RootBone: {smr.get('m_RootBone')}")
    print(f"  Bones: {smr.get('m_Bones')}")
    print(f"  AABB: {smr.get('m_AABB')}")
    if mesh:
        print(f"  Mesh PID: {mesh_pid}, Name: {mesh.get('m_Name')}")
        vcount = mesh["m_VertexData"]["m_VertexCount"]
        print(f"  Vertex Count: {vcount}")
        print(f"  SubMeshes ({len(mesh.get('m_SubMeshes', []))}):")
        for idx, sub in enumerate(mesh.get("m_SubMeshes", [])):
            print(f"    Submesh {idx}: firstByte={sub.get('firstByte')}, indexCount={sub.get('indexCount')}, topology={sub.get('topology')}, localAABB={sub.get('localAABB')}")
        print(f"  LocalAABB: {mesh.get('m_LocalAABB')}")
        print(f"  BoneNameHashes: {mesh.get('m_BoneNameHashes')}")
        print(f"  BonesAABB count: {len(mesh.get('m_BonesAABB', []))}")
        if mesh.get("m_BonesAABB"):
            print(f"  BonesAABB[0]: {mesh['m_BonesAABB'][0]}")
            if len(mesh['m_BonesAABB']) > 1:
                print(f"  BonesAABB[1]: {mesh['m_BonesAABB'][1]}")

# Inspect Jet Mesh
jet_mesh_pid = -6391917038499381755
if jet_mesh_pid in obj_map:
    jm = obj_map[jet_mesh_pid].read_typetree()
    print(f"\n--- Jet Mesh (PID {jet_mesh_pid}) ---")
    print(f"  Name: {jm.get('m_Name')}")
    print(f"  BoneNameHashes: {jm.get('m_BoneNameHashes')}")
    print(f"  BonesAABB count: {len(jm.get('m_BonesAABB', []))}")
    if jm.get("m_BonesAABB"):
        print(f"  BonesAABB[0]: {jm['m_BonesAABB'][0]}")
        if len(jm['m_BonesAABB']) > 1:
            print(f"  BonesAABB[1]: {jm['m_BonesAABB'][1]}")

# Inspect PropsController
print("\n=== PROPS CONTROLLER ===")
for pc_pid in (-8490429130128858862, -3021806434293993593):
    if pc_pid in obj_map:
        pc = obj_map[pc_pid].read_typetree()
        print(f"\nPropsController PID {pc_pid}:")
        props = pc.get("_props", {})
        keys = props.get("_serializedKeys", [])
        vals = props.get("_serializedValues", [])
        for k, v in zip(keys, vals):
            print(f"  Key '{k}': Name='{v.get('Name')}', InitFlags={v.get('InitFlags')}, Renderers={v.get('_renderers')}, PosOff={v.get('PositionOffset')}, RotOff={v.get('RotationOffset')}")

# Inspect Bone Transform and GameObject
for name, pid in [("Showcase Tank COG", -7543220954911659241), ("Combat Tank COG", -7942071043123098758),
                  ("Showcase Jet COG", -8160233092164819743), ("Combat Jet COG", -8081113419723769434)]:
    if pid in obj_map:
        tr = obj_map[pid].read_typetree()
        go_pid = tr["m_GameObject"]["m_PathID"]
        go = obj_map[go_pid].read_typetree() if go_pid in obj_map else None
        print(f"\n--- {name} (PID {pid}) ---")
        print(f"  GameObject PID: {go_pid}, Name: '{go.get('m_Name') if go else 'N/A'}'")
        print(f"  LocalPosition: {tr.get('m_LocalPosition')}")
        print(f"  LocalRotation: {tr.get('m_LocalRotation')}")
        print(f"  LocalScale: {tr.get('m_LocalScale')}")
        parent = tr.get("m_Father")
        print(f"  Parent: {parent}")

# Inspect Parent Transforms
for pid in (7256209656881810047, 6354873720385821623):
    if pid in obj_map:
        tr = obj_map[pid].read_typetree()
        go_pid = tr["m_GameObject"]["m_PathID"]
        go = obj_map[go_pid].read_typetree() if go_pid in obj_map else None
        print(f"\n--- Tank Parent Transform (PID {pid}) ---")
        print(f"  GameObject PID: {go_pid}, Name: '{go.get('m_Name') if go else 'N/A'}'")
        print(f"  LocalPosition: {tr.get('m_LocalPosition')}")
        print(f"  LocalRotation: {tr.get('m_LocalRotation')}")
        print(f"  LocalScale: {tr.get('m_LocalScale')}")


