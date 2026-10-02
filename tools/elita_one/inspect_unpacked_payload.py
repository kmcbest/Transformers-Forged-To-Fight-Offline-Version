import sys
from pathlib import Path

# Add Server directory to sys.path
sys.path.insert(0, str(Path("Server").resolve()))
import export_payload
import json

payload_bytes = Path("build/payload_test.bin").read_bytes()
payload = export_payload.load_payload(payload_bytes)

print(f"Total entries in payload: {len(payload.entries)}")

# 1. Check @roster
roster_text = payload.entries.get("@roster", b"").decode("utf-8")
roster_list = roster_text.splitlines()
print(f"@roster has {len(roster_list)} bots. elita_one_gs in @roster? {'elita_one_gs' in roster_list}")

# 2. Check @userdata:template
userdata_bytes = payload.entries.get("@userdata:template", b"")
userdata_json = json.loads(userdata_bytes.replace(b"%STEAM%", b"[]").replace(b"%ATEAM%", b"[]").decode("utf-8"))
res_user = userdata_json.get("result", {})
heroes_in_userdata = [h.get("bid") for h in res_user.get("updates", {}).get("heroes", []) if "bid" in h]
print(f"@userdata:template has {len(heroes_in_userdata)} heroes. elita_one_gs in userdata? {'elita_one_gs' in heroes_in_userdata}")

# 3. Check @logindata:zh
logindata_bytes = payload.entries.get("@logindata:zh", b"")
logindata_json = json.loads(logindata_bytes.decode("utf-8"))
res_login = logindata_json.get("result", {})
heroes_in_logindata = list(res_login.get("heroes", {}).keys())
print(f"@logindata:zh has {len(heroes_in_logindata)} heroes. elita_one_gs in logindata? {'elita_one_gs' in heroes_in_logindata}")
blueprints_in_logindata = list(res_login.get("blueprints", {}).keys())
print(f"@logindata:zh has {len(blueprints_in_logindata)} blueprints. elita_one_gs in blueprints? {'elita_one_gs' in blueprints_in_logindata}")
characters_in_logindata = list(res_login.get("characters", {}).keys())
print(f"@logindata:zh has {len(characters_in_logindata)} characters. elita_one_gs in characters? {'elita_one_gs' in characters_in_logindata}")

# 4. Check @hero:elita_one_gs:5:50
h5_50 = payload.entries.get("@hero:elita_one_gs:5:50")
print(f"@hero:elita_one_gs:5:50 exists? {h5_50 is not None}")
