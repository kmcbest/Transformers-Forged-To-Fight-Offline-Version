import json

with open("build/payload_test.bin", "rb") as f:
    data = f.read()

def find_key_body(key_name):
    # Header: 64 bytes
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

login_zh = find_key_body("@logindata:zh")
if login_zh:
    login_obj = json.loads(login_zh)
    heroes = login_obj.get("result", {}).get("heroes", {})
    print(f"@logindata:zh hero count: {len(heroes)}")
    print(f"demolishor_gs in @logindata:zh: {'demolishor_gs' in heroes}")
    if 'demolishor_gs' in heroes:
        print("Demolishor login entry:", json.dumps(heroes['demolishor_gs'], ensure_ascii=False))

userdata = find_key_body("@userdata:template")
if userdata:
    # replace sentinels
    ud_str = userdata.replace(b"%STEAM%", b"{}").replace(b"%ATEAM%", b"{}")
    ud_obj = json.loads(ud_str)
    all_heroes = ud_obj.get("result", {}).get("heroes", [])
    print(f"@userdata:template hero count: {len(all_heroes)}")
    demo_in_ud = [h for h in all_heroes if h.get("bid") == "demolishor_gs"]
    print(f"demolishor_gs in @userdata:template: {len(demo_in_ud)}")
    if demo_in_ud:
        print("Demolishor userdata entry:", json.dumps(demo_in_ud[0], ensure_ascii=False))
