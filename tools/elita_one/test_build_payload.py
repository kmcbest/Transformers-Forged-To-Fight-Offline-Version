import sys
from pathlib import Path

sys.path.insert(0, str(Path("Server").resolve()))
import export_payload

p = export_payload.build_payload(8080)
print(f"Payload size: {len(p)}")
print("elita_one_gs in p?", b"elita_one_gs" in p)
zh = "艾丽塔".encode("utf-8")
print("艾丽塔 in p?", zh in p)
if zh not in p:
    print("Why is 艾丽塔 not in p? Let's check @logindata:zh:")
    loaded = export_payload.load_payload(p)
    login_zh = loaded.entries.get("@logindata:zh", b"")
    print("zh in @logindata:zh?", zh in login_zh)
    import json
    parsed = json.loads(login_zh)
    chars = parsed["result"]["characters"]
    elita = chars.get("elita_one_gs")
    print("Elita char in login_zh:", elita)
