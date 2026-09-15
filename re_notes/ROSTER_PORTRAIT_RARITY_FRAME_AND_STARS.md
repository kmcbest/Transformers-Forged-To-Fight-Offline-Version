# 角色头像稀有度边框（紫色外框）与星级（五星）恢复方案

## 一、背景与目标

在当前离线逆向版本中，主界面**机器人列表（BOTS Roster）**中的角色头像卡片缺少原版的美术外框与星级展示：
- **当前现状**：仅显示角色名字、战力数值（如 6,175）、职业图标（如侦察兵小马标）、左上角 Rank 阶级小标，四周为透明空框，底部无星星。
- **原版设计**：
  1. 拥有**稀有度外框（Rarity Frame）**：5 星机器人拥有**高亮发光的紫色外框**（1~4 星分别为灰/绿/蓝/金）。
  2. 底部拥有**星级展示（Stars）**：显示对应的 1~5 颗白色星星（`★★★★★`），觉醒后显示为发光蓝星。
  3. 战力左侧拥有**阵营徽章（Faction Badge）**：汽车人（Autobot）红色标志 / 霸天虎（Decepticon）紫色标志 / 巨无霸（Maximal）/ 原始兽（Predacon）。**注意：它不是 Sprite，而是 UI 字体里的私用区（PUA）字形**（`U+E134` / `U+E135` / `U+E160` / `U+E161`），实现细节见文末「六」与 `.agents/skills/tftf_revival/SKILL.md` §16。

---

## 二、内置美术资产确认（100% 原生存在，无需导入外源图片）

经对客户端资源包进行逆向解析，所有所需 Sprite 均完整存储在 **`assets/assetpack/assets_common_odr/assets_common.assetbundle`** 的 NGUI `UIAtlas` 图集中：

| 元素分类 | Sprite 名称 | 说明 |
| :--- | :--- | :--- |
| **稀有度外框** | `frame_portrait_rarity_0` | 空/透明外框（当前被错误采用） |
| | `frame_portrait_rarity_1` | 1 星边框（普通灰） |
| | `frame_portrait_rarity_2` | 2 星边框（罕见绿） |
| | `frame_portrait_rarity_3` | 3 星边框（稀有蓝） |
| | `frame_portrait_rarity_4` | 4 星边框（史诗金） |
| | **`frame_portrait_rarity_5`** | **5 星边框（传说紫色发光外框，即目标边框）** |
| **星级星星** | **`Star_white`** | **原版卡片底部的白色星星（普通 1~5 星）** |
| | **`Star_Blue`** | 角色觉醒（Signature Ability）激活后的发光蓝星 |
| | `Star_small` | 小号备用星标 |
| **阵营/徽章** | `HeroTile_Badge` | 卡片徽章底板 |
| | `HeroTile_BadgeSmall` | 小型卡片徽章底板 |
| | `FactionIcon` | 阵营图标占位符 |

---

## 三、底层架构与核心函数偏移表（ARM64 RVA）

UI 系统基于 **NGUI** 实现，核心组件为 `HeroPortrait`、`RarityWidget`、`RatingWidget`。

> ⚠️ **下表为早期草稿，部分 RVA 与现行实现不符**（例如 `RefreshFromData` / `SetRarityFrame` 已就地更正，`HeroData::get_Faction` 与 `RatingWidget::SetData` 两行始终未经证实）。**一律以 [`tools/nativehook/hook.c`](file:///e:/Agent/TFTF/tools/nativehook/hook.c) 的 `H[]` 表与实际调用点为准**；这段草稿的未证实偏移正是「阵营徽章静默空白」能存活下来的原因之一，详见文末「六」。

| 类与方法名 | ARM64 偏移 (RVA) | 功能说明 |
| :--- | :--- | :--- |
| `HeroPortrait::RefreshFromData` | `0xE8DF9C` | 核心刷新入口：根据绑定 `HeroData` 刷新卡片各子组件（hook 槽位 33 `RFD`） |
| `HeroPortrait::SetRarityFrame` | `0xE91768` | 边框设置方法（调用点：`apply_hero_portrait_deco`，`hp, rarity, NULL`） |
| `HeroPortrait::ForceSetRarityFrame` | `0xE91D18` | 强制重新设置并刷新边框 UISprite |
| `HeroPortrait::OnHeroTextureLoaded` | `0xE917CC` | 头像贴图加载完成回调（已有 Hook Slot 46 `TEXDONE`） |
| `HeroPortrait::SetEnabledItems` | `0xE8FE60` | 位掩码开关（`OverlayBitMap`: 包含 `HERO_RARITY` 掩码） |
| `HeroPortrait::PlayStarAnim` | `0xE90E48` | 播放星星动画 |
| `RarityWidget::SetData` | `0xE1E7A8` | 星星控件数据入口：负责点亮对应数量的星星 |
| `RatingWidget::SetData` | `0xCD7F18` | 战力与阵营标志控件入口 |
| `HeroData::get_Rarity` | `0xE8A4E0` | 获取角色星级属性（返回值应为 1~5） |
| `HeroData::get_Faction` | `0xE8DBA8` | 获取角色阵营属性（`"autobot"` / `"decepticon"`） |

---

## 四、具体实现方案

本功能有两种实现路线：**方案 A（Native Hook 强开法，立竿见影）** 与 **方案 B（服务端数据层契约修复，原生优雅）**。建议先以方案 A 验证视觉通路，再配合方案 B 实现全量数据持久化。

---

### 方案 A：Native Hook 强开法（在 `tools/nativehook/hook.c` 中实现）

利用当前已有的 Hook 机制，在角色卡片加载完成或刷新时，直接在 Native C 语言层调用函数点亮紫色外框与星星。

#### 1. 挂钩点
直接扩展已有的 **Slot 46 (`TEXDONE` / `HeroPortrait.OnHeroTextureLoaded`, RVA `0xE917CC`)** 或 **Slot 44 (`HeroPortrait.LoadTexture`, RVA `0xE91708`)**。

#### 2. C 代码实现示例
```c
// 定义函数指针原型
typedef void (*hp_set_rarity_frame_t)(void* this_hp, void* str_sprite_name, void* method);
typedef void (*rarity_widget_set_data_t)(void* this_rw, void* hero_data, void* method);
typedef void (*gameobject_set_active_t)(void* go, int active);

void apply_hero_portrait_rarity(void* hp) {
    if (!obj_ok(hp)) return;

    // 1. 设置 5 星紫色发光外框
    // 构造 Il2CppString "frame_portrait_rarity_5"
    if (g_strnew) {
        void* frame_str = g_strnew("frame_portrait_rarity_5");
        if (frame_str) {
            hp_set_rarity_frame_t set_frame = (hp_set_rarity_frame_t)(g_base + 0xE91E10);
            set_frame(hp, frame_str, NULL);
        }
    }

    // 2. 激活边框 UISprite GameObject
    // HeroPortrait 的 frameSprite 位于偏移 +0x190
    void* frame_sprite = *(void**)((char*)hp + 0x190);
    if (obj_ok(frame_sprite)) {
        // Component.get_gameObject @ 0x1B4BD28, GameObject.SetActive @ 0x1B50CA8
        void* go = ((fn8)(g_base + 0x1B4BD28))(frame_sprite, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
        if (obj_ok(go)) {
            ((gameobject_set_active_t)(g_base + 0x1B50CA8))(go, 1);
        }
    }

    // 3. 点亮 5 颗星星 (RarityWidget)
    // HeroPortrait 的 _rarityWidget 位于偏移 +0x178 或 +0x180
    void* rarity_widget = *(void**)((char*)hp + 0x178);
    if (obj_ok(rarity_widget)) {
        void* go_rw = ((fn8)(g_base + 0x1B4BD28))(rarity_widget, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
        if (obj_ok(go_rw)) {
            ((gameobject_set_active_t)(g_base + 0x1B50CA8))(go_rw, 1);
        }
        // 调用 RarityWidget::SetData(@0xE1E7A8)
        // 传入当前绑定的 HeroData (位于 hp + 0x218)
        void* hero_data = *(void**)((char*)hp + 0x218);
        if (obj_ok(hero_data)) {
            ((rarity_widget_set_data_t)(g_base + 0xE1E7A8))(rarity_widget, hero_data, NULL);
        }
    }
}
```

---

### 方案 B：服务端数据驱动原生修复（在 `Server/gamedata.py` 中实现）

让客户端原生系统自动识别星级并挂载边框与星星，无需 Hook 强开。

#### 1. 完善 `Server/responses/GET__bcg_getUserData.json` 与 `build_hero_entry()`
在 `build_hero_entry` 中，目前仅有 `rank` 和 `level`，缺少让卡片直接读取的星级绑定：
```python
def build_hero_entry(bid, rank=1, level=1):
    faction, klass, star = ROSTER.get(bid, ("decepticon", "tact", 1))
    hp, atk = base_stats(bid, rank, level)
    return {
        "entity_type": "bot",
        "bid": bid,
        "rank": rank,
        "level": level,
        "s": star,                 # 注入星级属性 (1..5)
        "rarity": star,            # 某些客户端视图读取 rarity 键
        "star": star,
        "sig_lvl": 0,              # 0 为普通白星，>0 触发觉醒蓝星
        "faction": faction,        # 阵营：autobot / decepticon
        "max_hp": hp,
        "attack": atk,
        "rating": (hp + atk) // 20,
        ...
    }
```

#### 2. 补全 `build_rarity_properties()` 数据契约
客户端在登录时会通过 `rarityProperties` 查询星级的显示样式字典。确保 1~5 星的定义完整：
```python
def build_rarity_properties():
    out = {}
    for star in range(1, 6):
        name = f"{star} Star"
        out[str(star)] = {
            "id": str(star),
            "n": name,
            "name": name,
            "mv": star,
            "map_value": star,
            "sp3qt": 0.5,
            "sp3_quicktime": 0.5,
            "ms": 99,
            "max_sig": 99,
            "frame": f"frame_portrait_rarity_{star}",
            "star_color": "white"
        }
    return out
```

---

## 五、验证步骤与命令

1. **重新导出离线 Payload**：
   ```powershell
   python Server/export_payload.py --output build/tftf_offline_payload.bin
   ```
2. **重新编译 Hook 与打包 APK**（如采用方案 A）：
   ```powershell
   python build_apk.py
   ```
3. **在设备/模拟器中观察**：
   - 进入主界面 -> **机器人（BOTS）**。
   - 验证 5 星机器人卡片是否已显示**紫色发光外框**。
   - 验证卡片下方是否正确排列 **5 颗白色星星（★★★★★）**。
   - 验证战力数值旁是否显示**霸天虎/汽车人阵营标志**。

---

## 六、阵营徽章（PUA 字形）补充记录与踩坑（真机验证）

> 完整踩坑条目见 `.agents/skills/tftf_revival/SKILL.md` §16；此处只记录与本方案直接相关的结论与偏差修正。

### 6.1 机制更正：徽章是字形，不是图集 Sprite
第二节把阵营徽章归到 `assets_common.assetbundle` 图集（`FactionIcon`）是**错的**。阵营徽章是 **UI 字体的私用区（PUA）字形**，客户端把"一个字符"写进 RatingWidget 的阵营 UILabel（`widget+0x30`，先 `GameObject.SetActive(1)`）来绘制：

| 字形 | 阵营 | `ROSTER.faction` 取值（必须小写） |
| :--- | :--- | :--- |
| `U+E134` | Autobot 汽车人 | `"autobot"` |
| `U+E135` | Decepticon 霸天虎 | `"decepticon"` |
| `U+E160` | Maximal 巨无霸 | `"maximal"` |
| `U+E161` | Predacon 原始兽 | `"predacon"` |

### 6.2 静默空白的根因
早期实现把"取阵营 → 翻译成字形"外包给客户端符号：`HeroData.get_Faction`（`0xE8D8A0`；第三节表格曾写成 `0xE8DBA8`，两者都未经证实）与图标查询 `0xC2197C`。契约无从验证，而该查询函数遇到不认识的 key **返回 NULL**，调用点 `if (icon_str)` 判空后**直接跳过写入**——不崩溃、不报错、徽章空白。加上客户端自己的 `RatingWidget.SetData` 走的是同一个 getter，hook 只是复现同一条坏链路。

### 6.3 现行实现（`tools/nativehook/hook.c`）
* `faction_icon_code()` / `faction_icon_glyph()`：本地 `if/switch` 映射表；**不再调用** `0xC2197C` 与 `0xE8D94C`。
* `hero_faction_str()`：优先读 blueprint 的 `AttributeBaseType`（`@0x70`，即 login-data 的 `a` 键），`HeroData.get_Faction`（`0xE8D8A0`）仅作兜底。
* 写入：`g_strnew(字形)` → 阵营 label（`0xDE127C`），并打印 `RATEWGT <bid> faction='...' glyph=U+.... label=...(<类名>) written`；取不到字形时打印 `-> NO glyph, badge blank`（`label=(非 Label 类名)` 表示 `widget+0x30` 的偏移判断也错了）。

### 6.4 数据侧铁律
`ROSTER.faction` 一律**小写**，且四处同名定义必须同步：`Server/gamedata.py`、`Server/bot_names_zh.json`、`bot_names_zh.json`、`Server/gamedata.lbl`（前者的 faction 会被发射到 blueprint `a`、characters `gen` / `hc` / `hero_colour`、userData `faction`）。野兽之战角色归属以客户端自带官方 bio 为准（`assets/xlate/snapshots/zh-CN/character_bios_zh-CN.json`：`ID_CHARACTER_BIOS_DINOBOT_BW` = 由原始兽转变而来的巨无霸；`ID_CHARACTER_BIOS_SCORPONOK_BW` = 原始兽）。

### 6.5 验证判定标准
真机 `logcat` 或 `/sdcard/Documents/tftf_*.log` 必须出现 `RATEWGT ... written`；BOTS 列表中黄豹 / 恐龙勇士 / 猩猩队长 / 犀牛显示 `U+E160`（巨无霸），黄蜂勇士 / 巨蝎勇士显示 `U+E161`（原始兽），其余角色仍为 `U+E134` / `U+E135`。
