import UnityPy
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

bundle_path = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\grindor_cin_rotf_odr\grindor_cin_rotf.assetbundle"
env = UnityPy.load(bundle_path)

bones = set()
anim_clips = []
anim_controllers = []

for obj in env.objects:
    if obj.type.name == "AnimationClip":
        c = obj.read()
        anim_clips.append(getattr(c, "m_Name", getattr(c, "name", "clip")))
    elif obj.type.name == "AnimatorOverrideController":
        a = obj.read()
        anim_controllers.append(getattr(a, "m_Name", getattr(a, "name", "controller")))
    elif obj.type.name == "SkinnedMeshRenderer":
        s = obj.read()
        mesh_obj = s.m_Mesh.read() if getattr(s, "m_Mesh", None) else None
        mname = getattr(mesh_obj, "m_Name", getattr(mesh_obj, "name", "")) if mesh_obj else ""
        if "00" in mname and "wpn" not in mname:
            for b in getattr(s, "m_Bones", []):
                bo = b.read()
                bname = getattr(bo, "m_Name", getattr(bo, "name", ""))
                bones.add(bname)

print(f"Total Clips in bundle: {len(anim_clips)}")
for c in anim_clips:
    print(f"  Clip: {c}")

print(f"\nTotal Anim Controllers: {len(anim_controllers)}")
for ac in anim_controllers:
    print(f"  Controller: {ac}")

print(f"\nGrindor 00 Bones ({len(bones)}):")
for b in sorted(bones):
    print(f"  {b}")
