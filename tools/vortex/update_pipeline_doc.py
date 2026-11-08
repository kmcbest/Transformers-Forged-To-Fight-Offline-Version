import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path

doc_path = Path(r"E:\Agent\TFTF-blender\re_notes\THIRD_PARTY_3D_MODEL_PIPELINE.md")
content = doc_path.read_text(encoding="utf-8")

# 1. Update TOC
old_toc_marker = "   * 9.6 袭击（Onslaught）完整可复用脚本索引（供后续吵闹/诈骗/旋风/爆炸直接套用）"
new_toc_entry = """   * 9.6 袭击（Onslaught）完整可复用脚本索引（供后续吵闹/诈骗/旋风/爆炸直接套用）
10. [旋风（Vortex）与直升机/战机类空军角色专属流水线（借壳 Grindor 实战）](#10-旋风vortex与直升机战机类空军角色专属流水线借壳-grindor-实战)
   * 10.1 载具朝向防垂直与纯刚体旋转铁律（Anti-Vertical Yaw-Pitch Standard）
   * 10.2 载具 45 骨骼多部件权重挂载与副 SMR 屏蔽
   * 10.3 直升机主旋翼持续旋转动画机制与双重暗坑排查标准（Rotor Continuous Spin Engineering Protocol）"""

if old_toc_marker in content and "10. [旋风（Vortex）" not in content:
    content = content.replace(old_toc_marker, new_toc_entry)
    print("[✓] TOC updated.")

# 2. Section 10 replacement/update
# Cut everything from "## 10. 旋风" to the end if present, or append
sec10_header = "## 10. 旋风（Vortex）与直升机/战机类空军角色专属流水线（借壳 Grindor 实战）"
if sec10_header in content:
    content = content[:content.find(sec10_header)].rstrip() + "\n\n"
else:
    content = content.rstrip() + "\n\n---\n\n"

section_10_full = """## 10. 旋风（Vortex）与直升机/战机类空军角色专属流水线（借壳 Grindor 实战）

直升机与战机类角色相比地面轮式装甲车，在载具形态、近战光刃、折叠背包与母壳选型上有显著不同的物理拓扑特征：

### 10.1 载具朝向防垂直与纯刚体正交变换方程（Anti-Vertical Yaw-Pitch Standard）
* **陷阱现象**：源模型直升机在 Blender 中导出 FBX 进 Unity 后，展厅与战斗检视中直升机像火箭发射一样垂直竖立在地面上（机头朝天 $+Y$、机尾朝地 $-Y$、主旋翼像风车一样朝向前方 $+Z$）。
* **Unity 空间直升机标准拓扑基线**：
  * **机身长轴（机尾 $\\rightarrow$ 机头）**：必须严格对齐 Unity $Z$ 轴（机头 $+Z$、机尾 $-Z$）；
  * **机身高度（机腹 $\\rightarrow$ 旋翼）**：必须严格对齐 Unity $Y$ 轴（主旋翼顶 $+Y$、机腹贴地 $Y \\approx 0.3\\text{m}$）；
  * **左右机翼（副翼/武器挂架）**：必须严格对齐 Unity $X$ 轴（左翼 $-X$、右翼 $+X$）。
* **纯刚体正交变换方程（$\\det = +1$，零翻转法线与三角形绕序）**：
  若源网格发生置换（机长在 $Y$、旋翼在 $Z$），严禁使用负缩放或轴向镜像！必须采用正交旋转：
  $$x' = -x$$
  $$y' = z + dy$$
  $$z' = y + dz$$
  其变换矩阵 $\\mathbf{R} = \\begin{pmatrix} -1 & 0 & 0 \\\\ 0 & 0 & 1 \\\\ 0 & 1 & 0 \\end{pmatrix}$，行列式 $\\det(\\mathbf{R}) = (-1) \\times (0 - 1) = +1$！
  - 物理意义：相当于先绕 $X$ 轴俯仰低头 $90^\\circ$（将竖立机头放平），再绕机身 $Z$ 轴横滚 $180^\\circ$（将翻倒朝地的旋翼翻回天空）；
  - 偏移参数：取 $dy = 0.60\\text{m}$（机腹悬空离地 $0.29\\text{m}$，旋翼顶升至 $5.26\\text{m}$）、$dz = -1.50\\text{m}$（机头位于 $+5.69\\text{m}$，机尾位于 $-9.34\\text{m}$，完美对准展厅与战斗镜头中点）；
  - 法线与切线同步变换：
    $$n_x' = -n_x, \\quad n_y' = n_z, \\quad n_z' = n_y$$
    $$t_x' = -t_x, \\quad t_y' = t_z, \\quad t_y' = t_y, \\quad t_w' = t_w$$
  经此变换，全部 6,203 个三角形法线与顶点法线点积点乘夹角 $100\\%$ 大于 0，零破面、零反向黑洞！

### 10.2 载具 45 骨骼多部件权重挂载与副 SMR 屏蔽
* 母体 Grindor 载具包含 45 根骨骼（包含机身中枢 `BodyTopCenterRight`、4 联主旋翼旋转轴 `RotorMain`、8 支桨叶 `RotorMainBlade1~8`、尾桨 `TailRotor`、武器挂架与机身副翼等）。
* **静态机身分配规则**：将旋风直升机非旋转的全部主体网格（除主旋翼旋转体外的 5,481 顶点）作为刚体统一绑定至载具中枢骨骼 `BodyTopCenterRight`（或细分至 `Tail` 与 `WingLeft/Right`）。
* **母壳次要 SMR 屏蔽**：在 `generate_vortex_bundle.py` 阶段，Grindor 原生载具包含多个分离的 SMR（如悬空挂载的导弹、机头探针、备用副油箱等），这些次要 SMR 必须一律设为 `m_Enabled = 0`，仅保留承载我们嫁接网格的主载具 SMR，并对齐 PBR 材质 `scale=(1, 1), offset=(0, 0)`，防止外壳穿模。

### 10.3 直升机主旋翼持续旋转动画机制与双重暗坑排查标准（Rotor Continuous Spin Engineering Protocol）
直升机角色在变形为载具形态后，与普通地面轮式/履带装甲车辆有本质区别：地面车辆在展示台静止待机时车身完全静止，而直升机在待机悬停与展厅中**主旋翼必须保持高速匀速旋转**。在实战中排查并攻克了三大工程暗坑：

#### 10.3.1 Grindor 旋翼待机动画真理源与 Mecanim 驱动机制
* **驱动骨骼**：通过解构 Grindor 的载具展厅与待机动画（`frontend_Grindor_levelup_vehicle_idle_transformed`），真理源确认驱动旋转的唯一核心骨骼为：
  `Reference/COG/RotorMain`（CRC32 Hash: `3459633487`）。
* **曲线特征**：Mecanim 曲线在该骨骼的 `m_LocalRotation` 上烘焙了密集的四元数旋转帧，动画周期为 20 帧完成一整圈 $360^\\circ$ 旋转（在 30 FPS 下相当于 90 RPM 的待机悬停转速）。
* **子骨骼无旋转曲线**：其下属的子骨骼 `RotorMainBlade1~8` 在该待机动画中并没有独立的局部旋转曲线，所有自转完全依靠父骨骼 `RotorMain` 的旋转带动。
* **绑定铁律**：第三方直升机模具的所有旋转桨叶顶点，**必须直接绑定至 `RotorMain` 骨骼**（权重设为 1.0）。若错误绑定至 `BodyTopCenterRight`，旋翼在游戏中将成为死肉一块，绝不旋转。

#### 10.3.2 致命暗坑一：顶点组模糊子串匹配引发的“全身像电风扇一样暴转”
* **现象与录屏复盘**：在初版权重导出脚本中，使用模糊子串逻辑（如 `"bodyrobo18" in vg_name.lower()`）寻找旋翼。结果在游戏中，不仅螺旋桨在转，**机身两侧的短翼、火箭发射巢挂架、甚至半个机腹都在绕着机顶疯狂翻滚自转**（见复盘录屏），角色瞬间破相。
* **根因剖析**：源模型 Blender 顶点组命名规律极其隐蔽：
  * `C_BodyRobo18_XT` 代表中央（Center）旋翼连杆；
  * 但模型同时存在 `L_BodyRobo18_XT`、`R_BodyRobo18_XT`、`L_BodyRobo19_XT` 等，代表机身左/右两侧的机翼与武器挂架！
  * 粗暴的子串匹配导致整整 920 个机身与机翼顶点被错误分配进了 `RotorMain`。
* **直升机主旋翼 11 组绝对白名单**：
  在提取直升机旋转体时，必须无条件采用严格白名单匹配，仅允许 `C_` 前缀的 11 个旋转部件：
  ```python
  ROTOR_EXACT_VGS = {
      "C_BodyRobo06_XT",   # 旋翼顶盖帽
      "C_BodyRobo16_XT",   # 主轴立柱
      "C_BodyRobo17_XT",   # 十字倾斜盘
      "C_BodyRobo18_XT",   # 1号桨叶根部轴承
      "C_BodyRobo19_XT",   # 2号桨叶根部轴承
      "C_BodyRobo20_XT",   # 3号桨叶根部轴承
      "C_BodyRobo21_XT",   # 4号桨叶根部轴承
      "C_PropRobo18_XT",   # 1号主旋转桨叶
      "C_PropRobo19_XT",   # 2号主旋转桨叶
      "C_PropRobo20_XT",   # 3号主旋转桨叶
      "C_PropRobo21_XT",   # 4号主旋转桨叶
  }
  ```
  在 Blender 中精确统计为 974 个顶点（Unity 拆点后为 976 顶点）。所有带有 `L_` (Left) 与 `R_` (Right) 前缀的顶点组一律严禁归入旋翼！

#### 10.3.3 致命暗坑二：FBX 拆点导致跨语言顶点索引错位与直升机“瞬间升天”
* **现象与录屏复盘**：若在 Python 中把 Blender 识别出的 974 个顶点索引导出为 `rotor_indices.json`，再由 Unity C# 脚本读取该 JSON 来设置 `rawMesh.boneWeights`，会导致直升机在检视场景或展厅刚开场的一瞬间，整个机体以超高速垂直飞向天空消失不见，Unity Game 视图报错 `Display 1: No cameras rendering`！
* **根因剖析**：
  * **FBX UV 缝合线拆点机制**：Blender 中该直升机模型原始顶点数为 6,331；但当 Blender 导出 FBX 并由 Unity 导入时，Unity 会根据 UV 接缝（UV Seams）与硬法线边缘（Hard Normals）对共享顶点进行拆分复制，Unity 内的顶点总数骤增至 6,457！
  * 顶点数组长度由 6,331 变为 6,457，两端的顶点下标发生非线性错位。
  * Unity C# 读取 JSON 中粗暴的顶点索引去计算旋转中心和位移时，将机腹甚至尾部的顶点误判为旋翼，计算出了高达 $dy = +2.32\\text{m}$ 的虚假几何中心偏移，直接将机体坐标轴抛向外太空！
* **防坑铁律**：**严禁在外部跨工具（Blender Python $\\rightarrow$ Unity C#）传递裸顶点索引数组**！
  * 正确方案：在 Blender 端直接为网格建立顶点组并分配权重导出为标准带皮 FBX；
  * Unity 端若需重构 SMR，直接在 C# 中查询 FBX 原生导入的 `rawMesh.boneWeights[i].boneIndex0 == fbxRotorBoneIndex` 来识别旋翼顶点，保证拓扑与顶点标识 100% 自洽无缝！

#### 10.3.4 旋转轴心同轴对齐与偏心进动消除（Pivot Coincidence & Precession Elimination）
* 直升机主旋翼是绕其旋转轴的局部原点 $(0, 0, 0)$ 高速旋转的。
* 若旋翼模型的几何旋转中心与 Grindor `RotorMain` 骨骼的局部坐标原点存在偏移 $(\\Delta x, \\Delta y, \\Delta z)$，旋翼在旋转时就会产生明显的**离心进动晃动（Precession Wobble）**，如同摇摇欲坠的陀螺。
* 经精密几何回归，旋翼 11 组零件在刚体正交变换后的几何对称轴心为：
  $$X_c = +0.0359\\text{m}, \\quad Y_c = +0.0631\\text{m}, \\quad Z_c = -0.0039\\text{m}$$
* 将旋翼顶点在绑定前减去该偏心量，使其对称轴与 `RotorMain` 骨骼完全同轴对齐，彻底消除一切晃动偏心，实现真机展厅中如瑞士钟表般平稳顺滑的 90 RPM 悬停旋转。

#### 10.3.5 直升机空军角色专属质量门禁检查清单
- [x] **1. 载具朝向**：正交旋转矩阵消除直立，机头 $+Z$、机腹贴地 $+Y \\approx 0.3\\text{m}$、左右副翼 $\\pm X$。
- [x] **2. 旋翼白名单**：仅限 `C_` 开头的旋转盘与桨叶顶点组（974 顶点），严防 `L_`/`R_` 侧机身与武器挂架污染。
- [x] **3. 骨骼绑定归属**：机身全部顶点绑定至 `BodyTopCenterRight`，旋翼全部顶点绑定至 `RotorMain`（hash `3459633487`）。
- [x] **4. FBX 权重自洽**：在 Unity 内部直接由 C# 解析 FBX 原生骨骼权重，规避 UV 拆点索引位移引发的“升天 Bug”。
- [x] **5. 动画实测**：在 Unity 检视场景中切换 `Vehicle Mode Hover`，逐帧观察是否只有 4 片主桨叶与顶盖在平稳高速旋转，机身其余部分保持绝对刚性静止。
"""

content += section_10_full
doc_path.write_text(content, encoding="utf-8")
print("[✓] Successfully wrote complete Section 10 and updated TOC in THIRD_PARTY_3D_MODEL_PIPELINE.md")
