import UnityPy
import numpy as np

# Load Arcee bundle to get Bone 8 rest matrix and bindpose 8
env = UnityPy.load('extracted_apk/assets/assetpack/arcee_gs_deluxe2014_odr/arcee_gs_deluxe2014.assetbundle')
bp8 = None
for obj in env.objects:
    if obj.type.name == 'Mesh':
        tree = obj.read_typetree()
        if tree.get('m_Name') == 'cha_arcee_gs_deluxe2014_01':
            bps = tree.get('m_BindPose', [])
            bp8_dict = bps[8]
            bp8 = np.array([
                [bp8_dict['e00'], bp8_dict['e01'], bp8_dict['e02'], bp8_dict['e03']],
                [bp8_dict['e10'], bp8_dict['e11'], bp8_dict['e12'], bp8_dict['e13']],
                [bp8_dict['e20'], bp8_dict['e21'], bp8_dict['e22'], bp8_dict['e23']],
                [bp8_dict['e30'], bp8_dict['e31'], bp8_dict['e32'], bp8_dict['e33']]
            ])
            break

print("bp8:")
print(bp8)
print("\nbp8 inverted:")
print(np.linalg.inv(bp8))
