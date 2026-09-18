# TFTF 特殊任务与地图设计开发指南规范
# (Special Missions & Custom Map Design Specification)

本文档系统性地梳理并固化了《变形金刚：百炼为战》（Transformers: Forged to Fight）离线重构版本中**特殊任务（Special Missions / Event Quests）与全新地图的设计规范、数据流转逻辑与代码实现路径**。供后续开发人员与 AI 智能体快速上手、遵循标准流程创建全新地图与活动关卡。

---

## 一、 整体系统架构与数据流转链路

地图系统贯穿 Python 服务端生成、C 嵌入式本地离线服务端分发、Unity IL2CPP 原生 Hook 拦截与 APK 资源打包四个层级：

```
[1. Server/gamedata.py]
    │  声明地图元数据、多语言名称、队伍人数、出战限制、战斗词缀、网格邻接表、敌人实体
    ▼
[2. Server/export_payload.py]
    │  将 gamedata 生成的 JSON 数据编译打包为离线 Wire Payload 二进制字典
    ▼
[3. tools/nativehook/inapk_server.c]
    │  离线 HTTP 路由器：响应 /quests/quest-list, quest-detail/<mid>, quest-begin/<qid>, quest-movedir/<qid>
    │  动态捕获玩家挑选的阵容 (store_quest_team)，支持 1~5 人自由队伍
    ▼
[4. tools/nativehook/hook.c]
    │  hook_170 (SelectQuestTile.SetTexturePath): 重定向专属关卡图标
    │  hook_67 (StartFight) & hook_112/113: 注入 0能量/禁大招、属性倍率、流血DOT等词缀
    ▼
[5. Server/build_phone_apk.py]
    │  自动将 assets_redeco/portrait_*_quest.png 注入 questboard_odr 并更新 toc.txt
```

---

## 二、 地图展示样式与界面布局（Special Missions 规范）

常规故事关卡（Story）与特殊任务（Event）在 UI 和结构上存在明确区别：

| 要素 | 故事关卡 (Story Mode) | 特殊任务 (Special Missions / Event) |
| :--- | :--- | :--- |
| **所属分组** | `group: "story"`, `category: "Story"` | `group: "event"`, `category: "Event"` |
| **进度存档** | `hasProgression: true`（依赖关卡推进树） | `hasProgression: false`（即点即玩） |
| **UI 呈现** | 章节树状滑动图 | **全宽横幅卡片流 (Event Banner Cards)** |
| **难度角标** | `NORMAL` / `HARD` | `CHALLENGE` / `MASTER` / `EXPERT` 专属带色框 |
| **关卡图标** | 默认读取关底 Boss 头像 | **Hook 170 动态重定向为专属 128x128 图标** |
| **场景地形** | 默认战役地形 | 专属主题 3D 地形库（由 `theme` 字段加载） |

---

## 三、 地图核心构件与数据规范

一个完整的地图由 5 个核心部分组成：

### 1. 多语言元信息 (Multi-language Metadata)
- `qid`: 唯一关卡 ID，格式如 `"1.1.2"`、`"1.1.3"`、`"special_duel_01"`。
- `setId`: 所属活动集合 ID，如 `"special_karmasix"`、`"special_gladiator"`。
- `name_zh` / `name_en`: 地图标题，支持中文与英文无缝自适应切换。
- `description_zh` / `description_en`: 关卡剧情或挑战描述。
- `difficulty_label`: 卡片角标，可选 `"NORMAL"`, `"HARD"`, `"CHALLENGE"`, `"EXPERT"`, `"MASTER"`。

### 2. 专属图标与主题视觉 (Custom Visuals)
- **关卡图标（Portrait Icon）**：
  - 尺寸：`128x128`，透明通道 PNG。
  - 命名格式：`portrait_<name>_quest.png`，存放于 `assets_redeco/`。
  - `build_phone_apk.py` 会自动打包进 `questboard_odr/questboard/` 并在 `toc.txt` 注册。
  - 在 `hook.c` 的 `hook_170` 中添加一条映射：
    ```c
    if (strcmp(qid, "<your_qid>") == 0 && g_strnew) {
        a1 = g_strnew("questboard/portrait_<name>_quest");
    }
    ```
- **3D 地貌主题（Terrain Theme）**：
  - 由 `theme` 字段控制（如 `"primordial"` 远古遗迹、`"cybertron"` 赛博坦工场等），Unity 棋盘加载器会寻找 `library_<theme>` 资产包生成 3D 地砖与周边建筑。

### 3. 网格拓扑与路径规则 (Grid, Nodes & Paths)
- **网格维度 (`gridDimension`)**：必须为正方形网格（如 3x3, 5x5, 7x7），坐标系为 `(row, col)`。
- **瓦片属性规范**：
  - 通行瓦片：`{"walkable": true, "hidden": false}`
  - 障碍/空白瓦片：`{"walkable": false, "hidden": true}`
  - 起点：`"start": true`，出生点无敌人。
  - 终点：`"final": true`，战胜终点 Boss 即判定关卡结算胜利。
- **邻接表 (`links` 与 `visibleLinks`) —— 核心关键！**：
  - 每个可通行的瓦片必须显式声明其直接相邻的所有可移动坐标：
    ```json
    "links": [{"x": 1, "y": 1}],
    "visibleLinks": [{"x": 1, "y": 1}]
    ```
  - **严重警告**：若遗漏 `links`，Unity 客户端的 `Gameboard.RequestMove` 会判定移动无效，玩家点击节点将毫无反应、无法移动！
- **折线路径 (`pathData`)**：
  - 驱动棋盘摄像机居中与路径高亮连线。
  - 必须包含至少 1 条完整从起点到终点的点位序列：
    ```json
    "pathData": [{ "path": [{"x": 0, "y": 1}, {"x": 1, "y": 1}, {"x": 2, "y": 1}] }]
    ```

### 4. 敌人实体 (BCGEntity / Encounters)
在遭遇战瓦片上挂载：
```python
"boss": "optimus_c_tf",
"entities": {
    "optimus_c_tf": {
        "key": "optimus_c_tf",
        "characters": ["optimus_c_tf"],
        "entityType": "boss",
        "parentEntityType": "boss",
        "isFinalBoss": True,     # 终点为 True，途中敌人为 False
        "rank": 5,
        "level": 50,
        "sig_lvl": 100,
        "aiType": 0,
        "aiString": "default",
        "aiPer": "default",
        "mapOverride": "arena_level",
        "todIndex": 0
    }
}
```

---

## 四、 4 大高阶设计维度规范

### 维度 1：上阵人数限制（队伍规模）
*支持单挑 1v1、双人搭档 2v2、标准三人队 3v3、满编大队 5v5。*

* **配置方式**：在 `QuestSummary` 与 `availableQuests` 中设置：
  ```json
  "teamSettings": {
      "v": 1,
      "minTeamSize": 1,
      "maxTeamSize": 1,
      "teamSizeMin": 1,
      "teamSizeMax": 1,
      "presetTeam": false
  },
  "minTeamSize": 1,
  "maxTeamSize": 1,
  "teamSizeMin": 1,
  "teamSizeMax": 1
  ```
* **实现原理**：
  - Unity 客户端 `QuestTeamSelectScreen` 读取 `teamSizeMin`/`teamSizeMax`，决定选人界面解锁的槽位数量；
  - `inapk_server.c` 中的 `store_quest_team()` 支持动态解析 `tm0` 至 `tm4`，无论玩家选 1 个人还是 5 个人，都会准确绑定并下发至对战与棋盘。

---

### 维度 2：出战机器人限定（Roster Restrictions）
*支持限定阵营（Autobot/Decepticon/Maximal/Predacon）、限定职业（Scout/Tech/Brawler/Warrior/Tactician/Demo）、星级限制、或指定出战 Bot。*

* **配置方式**：在 `QuestSummary` 中挂载 `restrictions`：
  ```json
  "restrictions": [
      { "type": "class", "allowed": ["brawler", "warrior"] },
      { "type": "faction", "allowed": ["autobot"] },
      { "type": "rarity", "minStar": 4, "maxStar": 5 }
  ]
  ```
* **实现原理**：
  - 客户端 `RestrictionsSelectorContainer` 与 `IsMissingGateRequirements` 会比对玩家拥有的机器人，对不符合条件的机器人予以置灰并显示加锁提示；
  - 必要时可通过 `hook.c` 拦截 `VerifyTeamComposition` 确保规则严密执行。

---

### 维度 3：特殊战斗规则与词缀（Combat Modifiers & Affixes）
*支持禁能量/禁必杀（体术肉搏）、生命/攻击动态倍率、环境流血（DOT）、霸体/暴击增强。*

* **实现方式**：
  在 `tools/nativehook/hook.c` 的 `hook_67`（`CombatEngine.StartFight`）中按 `qid` 挂载词缀：
  1. **0 能量 / 禁大招（Silence Mana）**：
     ```c
     if (is_special_silence_quest) {
         *(float*)  ((char*)player_at + 0x54) = 0.0f; // ManaGainRate = 0 (攻击/受击不涨气)
         *(int32_t*)((char*)player_at + 0x58) = 0;    // ManaStart = 0
         *(int32_t*)((char*)player_at + 0x28) = 0;    // SpecialAttackCount = 0 (大招槽数量归零)
     }
     ```
  2. **高难 Boss 属性倍率（HP / Atk Multiplier）**：
     ```c
     hp_f *= 10.0f;  // 10倍血量
     atk_f *= 1.25f; // 1.25倍攻击力
     ```
  3. **环境流血 / 中毒 (DOT)**：
     可在战斗帧循环中定时根据战斗时间扣减生命值，或开局直接挂载特定负面状态。

---

### 维度 4：专属横幅主题与卡片艺术
- **卡片条目图标**：`assets_redeco/portrait_<qid>_quest.png`（128x128），Hook 170 精确重定向。
- **活动横幅背景**：`image` 可指定 `fightlanding/fighteventimglrg_hd` 或其他活动背景。

---

## 五、 新地图开发实施标准作业程序 (SOP)

当需要新增一个特殊地图时，按以下步骤实施：

1. **准备美术资源**：
   - 制作一张 128×128 的 PNG 关卡图标，命名为 `portrait_<name>_quest.png`，放入 `assets_redeco/`。
2. **在 `Server/gamedata.py` 中声明配置**：
   - 在 `_QUEST_NAMES` 与 `_QUEST_DESCRIPTIONS` 中添加多语言翻译。
   - 在 `build_quest_list()` 的 `special_set` 中挂载该地图项，配置 `teamSizeMin/Max`、`difficulty_label`、`theme` 等。
   - 在 `build_quest_summary()` 中增加该 `qid` 的详情字典。
   - 编写或调用拓扑生成函数（如 `build_challenge_map()`），构建 `grid`、`links` 与 `pathData`。
3. **在 `hook.c` 注册图标与词缀**：
   - 在 `hook_170` 中添加 `qid` 重定向至 `questboard/portrait_<name>_quest`。
   - 若有特殊战斗词缀（如 0能量、特定倍率），在 `hook_67` 中挂载判定逻辑。
4. **编译与打包**：
   - 运行 `python tools/build_apk_pipeline.py`（或 `Server/build_phone_apk.py`）重新生成 APK，图标将自动被索引打包。
   - 使用 `python INSTALL-ADB.py` 安装到测试设备进行实机验证。
