import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

bundle_path = r'E:\Agent\TFTF-blender\toolchain\megatron_anims_registered.assetbundle'
env = UnityPy.load(bundle_path)

for obj in env.objects:
    if obj.type.name == 'Avatar':
        data = obj.read()
        name = getattr(data, 'm_Name', 'avatar')
        if '00' in name and 'wpns' not in name:
            human = data.m_Avatar.m_Human.data
            print("m_HasLeftHand:", human.m_HasLeftHand)
            print("m_HasRightHand:", human.m_HasRightHand)
            print("m_LeftHand:", human.m_LeftHand)
            print("m_HumanBoneIndex count:", len(human.m_HumanBoneIndex))
            # Let's print skeleton bone names
            skel = human.m_Skeleton.data
            print("Skeleton bones count:", len(skel.m_Node))
            for i, node in enumerate(skel.m_Node):
                # find name from TOS
                print(f"  node {i}: parent={node.m_ParentId}, axId={node.m_AxesId}")
