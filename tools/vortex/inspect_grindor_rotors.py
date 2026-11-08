import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\grindor_cin_rotf_odr\grindor_cin_rotf.assetbundle")
env = UnityPy.load(str(bundle_path))

# 1. Collect all GameObjects and their path hierarchy
nodes = {}
for obj in env.objects:
    if obj.type.name == "GameObject":
        data = obj.read_typetree()
        nodes[obj.path_id] = {
            "name": data.get("m_Name"),
            "components": [c.get("component", {}).get("m_PathID") for c in data.get("m_Component", [])]
        }

print(f"Total GameObjects: {len(nodes)}")

# 2. Check SMRs and MeshFilters
for obj in env.objects:
    if obj.type.name == "SkinnedMeshRenderer":
        data = obj.read_typetree()
        go_id = data.get("m_GameObject", {}).get("m_PathID")
        go_name = nodes.get(go_id, {}).get("name", "unknown")
        mesh_id = data.get("m_Mesh", {}).get("m_PathID")
        bones = data.get("m_Bones", [])
        print(f"SMR on GameObject '{go_name}': {len(bones)} bones, mesh PID={mesh_id}")
    elif obj.type.name == "MeshRenderer":
        data = obj.read_typetree()
        go_id = data.get("m_GameObject", {}).get("m_PathID")
        go_name = nodes.get(go_id, {}).get("name", "unknown")
        print(f"MeshRenderer on GameObject '{go_name}'")

# 3. Check AnimationClips and see which clips animate RotorMain
print("\n=== CLIPS ANIMATING ROTOR ===")
for obj in env.objects:
    if obj.type.name == "AnimationClip":
        data = obj.read_typetree()
        clip_name = data.get("m_Name")
        # Check bindings
        clip_binding = data.get("m_ClipBindingConstant", {})
        generic_bindings = clip_binding.get("genericBindings", [])
        
        # Check sample curves or path hashes
        # Path hash for RotorMain: hash is CRC32 of relative path or bone name
        # Let's inspect data
        has_rot = False
        rot_bindings = []
        for b in generic_bindings:
            # attribute 2 is rotation in Mecanim (1: pos, 2: rot, 3: scale, 4: euler)
            attr = b.get("attribute")
            type_id = b.get("typeID")
            path_hash = b.get("path")
            # If attribute is 2 (Quaternion) or 4 (Euler) or 1 (Position)
            # Let's note if this clip has rotation bindings
            rot_bindings.append((path_hash, attr, type_id))
        
        # Let's check if clip name contains rotor, vehicle, idle, etc.
        if any(k in clip_name.lower() for k in ["rotor", "vehicle", "idle", "levelup", "reveal"]):
            print(f"Clip '{clip_name}': {len(generic_bindings)} bindings")
