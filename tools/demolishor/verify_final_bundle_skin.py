import sys
import struct
from pathlib import Path
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

final_bundle = Path("assets_redeco/demolishor_gs.assetbundle")
f_env = UnityPy.load(str(final_bundle))

# Get SMR bone names
tr_to_go = {}
go_dict = {}
for obj in f_env.objects:
    if obj.type.name == 'GameObject':
        go_dict[obj.path_id] = obj.read_typetree()
    elif obj.type.name == 'Transform':
        tree = obj.read_typetree()
        go_id = tree.get('m_GameObject', {}).get('m_PathID')
        tr_to_go[obj.path_id] = go_id

smr_bones = []
for obj in f_env.objects:
    if obj.type.name == "SkinnedMeshRenderer":
        smr = obj.read_typetree()
        if len(smr.get("m_Bones", [])) == 80:
            for b in smr.get("m_Bones", []):
                tr_id = b.get("m_PathID")
                go_id = tr_to_go.get(tr_id)
                smr_bones.append(go_dict.get(go_id, {}).get("m_Name", "UNKNOWN"))
            break

print(f"Loaded {len(smr_bones)} SMR bones.")

# Now inspect Mesh
for obj in f_env.objects:
    if obj.type.name == "Mesh":
        tree = obj.read_typetree()
        if tree.get("m_Name") == "cha_ironhide_cin_rotf_00":
            vdata = tree.get("m_VertexData", {})
            vcount = vdata.get("m_VertexCount", 0)
            data = bytes(vdata.get("m_DataSize", []))
            
            s0_stride = 40
            s1_stride = 4
            s2_stride = 4
            s2_offset = vcount * (s0_stride + s1_stride)
            
            finger_bone_indices = set(i for i, b in enumerate(smr_bones) if any(k in b.lower() for k in ["thumb", "index", "middle", "ring", "pinky"]))
            print(f"Finger bone indices in SMR ({len(finger_bone_indices)}):", sorted(list(finger_bone_indices)))
            
            violations = []
            finger_vert_count = 0
            for v in range(vcount):
                px, py, pz = struct.unpack_from('<3f', data, v * s0_stride)
                base = s2_offset + v * s2_stride
                b_idx, = struct.unpack('<H', data[base : base + 2])
                
                if b_idx in finger_bone_indices:
                    finger_vert_count += 1
                    # Hand in transformed coords: |X| > 1.6, Y (height) in [3.4, 5.2]
                    # If |X| < 1.5 or Y > 5.5, it's a violation!
                    if abs(px) < 1.5 or py > 5.5 or py < 3.0:
                        violations.append((v, smr_bones[b_idx], (px, py, pz)))
                        
            print(f"\nFinal Bundle Inspection Results:")
            print(f"  Total vertices evaluated: {vcount}")
            print(f"  Total finger-bound vertices: {finger_vert_count}")
            print(f"  Non-hand vertices referencing finger bones: {len(violations)}")
            if violations:
                print(f"  [!] VIOLATION: {violations[0]}")
            else:
                print("  [✓] ZERO SPIKES CONFIRMED: Exactly 0 non-hand vertices have finger weights!")
            break
