# 技能靶场自动化验收工作流与剧本设计经验库

本文档固化了 TFTF Offline 技能实现与回归验证的标准靶场工作流，配合以下工程工具链使用：
- C 侧靶场引擎：`tools/nativehook/autotest.h`、`tools/nativehook/autotest.c`
- MuMu 15 秒级热部署：`tools/deploy_autotest_mumu.py`
- 场景执行与断言：`tools/run_autotest.py`

---

## 一、双轨验收工作流规范

### 1. 默认工作流：**先审后验**（Default Workflow）

适用于新写技能、重做角色或精密回归排查——**先让人审剧本，再进靶场跑实机**。

1. **技能拆解与前置阅读**：
   - 读取官方中文技能描述（数据库 / 注释）以及 `Server/abilities/bots/<bot>.py`、`tools/nativehook/skills/bots/skill_<bot>.c`。
   - 拆出每一条独立机制（如：距离闪避、前冲反制、暴击充能、SP1/SP2/SP3 独立特效、觉醒技或低血线被动）。
2. **输出编号人类可读剧本（不直接跑测试）**：
   向用户提交一张**带编号**的验收剧本表，至少包含以下字段：
   - **序号**：`#1, #2, #3...`（用户可指定全测或只测特定序号，如 `--only 1,3`）
   - **验证目标**：要验证的具体技能条文与判定窗口
   - **双方与开局状态**：`P0 vs P1`、`qid`、初始能量 (`mana`)、初始血量 (`hp_ratio`)、开局注入 Buff (`initial_buffs`)、`freeze_enemy_ai` / `dummy_invincible`
   - **编排动作与战中注入**：`P0` 与 `P1` 的动作序列（何时后闪、何时前冲、何时 `APPLY_BUFF` / `SET_MANA` / `SET_HP` / `SP1~SP3`）
   - **验收通过标准**：`[AB_TRACE]` 日志断言与战斗画面肉眼观测重点（HUD 横幅、浮字 Callout、血条/能量变化）
3. **审阅对齐与转译 JSON**：
   - 用户确认（或提出修改意见）后，再将批准条目写入 `tools/autotest_scenarios/<bot>_test_<case>.json`。
4. **热部署与逐条实机运行**：
   - 若只改了技能 C/Python，禁止重打 1.39GB APK！直接执行：
     ```powershell
     python tools/run_autotest.py --deploy --serial 127.0.0.1:7555 --scenarios <json1> <json2> ... [--only 1,3]
     ```
   - 运行时在屏幕上通过 `skill_overlay` 展示 `[AUTOTEST] <banner>`，方便用户旁观比对。
5. **输出逐条验收报告**：
   - 汇总每条编号用例的断言结果、关键 `[AB_TRACE]` / `[AUTOTEST]` 证据以及人眼观察反馈（如发现异常记录缺陷并进入修复）。
6. **代表角色归档与物理锁定**：
   - 经用户确认“验收完成”的代表角色，登记至 [ACCEPTED_BOTS_REGISTRY.md](file:///e:/Agent/TFTF/re_notes/ACCEPTED_BOTS_REGISTRY.md) 与 `Server/abilities/accepted_bots_lock.json`，并运行 `python tools/check_accepted_lock.py --lock <bot_id>` 锁定其 `.py`、`skill_*.c` 与全部剧本 `.json` 的 SHA-256（门禁默认自动校验防篡改）。

---

### 2. 特指工作流：**先验后审**（仅当用户明确要求时触发）

仅当用户明确说明“先验后审 / 你先自测完汇报”时使用，用于无人值守预验证。

1. **自主拆解与转 JSON**：Agent 直接理解技能描述并编写 `tools/autotest_scenarios/*.json`。
2. **热部署自测与原地修复**：调用 `tools/deploy_autotest_mumu.py` 热更 + `tools/run_autotest.py` 执行并排查问题。
3. **3 轮失败熔断铁律（节约算力）**：
   - 对同一角色或同一场景，若“改代码 -> 热部署 -> 跑靶场”**连续 3 轮未通过**，**必须立即停止自动循环**。
   - 保留现场日志（`build/autotest_last_ring.log` 或 `--out-log`），向用户汇报已确认事实、卡点位置与可选方案。
4. **输出验收报告与真机交付边界**：
   - 自测全绿后输出验收报告供用户审阅；待用户确认后，再由用户（或明确指令后）打包正式 APK 安装到真机复验。

---

## 二、靶场 JSON 协议速查

### 1. 顶层与双方状态字段
- `name`: 场景标识名
- `banner`: 可选，进战斗首帧通过 `skill_overlay` 显示 `[AUTOTEST] <banner>`，建议带编号如 `"#1 Arcee Passive & Dash"`
- `qid`: 关卡 ID（默认 `"1.1.1"`）
- `auto_fight`: `0` 或 `1`（若 `p0_script` 非空，脚本跑完后再根据此值决定是否接管 AutoFight）
- `freeze_enemy_ai`: `0` 或 `1`（推荐 `1`，避免 AI 乱动破坏编排好的交互窗口）
- `dummy_invincible`: `0` 或 `1`（测试多段 SP 或 DOT 累加时建议开启，防止敌方提前死亡）
- `player_invincible`: `0` 或 `1`
- `max_duration_ms`: 超时结束毫秒数（单条用例建议 `15000` ~ `25000`）
- `p0` / `p1`:
  - `bid`: 角色 `bot_id`
  - `mana`: 初始能量（`0.0` ~ `3.0`）
  - `hp_ratio`: 初始血量比例（`0.01` ~ `1.0`，自动钳位防 0 暴毙）
  - `initial_buffs`: 开局挂载 Buff 数组，格式 `[{"id": "<mod_id>", "dur": 5.0, "stacks": 1}]`

### 2. `p0_script` / `p1_script` 动作指令
- **移动与交互动作**：
  `WAIT` (`duration_ms`), `DASH`, `LIGHT`, `MEDIUM`, `HEAVY`, `RANGED` (或 `SHOOT`), `BLOCK` (`hold_ms` / `duration_ms`), `DODGE`, `SIDESTEP_LEFT`, `SIDESTEP_RIGHT`, `SP1`, `SP2`, `SP3`
- **战中即时状态注入动作**（即时生效并推进到下一步）：
  - `APPLY_BUFF` / `BUFF`: `{"action": "APPLY_BUFF", "target": "P1", "id": "<mod_id>", "dur": 4.0, "stacks": 1}`
  - `SET_MANA`: `{"action": "SET_MANA", "target": "P0", "mana": 2.0}`
  - `SET_HP` / `SET_HP_RATIO`: `{"action": "SET_HP", "target": "P0", "hp_ratio": 0.25}`
  > 注：`target` 可填 `"P0"` / `"P1"` 或 `0` / `1`；省略时默认作用于当前脚本所属方（`p0_script` -> `P0`，`p1_script` -> `P1`）。

---

## 三、剧本设计避坑经验库（Arcee 实战沉淀）

1. **远程开枪与远程闪避必须双边拉开距离**：
   - 开局双方默认处于近战贴脸距离，若直接让 `P0` 执行 `RANGED`，或等对方站桩不动，很容易受限于自身一次后闪距离或被对手卡位。
   - **最佳实践**：开局让 `p0_script` 与 `p1_script` 同步执行 `DODGE`（如需要更远可 `repeat: 2`），拉出安全远距离后再发射 `RANGED` / `SP1`。
2. **前冲惩罚（Dash Punishment）交互时序**：
   - 验证“敌方前冲时开枪/反制”时，需显式编排：`P0` 先 `DODGE` 拉距 + 短暂 `WAIT`，`P1` 先同步 `DODGE` 后通过计算好的 `WAIT` 发起 `DASH`，`P0` 在同一时间窗口发出 `RANGED` 或 `SP1`。
3. **SP1 / SP2 / SP3 必须精确预置初始能量**：
   - 验证 SP1 设 `mana: 1.5~2.0`；验证 SP2 设 `mana: 2.2~2.8`；**验证 SP3 务必在开局或施放前注入 `mana: 3.0`**（实机曾出现未满气导致双方傻站发呆的假阴性）。
4. **高伤片段记得保护靶子不暴毙**：
   - 多段 SP 或需要观察后续 DOT / 状态联动时，把 `dummy_invincible` 设为 `1`，防止前三段打死对手后后续击打与 DOT 采样丢失。
5. **条件分支用战中状态注入解耦，别靠运气赌前序触发**：
   - 验证“敌方流血时增伤”“自身低血线触发强化”等逻辑，直接用开局 `hp_ratio` 或战中 `APPLY_BUFF` / `SET_HP` 构造前置条件，单条剧本只测一个明确因果链。
6. **热部署优先，APK 重编殿后**：
   - 在 MuMu 15 上只需首次用 `--no-incremental` 装好 `-DTFTF_AUTOTEST=1` APK。之后修改 `Server/abilities/bots/*.py` 或 `tools/nativehook/skills/bots/skill_*.c` 一律使用：
     ```powershell
     python tools/deploy_autotest_mumu.py --serial 127.0.0.1:7555
     ```
     2~3 秒即完成 `.so`（全新 inode）+ `tftf_offline_payload.bin` 替换；**严禁动辄全量重打 APK**。
