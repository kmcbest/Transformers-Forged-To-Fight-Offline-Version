import UnityPy
from pathlib import Path

bundle_path = Path(r"E:\Agent\TFTF\assets_ios\nemesisprime_gs_voyager2015_odr\nemesisprime_gs_voyager2015.assetbundle")
env = UnityPy.load(str(bundle_path))

id_map = {}
for obj in env.objects:
    try:
        tree = obj.read_typetree()
        name = tree.get("m_Name", "")
        id_map[obj.path_id] = name
    except:
        pass

for obj in env.objects:
    if obj.type.name == "Material":
        tree = obj.read_typetree()
        mat_name = tree.get("m_Name", "")
        if mat_name in ['8F8E8AAC8FF079A2FAF6E9C0996AD2E2A1995AFF', '1885CDD43C9A8818ABBBC06223DC4AAD24ED4889', 'D42B5B20BEECA180412E3A084375B0177A86EDD0', '609F38EECE3A378D70EF815B10658B6C6737D16A']:
            print(f"\nMaterial: {mat_name}")
            tex_envs = tree.get("m_SavedProperties", {}).get("m_TexEnvs", [])
            for prop, val in tex_envs:
                tex_id = val.get("m_Texture", {}).get("m_PathID")
                tex_name = id_map.get(tex_id, "None")
                print(f"  Tex property: {prop} -> {tex_name} (PathID: {tex_id})")
