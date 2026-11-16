import sys
from pathlib import Path
import UnityPy

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

donor_path = Path("extracted_apk/assets/assetpack/megatron_cin_rotf_odr/megatron_cin_rotf.assetbundle")
brawl_path = Path("assets_redeco/brawl_gs.assetbundle")

env_d = UnityPy.load(str(donor_path))
env_b = UnityPy.load(str(brawl_path))

f_d = list(env_d.files.values())[0] if not hasattr(list(env_d.files.values())[0], 'files') else list(list(env_d.files.values())[0].files.values())[0]
f_b = list(env_b.files.values())[0] if not hasattr(list(env_b.files.values())[0], 'files') else list(list(env_b.files.values())[0].files.values())[0]

# Check the two missing materials in donor: -7777457830161264517 and -7854615674899395621
for pid in [-7777457830161264517, -7854615674899395621]:
    obj_d = f_d.objects.get(pid)
    print(f"Donor Mat {pid}: {obj_d.read_typetree().get('m_Name')}")
    obj_b = f_b.objects.get(pid)
    print(f"Brawl Mat {pid}: {obj_b.read_typetree().get('m_Name')}")

# Who references these materials in donor?
print("\nChecking who references these materials in donor:")
for o in f_d.objects.values():
    try:
        tt = o.read_typetree()
        s = str(tt)
        if "-7777457830161264517" in s or "-7854615674899395621" in s:
            print(f"  Donor Obj {o.path_id} ({o.type.name}) references missing mat")
    except:
        pass

print("\nChecking who references these materials in brawl:")
for o in f_b.objects.values():
    try:
        tt = o.read_typetree()
        s = str(tt)
        if "-7777457830161264517" in s or "-7854615674899395621" in s:
            print(f"  Brawl Obj {o.path_id} ({o.type.name}) references missing mat")
    except:
        pass
