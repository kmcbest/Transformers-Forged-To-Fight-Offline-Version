import UnityPy

bundle_path = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\arcee_gs_deluxe2014_odr\arcee_gs_deluxe2014.assetbundle"
env = UnityPy.load(bundle_path)

def dump_node(node, level=0):
    go = node.read()
    comps = [c.type.name for c in go.m_Components]
    print("  " * level + f"- {go.m_Name} ({', '.join(comps)})")
    for child_ptr in go.m_Transform.read().m_Children:
        dump_node(child_ptr, level + 1)

for obj in env.objects:
    if obj.type.name == "GameObject":
        go = obj.read()
        if go.m_Name == "Arcee_GS_Deluxe2014":
            print("Found root prefab:")
            # print tree
            for comp_ptr in go.m_Components:
                c = comp_ptr.read()
                print(f"  Root component: {comp_ptr.type.name}")
            # dump top children
            tr = go.m_Transform.read()
            for child_ptr in tr.m_Children:
                ch = child_ptr.read().m_GameObject.read()
                print(f"  Child: {ch.m_Name}")
                if ch.m_Name in ["character_model", "transformed"]:
                    for c2_ptr in ch.m_Transform.read().m_Children:
                        c2 = c2_ptr.read().m_GameObject.read()
                        print(f"    Child2: {c2.m_Name} ({[x.type.name for x in c2.m_Components]})")
                        for c3_ptr in c2.m_Transform.read().m_Children:
                            c3 = c3_ptr.read().m_GameObject.read()
                            print(f"      Child3: {c3.m_Name} ({[x.type.name for x in c3.m_Components]})")
