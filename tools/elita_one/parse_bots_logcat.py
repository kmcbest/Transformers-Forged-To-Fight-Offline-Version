from pathlib import Path

txt = Path(r"C:\Users\Xiangli496\.gemini\antigravity\brain\db8b7cf0-602b-4ceb-a715-2db112ce44ce\logcat_bots_tab.txt").read_text(encoding="utf-8", errors="replace")
lines = txt.splitlines()
print(f"Total logcat lines captured: {len(lines)}")

relevant = [l for l in lines if any(k in l for k in ["RATEWGT", "elita", "kabam", "Unity", "Hero", "hero", "DOTH", "INAPK"])]
print(f"Relevant lines: {len(relevant)}")
for l in relevant[:40]:
    print(l)
