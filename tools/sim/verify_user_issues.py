import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from sim_server import g_engine

print("================================================================")
print("TESTING SCENARIO 1: Optimus crits Bonecrusher")
print("================================================================")
g_engine.init("optimusprime_cin_tf", "bonecrusher_cin_rotf", 15000.0, 15000.0, 1000.0, 1000.0)
g_engine.reset()

# P0 (Optimus) performs a Melee Crit attack on P1 (Bonecrusher)
# action_type=1 (Light), is_crit=1, is_heavy=0, is_ranged=0
print("[Action] P0 (Optimus) strikes P1 (Bonecrusher) with MELEE CRIT...")
dmg = g_engine.attack(0, 1, 1, 0, 0)
logs = g_engine.pop_logs()
for log in logs:
    if "碎骨魔" in log or "bleed" in log or "ROLL" in log or "CRIT" in log:
        print(f"  [Log] {log}")

st = g_engine.get_state()
print(f"  P0 (Optimus) buffs: {[b['id'] + ' (stacks=' + str(b['stacks']) + ')' for b in st['p0']['buffs']]}")
print(f"  P1 (Bonecrusher) buffs: {[b['id'] + ' (stacks=' + str(b['stacks']) + ')' for b in st['p1']['buffs']]}")

print("\n================================================================")
print("TESTING SCENARIO 2: Bonecrusher uses SP1 on Optimus (2 bleeds)")
print("================================================================")
g_engine.init("optimusprime_cin_tf", "bonecrusher_cin_rotf", 15000.0, 15000.0, 1000.0, 1000.0)
g_engine.reset()

# P1 (Bonecrusher) fires SP1 (action_type=16) on P0 (Optimus), landing 2 hits
print("[Action] P1 (Bonecrusher) fires SP1 hit 1 on P0...")
g_engine.attack(1, 16, 0, 0, 0)
print("[Action] P1 (Bonecrusher) fires SP1 hit 2 on P0...")
g_engine.attack(1, 16, 0, 0, 0)

logs = g_engine.pop_logs()
for log in logs:
    if "SP1" in log or "bleed" in log or "ROLL" in log:
        print(f"  [Log] {log}")

st = g_engine.get_state()
print(f"  Immediately after SP1: P0 (Optimus) buffs: {[b['id'] + ' (stacks=' + str(b['stacks']) + ', rem=' + str(b['rem_ms']) + 'ms)' for b in st['p0']['buffs']]}")

print("\n[Action] Advancing simulator clock by 1100ms (1.1s)...")
g_engine.tick(1100)

logs = g_engine.pop_logs()
for log in logs:
    if "Purified" in log or "purify" in log or "bleed" in log or "OPTIMUS" in log:
        print(f"  [Log] {log}")

st = g_engine.get_state()
print(f"  After 1100ms: P0 (Optimus) buffs: {[b['id'] + ' (stacks=' + str(b['stacks']) + ', rem=' + str(b['rem_ms']) + 'ms)' for b in st['p0']['buffs']]}")
print(f"  P0 Mana: {st['p0']['mana']:.2f} bars")
