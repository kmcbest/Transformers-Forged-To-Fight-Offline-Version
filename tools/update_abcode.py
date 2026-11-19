import json
import re
import sys
import urllib.request

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

html_path = r'd:\#E\Personal\kmcbest.github.io\tftfr\abcode.html'

with open(html_path, 'r', encoding='utf-8', errors='ignore') as f:
    html = f.read()

# Extract LOCAL_DATA
pattern = r'const LOCAL_DATA = (\{.*?\});\s*\n\s*let ACTIVE_DATA'
match = re.search(pattern, html, re.DOTALL)
if not match:
    print("Error: Could not locate LOCAL_DATA in abcode.html")
    sys.exit(1)

raw_json = match.group(1)
data = json.loads(raw_json)

print(f"Existing version: {data.get('version')}")
print(f"Existing triggers: {len(data.get('triggers', []))}")
print(f"Existing scopes: {len(data.get('scopes', []))}")
print(f"Existing pitfalls: {len(data.get('pitfalls', []))}")

# 1. New Pitfalls
new_pitfalls = [
    {
        "title": "向前划屏 (Action.Dash 32) 严禁单凭相对距离判定为主动前冲",
        "severity": "CRITICAL",
        "bad": "if (action == 32 && dist >= 3.5f) { apply_dash_unstoppable(); }",
        "good": "if (action == 32 && _lightAttackIndex == 0 && _mediumAttackIndex == 0 && !IsInMeleeRange())",
        "desc": "TFTF 触摸屏向前划屏统一发出 action 32。在中立远距离发起时为前冲突进（PlayerDashState），但在攻击连招中（L1/L2/L3 后）向前划屏实质是打出中攻击（M1/M2，处于 PlayerAttackState）；且两机体贴身肉搏时根节点测距实际为 8.0m！单凭 dist >= 3.5f 判定会导致平A连招中击被误判为前冲，频繁误发霸体并抑制随后的防御。必须使用连招计数器归零与原生 IsInMeleeRange() 双重门禁。"
    },
    {
        "title": "濒死触发锁血保底严禁整击提前拒伤 (必须扣血卡线原则)",
        "severity": "HIGH",
        "bad": "if (cur_hp - hit_dmg < max_hp * 0.1) return 0.0f; // 导致重击/必杀直接把伤害整发免掉！",
        "good": "float allowed = cur_hp - max_hp * 0.1f; final_damage = (allowed > 0.0f) ? allowed : 0.0f; trigger_immortality_and_white_relic();",
        "desc": "类似震天尊不朽遗迹（跌破10%血量触发8秒免伤），若在受击计算前直接判定并将伤害置零，会导致将对手原本能打掉大量生命值的那一次重击/大招完全吃掉，甚至在 24% 血量时挨打直接免伤。正确做法是本次攻击依然正常扣除伤害，仅将本次扣血量截断到 10% 警戒线，随后激活免伤状态与白色光环。"
    },
    {
        "title": "自主时间推进技能必须绑定战斗暂停生命周期 (BattleArbiter.Paused)",
        "severity": "MEDIUM",
        "bad": "在 simulation_tick 中无脑累加时间推进能量，未检查对局运行状态",
        "good": "if (Time.timeScale > 0.0001f && !BattleArbiter.Paused && BattleArbiter.IsRunningFight) { update_autonomous_charge(); }",
        "desc": "像震天尊火种源自主充能这类不依赖外部击中、每秒自行充气的机制，必须在原生 Hook 中监听 UnityEngine.Time.timeScale、BattleArbiter.Paused 以及 IsRunningFight。若未加入暂停门禁，玩家暂停游戏、进入设置或KO结算画面时，后台时钟仍在运转，会导致偷充能量破坏平衡。"
    }
]

for p in new_pitfalls:
    if not any(x['title'] == p['title'] for x in data['pitfalls']):
        data['pitfalls'].append(p)
        print(f"Added pitfall: {p['title']}")

# 2. New Triggers
new_triggers = [
    {
        "id": "trig_autonomous_clock",
        "category": "resource_battle",
        "name": "autonomousClock / AutonomousTick",
        "name_zh": "自主火种源充能与周期性时钟 (震天尊被动)",
        "source": "BattleArbiter.cs / PlayerController.cs (hook_145 / simulation_tick)",
        "scope_grammar": "isFightRunning=true; intervalMs=[100..1000]; excludeDefenderGain=true",
        "summary": "不依赖受击与命中的全自主能量推进时钟。用于像震天尊每秒充能、战车持续狂怒倒数等自主机制。",
        "detail": "震天尊官方被动为火种源自主充能，受击不产生能量（DefenderManaGain=0.0）。此触发器在 Native Hook 中通过 simulation_tick 每帧驱动，但必须绑定 is_fight_running()（排除暂停与KO特写）。达到 2.99 格时需通过 ensure_p0_power_rounding 向上卡整至 1.0f 亮起 SP3 红灯。",
        "examples": [
            {
                "bot": "震天尊 (Megatronus)",
                "skill": "火种源自主充能",
                "code": "hook_198(DefenderManaGain)=0.0; autonomous_clock_rate=0.015/s; rounding_clamp=0.985->1.0"
            }
        ],
        "factory": "make_power_gain_statmod",
        "native_hook": True,
        "sample_wire": {
            "t": "autonomous_power",
            "tr": ["simulationTick"],
            "trs": "isFightRunning=true",
            "c": 1.0,
            "m": 1.0,
            "d": -1.0
        }
    },
    {
        "id": "trig_vfx_move_stitched",
        "category": "player_state",
        "name": "stitchedMoveVfx (EnterMove / ExitMove)",
        "name_zh": "缝合动作与周身光环挂载 (EnterMove/ExitMove 驱动)",
        "source": "SequencePlayer.cs:EnterMove(0x100C88C) / ExitMove(0x100C104)",
        "scope_grammar": "moveName=[relic_orange, relic_blue, relic_white, status_unstoppable, shield_bubble]",
        "summary": "通过动画容器 SequencePlayer 动态挂载与卸载周身 3D 光圈、招架护盾与变身特效。",
        "detail": "震天尊切换遗迹（狂怒橙色 relic_orange、保存蓝色 relic_blue、不朽白色 relic_white）以及天火招架护盾的官方真理源实现。切换时光圈互斥，必须先 ExitMove 移除旧光环，再 EnterMove 启动新光环。",
        "examples": [
            {
                "bot": "震天尊 (Megatronus)",
                "skill": "遗迹光环轮转",
                "code": "skill_stop_bot_move(tp, 'relic_orange'); skill_play_bot_move(tp, 'relic_white');"
            },
            {
                "bot": "汽车大师 (Motormaster)",
                "skill": "霸体金色光环",
                "code": "skill_play_bot_move(tp, 'status_unstoppable');"
            }
        ],
        "factory": "make_unstoppable_statmod",
        "native_hook": True,
        "sample_wire": {
            "t": "play_move",
            "tm": "relic_white",
            "tr": ["onTypeActivate"],
            "trs": "type=immortality",
            "c": 1.0,
            "m": 1.0,
            "d": -1.0
        }
    }
]

for t in new_triggers:
    if not any(x['id'] == t['id'] for x in data['triggers']):
        data['triggers'].append(t)
        print(f"Added trigger: {t['name']}")

# 3. New Scopes
new_scopes = [
    {
        "name": "Medium vs Dash",
        "category": "combat_param",
        "syntax": "level=Medium (连招中击) 与 state=Dash (突进前冲) 的本质区分",
        "scope_source": "PlayerController.cs (_lightAttackIndex, _mediumAttackIndex, IsInMeleeRange)",
        "desc_zh": "官方战斗输入中向前划屏 (Action 32) 的歧义分流规则。在连招中为 Medium 攻击，在中立远距离为 Dash 前冲。",
        "values": [
            "level=Medium (_lightAttackIndex > 0 || _mediumAttackIndex > 0 时划屏，普通中击挥砍)",
            "state=Dash (_lightAttackIndex == 0 && _mediumAttackIndex == 0 && !IsInMeleeRange() 时划屏，全场突进)",
            "IsInMeleeRange() (官方近战范围包围盒，用于排除贴脸出招)"
        ],
        "bot_demo": "汽车大师 (Motormaster): 仅在 state=Dash 且 !IsInMeleeRange() 时赋予前冲霸体"
    }
]

for s in new_scopes:
    if not any(x['name'] == s['name'] for x in data['scopes']):
        data['scopes'].append(s)
        print(f"Added scope: {s['name']}")

# Update metadata
data['updated_at'] = "2026-10-29 10:00:00"
data['version'] = "1.2.0"
data['triggers_count'] = len(data['triggers'])
data['scopes_count'] = len(data['scopes'])
data['pitfalls_count'] = len(data['pitfalls'])

updated_json = json.dumps(data, ensure_ascii=False)

# Replace in HTML
new_html = html[:match.start(1)] + updated_json + html[match.end(1):]

with open(html_path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(new_html)

print(f"Successfully updated {html_path}!")
print(f"New counts: triggers={data['triggers_count']}, scopes={data['scopes_count']}, pitfalls={data['pitfalls_count']}")

# 4. Push to Upstash
try:
    upstash_url = "https://deciding-bulldog-136761.upstash.io/set/tftf:ability_triggers_dict"
    upstash_token = "gQAAAAAAAhY5AAIgcDEyZGMwZDRhNzRlZGQ0MDI2YWM2YmI3ZDExNTc3ZjZmNA"
    req = urllib.request.Request(
        upstash_url,
        data=updated_json.encode('utf-8'),
        headers={
            "Authorization": f"Bearer {upstash_token}",
            "Content-Type": "application/json"
        },
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=10) as response:
        res = response.read().decode('utf-8')
        print(f"Upstash Cloud Sync Response: {res}")
except Exception as e:
    print(f"Upstash Cloud Sync Warning: {e}")
