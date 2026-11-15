import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')
import UnityPy

DONOR_BUNDLE = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_gs_leader2015_odr\megatron_gs_leader2015.assetbundle"
env = UnityPy.load(DONOR_BUNDLE)
obj_map = {o.path_id: o for o in env.objects}

for o in env.objects:
    if o.path_id in (-7481134504555158405, 3992037002325232027):
        smr = o.read_typetree()
        mesh_pid = smr.get("m_Mesh", {}).get("m_PathID")
        root_bone = smr.get("m_RootBone", {}).get("m_PathID")
        bones = [b.get("m_PathID") for b in smr.get("m_Bones", [])]
        print(f"Cannon SMR {o.path_id}: mesh={mesh_pid} root={root_bone}")
        for i, b_id in enumerate(bones):
            b_go = obj_map[b_id].read_typetree().get("m_GameObject", {}).get("m_PathID") if b_id in obj_map else 0
            b_name = obj_map[b_go].read_typetree().get("m_Name") if b_go in obj_map else "Unknown"
            print(f"  Bone[{i}] PID={b_id}: '{b_name}'")

for o in env.objects:
    if o.path_id == -6391917038499381755:
        m = o.read_typetree()
        print(f"Cannon Mesh: {m['m_Name']} bindposes: {len(m['m_BindPose'])}")
        for i, bp in enumerate(m['m_BindPose']):
            print(f"  BP[{i}]: e00={bp['e00']} e11={bp['e11']} e22={bp['e22']} e03={bp['e03']} e13={bp['e13']} e23={bp['e23']}")
