import sys
import json
from pathlib import Path
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(r"E:\Agent\TFTF-blender")
arcee_bundle = ROOT / "extracted_apk" / "assets" / "assetpack" / "arcee_gs_deluxe2014_odr" / "arcee_gs_deluxe2014.assetbundle"
env = UnityPy.load(str(arcee_bundle))

go_dict = {}
tr_dict = {}
tr_to_go = {}
go_to_tr = {}

for obj in env.objects:
    if obj.type.name == "GameObject":
        go_dict[obj.path_id] = obj.read_typetree()
    elif obj.type.name == "Transform":
        tr = obj.read_typetree()
        tr_dict[obj.path_id] = tr
        go_id = tr.get("m_GameObject", {}).get("m_PathID")
        tr_to_go[obj.path_id] = go_id
        go_to_tr[go_id] = obj.path_id

def get_prefab_transforms(root_go_id):
    result = {}
    def recurse(go_id):
        go = go_dict.get(go_id)
        if not go: return
        name = go.get('m_Name')
        tr_id = go_to_tr.get(go_id)
        if name not in result:
            result[name] = tr_id
        tr = tr_dict.get(tr_id)
        if tr:
            for child in tr.get('m_Children', []):
                c_tr_id = child.get('m_PathID')
                c_go_id = tr_to_go.get(c_tr_id)
                recurse(c_go_id)
    recurse(root_go_id)
    return result

p1_transforms = get_prefab_transforms(-5193028223035516378)
p2_transforms = get_prefab_transforms(-4037407093067927022)

# Check all 64 compiled bone names
compiled_bones = [
   "Reference", "Hips", "LeftUpLeg", "LeftLeg", "LeftFoot", "LeftToeBase", "Left_FootFx", "LeftToe", 
   "RightUpLeg", "RightLeg", "RightFoot", "RightToeBase", "Right_FootFx", "RightToe", "Spine", "Spine1", 
   "LeftShoulder", "LeftArm", "LeftArmRoll", "LeftForeArm", "LeftForeArmRoll", "LeftHand", 
   "LeftHandIndex1", "LeftHandIndex2", "LeftHandIndex3", "LeftHandMiddle1", "LeftHandMiddle2", "LeftHandMiddle3", 
   "LeftHandPinky1", "LeftHandPinky2", "LeftHandPinky3", "LeftHandRing1", "LeftHandRing2", "LeftHandRing3", 
   "LeftHandThumb1", "LeftHandThumb2", "LeftHandThumb3", "LeftProp", "LeftShoulderPad", "Neck", "Head", 
   "RightShoulder", "RightArm", "RightArmRoll", "RightForeArm", "RightForeArmRoll", "RightHand", 
   "RightHandIndex1", "RightHandIndex2", "RightHandIndex3", "RightHandMiddle1", "RightHandMiddle2", "RightHandMiddle3", 
   "RightHandPinky1", "RightHandPinky2", "RightHandPinky3", "RightHandRing1", "RightHandRing2", "RightHandRing3", 
   "RightHandThumb1", "RightHandThumb2", "RightHandThumb3", "RightProp", "RightShoulderPad"
]

missing_p1 = [b for b in compiled_bones if b not in p1_transforms]
missing_p2 = [b for b in compiled_bones if b not in p2_transforms]

print(f"Missing in Prefab 1: {missing_p1}")
print(f"Missing in Prefab 2: {missing_p2}")
