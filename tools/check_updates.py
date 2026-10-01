import json

with open("build/payload_test.bin", "rb") as f:
    data = f.read()

def find_key_body(key_name):
    entry_count = int.from_bytes(data[20:24], "little")
    entry_off = int.from_bytes(data[24:28], "little")
    for i in range(entry_count):
        rec = entry_off + i * 16
        k_off = int.from_bytes(data[rec:rec+4], "little")
        k_len = int.from_bytes(data[rec+4:rec+8], "little")
        b_off = int.from_bytes(data[rec+8:rec+12], "little")
        b_len = int.from_bytes(data[rec+12:rec+16], "little")
        k = data[k_off:k_off+k_len].decode("ascii", errors="ignore")
        if k == key_name:
            return data[b_off:b_off+b_len]
    return None

userdata = find_key_body("@userdata:template")
ud_str = userdata.replace(b"%STEAM%", b"{}").replace(b"%ATEAM%", b"{}")
ud_obj = json.loads(ud_str)
updates = ud_obj.get("result", {}).get("updates", [])
print(f"Updates count: {len(updates)}")
update_types = {}
for u in updates:
    t = u.get("type", "unknown")
    update_types[t] = update_types.get(t, 0) + 1
print("Update types:", update_types)

hero_updates = [u for u in updates if u.get("type") == "hero"]
print(f"Hero updates count: {len(hero_updates)}")
demo_hero = [u for u in hero_updates if u.get("value", {}).get("bid") == "demolishor_gs"]
print(f"Demolishor in hero updates: {len(demo_hero)}")
if demo_hero:
    print("Demolishor hero update:", demo_hero[0])
