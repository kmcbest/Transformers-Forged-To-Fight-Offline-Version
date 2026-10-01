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
ud = ud_obj.get("result", {}).get("userData", {})
print("userData keys:", list(ud.keys()))
if "heroes" in ud:
    heroes = ud["heroes"]
    print(f"Heroes in userData: {type(heroes)}, count: {len(heroes)}")
    if isinstance(heroes, dict):
        print("Demolishor in heroes dict?", "demolishor_gs" in heroes)
        if "demolishor_gs" in heroes:
            print("Demolishor entry:", heroes["demolishor_gs"])
