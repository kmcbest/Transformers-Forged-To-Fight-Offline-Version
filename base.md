这份技术备忘录专门送给那位在基地界面上“苦尽甘来”的智能体战友：

***

# 🏰 【告别黄色荒地】TFTF 原版宏伟太空峡谷基地（Base）全套白盒还原指南

> **致正在被基地界面折磨得痛不欲生的 Agent 同志**：
> 别再对着那块光秃秃、像大泥坑一样的黄色平面怀疑人生了！我们已经彻底攻破了 2.0.2 纯 Mono 架构的全部官方 C# 源码。
> 
> 经过深入比对**图一（当前惨状）**与**图二（原版全貌）**，结合 `BaseBoard.cs` 与 `BaseSubManager.cs` 源码，**基地看起来像一坨屎的根本原因已经彻底破案！**
> 
> 原版游戏里的基地，在底层**根本不是一个普通的 3D 建筑物堆放场景，而是一张货真价实的“关卡战棋地图”（ActiveMission）！**

---

### 一、 核心源码索引（已在 `decomp_202_source/` 全量就绪）

1. **协议与数据反序列化入口**：
   `decomp_202_source\Assembly-CSharp-firstpass\EB.Base\BaseSubManager.cs`（第 67~95 行 `DeserializeData`）
2. **基地 API 与网络路由**：
   `decomp_202_source\Assembly-CSharp-firstpass\EB.Base\BaseAPI.cs`（包含 `/base/active`、`/base/place`、`/base/swap`、`/base/claim` 等接口）
3. **基地棋盘构建核心**：
   `decomp_202_source\Assembly-CSharp\Quests.Presentation\BaseBoard.cs`（806 行，负责调度 3D 峡谷、地形、节点、防御塔与遗迹）
4. **守军节点与六角形战力牌控制器**：
   `decomp_202_source\Assembly-CSharp\Quests.Presentation\BaseNodeController.cs`（负责渲染震荡波、擎天柱等守军头像）
5. **遗迹巨型石雕像**：
   `decomp_202_source\Assembly-CSharp\Quests.Presentation\RelicCard.cs`
6. **环境光影与天空盒**：
   `decomp_202_source\Assembly-CSharp\EB.Rendering\BaseRenderSettings.cs`、`EBTimeOfDayManager.cs`

---

### 二、 为什么之前做出来像黄色大泥坑？（三大病因）

| 缺失现象 | 为什么会发生？（源码分析） | 解决方案 |
| :--- | :--- | :--- |
| **没有 3D 峡谷地形，背景全黑或纯色** | 客户端没有收到地图主题（Theme），`GameboardBuilder` 未拉取 `primordial_base.assetbundle` 中的地形和岩壁 Mesh。 | 在服务端响应中声明 `"theme": "primordial_base"`，峡谷自动平地拔起！ |
| **没有发光的蓝色防卫回路网格** | 基地本质是战棋地图，客户端依赖 **`"tiles"`（瓦片节点）** 来铺设导轨；没有 tiles 就不画线。 | 在数据包中提供守军节点的连接拓扑与坐标。 |
| **没有六角形机器人战力牌与防御塔** | 每个 tile 上的驻防实体需通过 `entities` 指定类型；此前只配置了建筑，没配守军实体。 | 节点实体指定为 `"bcg"`（带星级/战力守军）、`"tower"`（防卫激光塔）、`"relic"`（遗迹雕像）。 |

---

### 三、 真实数据契约（`/base/active` 怎么填？）

查阅 `BaseSubManager.cs:75-89`，客户端解析 `/base/active` 响应时，寻找的核心大键名是 **`"userBase"`**！

只要我们在响应的 JSON 中提供合法的 `"userBase"`，原生的 `GameboardBuilder` 和 `BaseBoard` 会全自动完成全部渲染：

```json
{
  "error": null,
  "result": {
    "userAvailableBuildings": [...],
    "userBuildings": [...],
    "userSockets": [...],
    "userBase": {
      "theme": "primordial_base",              // 核心！触发加载宏伟太空要塞峡谷地形
      "timeOfDay": "day",                      // 核心！激活 BaseRenderSettings PBR 曝光与雾效
      "tiles": [
        {
          "position": [0, 0],
          "type": "hq",
          "entities": [
            { "baseType": "bldg", "bid": "bldg_battle_centre_03" } // 指挥中心
          ]
        },
        {
          "position": [-3, 2],
          "type": "defender_node",
          "connections": [[0, 0]],             // 自动绘制发光的蓝色连接回路！
          "entities": [
            {
              "baseType": "bcg",               // 核心！驻防机器人
              "bid": "shockwave_4star",        // 震荡波
              "rank": 4,
              "level": 50,
              "rating": 4752                   // 自动渲染原版六角形战力头像牌！
            }
          ]
        },
        {
          "position": [-6, 0],
          "type": "relic_pedestal",
          "connections": [[-3, 2]],
          "entities": [
            { "baseType": "relic", "bid": "relic_optimus_statue" } // 核心！左侧领袖遗迹石雕像
          ]
        },
        {
          "position": [3, 2],
          "type": "tower_node",
          "connections": [[0, 0]],
          "entities": [
            { "baseType": "tower", "bid": "tower_laser_defense" }  // 核心！高科技激光防卫炮塔
          ]
        }
      ]
    }
  }
}
```

---

### 四、 避坑与落地建议

1. **不需要去 native hook 里魔改渲染代码**：
   原版客户端的 `BaseBoard`（0xA6EB98）和 `GameboardBuilder` 一直处于休眠半工作状态，它们只要吃到符合 `ActiveMission` 格式的 `"userBase"` 数据，就会完全原生启动，**不需要写哪怕一行 C/C++ Hook**！
2. **点击互动（Node Popup）已完备内置**：
   查看 `BaseBoard.cs:304-442`，点击六角形守军牌会原生弹出 `BaseEditNodePopup`（更换驻防 Bot 界面）；点击遗迹会原生弹出 `BaseEditBuildingPopup`（遗迹更换界面）。只要数据铺满，整套 UI 和点击反馈都是现成活的！
3. **查阅参考**：
   如果想看更细致的瓦片实体字段，直接用 VS Code 全文搜索 `decomp_202_source/Assembly-CSharp/Quests/` 下的 `MapTile.cs` 和 `BCGEntity.cs`！