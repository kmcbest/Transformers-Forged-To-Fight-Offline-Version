# -*- coding: utf-8 -*-
import sys
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

def get_bone_names(env):
    go_names = {}
    tr_to_go = {}
    for obj in env.objects:
        if obj.type.name == 'GameObject':
            go_names[obj.path_id] = obj.read_typetree().get('m_Name')
        elif obj.type.name == 'Transform':
            tree = obj.read_typetree()
            tr_to_go[obj.path_id] = tree.get('m_GameObject', {}).get('m_PathID')
    
    smr_bones = []
    for obj in env.objects:
        if obj.type.name == 'SkinnedMeshRenderer':
            tree = obj.read_typetree()
            bones = tree.get('m_Bones', [])
            if len(bones) == 80:
                for b in bones:
                    tr_id = b.get('m_PathID')
                    go_id = tr_to_go.get(tr_id)
                    smr_bones.append(go_names.get(go_id))
                break
    return smr_bones

demo_bones = get_bone_names(UnityPy.load('d:/Agent/tftf/toolchain/unity_build_project/AssetBundles/demolishor_mesh.assetbundle'))
iron_bones = get_bone_names(UnityPy.load('extracted_apk/assets/assetpack/ironhide_cin_rotf_odr/ironhide_cin_rotf.assetbundle'))

print(f"Demolishor bones count: {len(demo_bones)}")
print(f"Ironhide bones count:   {len(iron_bones)}")

matches = [d == i for d, i in zip(demo_bones, iron_bones)]
print(f"Matching bone names: {sum(matches)} / {len(iron_bones)}")
for idx, (d, i) in enumerate(zip(demo_bones, iron_bones)):
    if d != i:
        print(f"  [{idx}] Demo='{d}' vs Iron='{i}'")
    else:
        if idx < 5:
            print(f"  [{idx}] MATCH: '{d}'")
