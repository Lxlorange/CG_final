可以。根据课程要求，你的论文最好不是“用 AI 生成一张图”，而是围绕一个明确 CG 过程，设计“传统流程 vs 大模型辅助流程”的实验，并比较质量、控制性、效率和局限。课程文件也明确要求论文包含摘要、引言、相关技术现状、方法设计、实验与对比、结果讨论、参考文献等部分。

我建议你优先选这个题目：

**题目建议：基于大语言模型的文本驱动 3D 室内场景布局生成与传统规则方法对比**

这个题目最适合课程论文，因为实现难度可控：不用真正训练 3D 生成模型，只需要让大模型把自然语言描述解析成“场景图 / JSON / Blender Python 参数”，再由传统 CG 工具完成建模、布局和渲染。它也非常符合课程要求中的“场景建模”“大模型参与输入理解与 pipeline 优化”“有无大模型对比”。

### 一、推荐参考论文列表

| 类别                 | 论文                                                                                                 | 你可以怎么用                                                                                                |
| ------------------ | -------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| LLM + 场景布局         | **LayoutGPT: Compositional Visual Planning and Generation with Large Language Models**             | 这篇最贴近你的题目。它把 LLM 当作 visual planner，把文本条件转成布局，覆盖 2D 图像和 3D 室内场景，适合写“LLM 负责语义理解和空间规划”的理论依据。([arXiv][1]) |
| LLM + Blender 场景生成 | **An LLM Agent for Synthesizing 3D Scene as Blender Code / SceneCraft**                            | 这篇可以支持你的实现路线：让 LLM 输出 Blender 可执行脚本，完成物体放置、空间关系、材质和渲染设置。([arXiv][2])                                  |
| 指令驱动 3D 室内场景       | **InstructScene: Instruction-Driven 3D Indoor Scene Synthesis with Semantic Graph Prior**          | 可用于说明“自然语言指令—语义图—布局解码”的方法链路，尤其适合写控制性与空间关系。([arXiv][3])                                                |
| 布局约束 3D 场景生成       | **SceneCraft: Layout-Guided 3D Scene Generation**                                                  | 适合写“布局约束比纯文本生成更可控”。它用 3D semantic layout 转成多视角 proxy map，再生成 NeRF 场景。([arXiv][4])                     |
| 语言到 3D 场景          | **SceneTeller: Language-to-3D Scene Generation**                                                   | 可以作为语言驱动 3D 场景生成的近邻工作，适合放在相关工作中补充。([ECVA][5])                                                         |
| 传统 / 深度场景合成基线      | **ATISS: Autoregressive Transformers for Indoor Scene Synthesis**                                  | 可作为“非 LLM 的学习式室内场景布局方法”参考。它根据房间类型和平面图生成家具布局，适合作为传统 AI/深度学习基线文献。([arXiv][6])                           |
| 传统 / 深度场景合成基线      | **SceneFormer: Indoor Scene Generation with Transformers**                                         | 可用于说明 LLM 出现前，场景生成常被建模为对象序列生成或布局预测问题。([arXiv][7])                                                     |
| 程序化建模              | **Procedural Modeling of Buildings**                                                               | 可作为传统 CG 程序化建模代表，说明“规则、语法、参数化建模”的优势与局限。([Peter Wonka][8])                                             |
| 文本到 3D 场景          | **Text2Room: Extracting Textured 3D Meshes from 2D Text-to-Image Models**                          | 如果你想扩展到“纹理化房间场景”，这篇很有用。它从文本生成多视角图像，再结合深度估计和 inpainting 融合成 textured 3D mesh。([arXiv][9])              |
| 文本到 3D 物体          | **DreamFusion: Text-to-3D using 2D Diffusion**                                                     | 适合写背景：早期 text-to-3D 通过 2D diffusion prior 和 SDS 绕开大规模 3D 数据不足问题。([arXiv][10])                         |
| 高质量 text-to-3D     | **Magic3D: High-Resolution Text-to-3D Content Creation**                                           | 可用于说明 text-to-3D 从低分辨率 NeRF 到高分辨率 mesh 的 coarse-to-fine pipeline。([arXiv][11])                        |
| 高效 3D 生成           | **DreamGaussian: Generative Gaussian Splatting for Efficient 3D Content Creation**                 | 如果你想讨论效率，可以引用它。它用 3D Gaussian Splatting 提高 3D 生成速度，并能输出 textured mesh。([arXiv][12])                   |
| 条件式 3D 资产生成        | **Shap-E: Generating Conditional 3D Implicit Functions**                                           | 可作为“文本/图像条件生成 3D 资产”的背景文献，尤其适合说明从 prompt 到 3D asset 的生成模型路线。([arXiv][13])                             |
| 纹理生成               | **TexFusion: Synthesizing 3D Textures with Text-Guided Image Diffusion Models**                    | 如果你的题目改成“AI 辅助材质与纹理生成”，这篇是核心文献。它强调多视角一致性和给定 mesh 的文本引导贴图生成。([arXiv][14])                              |
| 材质生成               | **ControlMat: A Controlled Generative Approach to Material Capture**                               | 适合材质方向：从单张自然光照片生成可平铺、高分辨率、PBR 材质通道。([arXiv][15])                                                      |
| 光照生成               | **Text2Light: Zero-Shot Text-Driven HDR Panorama Generation**                                      | 如果你选“AI 辅助光照与渲染设计”，这篇最相关。它根据文本生成 HDR panorama，可用于真实感照明和 VR 场景。([arXiv][16])                           |
| 几何与外观解耦            | **Fantasia3D: Disentangling Geometry and Appearance for High-quality Text-to-3D Content Creation** | 可用于说明 text-to-3D 中“几何—材质—渲染”分离的重要性，尤其适合讨论可编辑性和 relighting。([arXiv][17])                               |

如果你的时间有限，建议重点读这 6 篇：**LayoutGPT、SceneCraft as Blender Code、InstructScene、ATISS、Text2Room、TexFusion 或 Text2Light**。前四篇支撑主线，后两篇用于扩展材质/光照讨论。

### 二、建议论文核心思路

你的论文可以围绕这样一个问题展开：

**传统 CG 规则流程能否根据自然语言构建合理 3D 场景？引入大语言模型后，是否能提升语义理解、空间关系表达、布局合理性和制作效率？**

传统方法可以设计成：你预先写一套规则，例如“卧室必须有床、床靠墙、床头柜在床两侧、桌子靠窗、椅子在桌前”。输入只能是结构化参数，比如房间大小、房间类型、家具数量。然后 Blender 脚本根据规则自动摆放模型。

大模型方法可以设计成：用户输入自然语言，例如“一个小型卧室，床靠左墙，书桌靠窗，椅子在书桌前，地毯位于床边，整体为暖色调”。大模型先把文本解析为 JSON 场景描述，包括物体类别、尺寸、位置、朝向、相对关系、材质风格、光照风格。然后 Blender 脚本读取 JSON，自动生成场景。

这样你就不是在写“AI 画图”，而是在构建一个 **自然语言 → 语义场景图 → 3D 布局 → 材质/光照 → 渲染结果** 的 CG pipeline。

### 三、可写的方法设计

你可以把方法分成四个模块：

第一，输入解析模块。传统方法只接受结构化输入，例如 `room_type=bedroom, bed_count=1, desk=True`。大模型方法接受自然语言输入，并输出结构化 JSON。

第二，场景图生成模块。让大模型输出类似这样的结构：

```json
{
  "room": {"type": "bedroom", "size": [5, 4, 3]},
  "objects": [
    {"name": "bed", "position": "against left wall", "style": "modern"},
    {"name": "desk", "position": "near window", "style": "wooden"},
    {"name": "chair", "position": "in front of desk"},
    {"name": "rug", "position": "beside bed"}
  ],
  "lighting": {"style": "warm evening", "intensity": "medium"}
}
```

第三，Blender 生成模块。你用 Python 脚本读取 JSON，调用预置模型或简单几何体生成物体，完成位置、比例、旋转、材质和灯光设置。

第四，渲染与评价模块。输出俯视图、透视图和若干实验表格，对比传统方法和大模型方法。

### 四、实验设计

实验不要太大，建议做 10 到 20 条文本输入，分成三类：

简单描述：
“生成一个卧室，有床、桌子、椅子和衣柜。”

空间关系描述：
“床靠左墙，桌子靠窗，椅子在桌子前方，地毯在床右侧。”

风格与功能描述：
“生成一个适合学生学习的小卧室，整体简洁，光照温暖，桌面区域明亮。”

对比组可以这样设计：

| 组别     | 方法              | 输入             | 输出                |
| ------ | --------------- | -------------- | ----------------- |
| A 组    | 传统规则方法          | 结构化参数          | 固定模板场景            |
| B 组    | LLM 零样本         | 自然语言           | JSON + Blender 场景 |
| C 组    | LLM + 约束 prompt | 自然语言 + 输出格式约束  | 更稳定的 JSON + 场景    |
| D 组，可选 | LLM + 人工修正      | 初始 JSON + 人工编辑 | 半自动协同场景           |

评价指标可以用这些：

一是**物体完整率**：文本中提到的物体有多少被正确生成。

二是**空间关系准确率**：例如“床靠墙”“椅子在桌前”“地毯在床边”是否满足。

三是**碰撞率**：物体之间是否重叠，是否穿墙。

四是**布局合理性**：可以人工打分，1 到 5 分。

五是**制作效率**：记录每个场景从输入到渲染完成的时间，以及人工修改次数。

六是**稳定性**：同一个 prompt 运行 3 次，看输出是否一致，是否出现 JSON 格式错误或空间关系错误。

这些指标刚好对应课程要求中的结果质量、控制性、效率和新问题分析。

### 五、论文结构建议

你的论文可以按这个结构写：

**摘要**：说明你提出了一个 LLM 辅助的文本到 3D 室内场景布局 pipeline，并与传统规则方法比较。

**引言**：写传统 3D 场景制作依赖人工建模和规则脚本，普通用户很难把自然语言需求转成可执行 CG 流程。大模型可以承担语义解析和空间关系规划，但也会带来不稳定、不可预测和几何不一致问题。

**相关技术现状**：分三部分写：传统程序化建模与室内场景合成；文本/语言驱动 3D 场景生成；AI 辅助材质、光照和渲染。

**方法设计**：介绍你的系统流程：自然语言输入、LLM 解析、JSON 场景图、Blender 脚本生成、材质光照设置、渲染输出。

**实验与对比**：列出 prompt 集合、对比组、评价指标、实验结果截图和表格。

**结果讨论**：重点讨论大模型的提升和局限。提升包括输入更自然、空间关系表达更强、风格控制更灵活、人工建模时间减少。局限包括输出格式偶尔错误、空间关系可能误解、物体尺寸不一致、复杂场景中容易碰撞、不同运行结果不稳定。

**结论**：总结大模型更适合作为 CG pipeline 中的“语义规划器”和“参数生成器”，而不是完全替代传统图形学流程。

### 六、可以直接采用的论文题目

你可以选下面其中一个：

**《基于大语言模型的文本驱动 3D 室内场景布局生成方法研究》**

**《面向自然语言输入的 3D 场景自动构建：传统规则方法与大模型辅助方法对比》**

**《大语言模型辅助的 Blender 场景生成 Pipeline 设计与实验分析》**

我最推荐第三个，题目更工程化，容易和你的实现对应，也更符合课程“设计并实现一个结合大模型的方法”的要求。

[1]: https://arxiv.org/abs/2305.15393?utm_source=chatgpt.com "LayoutGPT: Compositional Visual Planning and Generation with Large Language Models"
[2]: https://arxiv.org/abs/2403.01248?utm_source=chatgpt.com "An LLM Agent for Synthesizing 3D Scene as Blender Code"
[3]: https://arxiv.org/abs/2402.04717?utm_source=chatgpt.com "InstructScene: Instruction-Driven 3D Indoor Scene ..."
[4]: https://arxiv.org/abs/2410.09049?utm_source=chatgpt.com "SceneCraft: Layout-Guided 3D Scene Generation"
[5]: https://www.ecva.net/papers/eccv_2024/papers_ECCV/papers/11481.pdf?utm_source=chatgpt.com "SceneTeller: Language-to-3D Scene Generation"
[6]: https://arxiv.org/abs/2110.03675?utm_source=chatgpt.com "ATISS: Autoregressive Transformers for Indoor Scene Synthesis"
[7]: https://arxiv.org/abs/2012.09793?utm_source=chatgpt.com "SceneFormer: Indoor Scene Generation with Transformers"
[8]: https://peterwonka.net/Publications/pdfs/2006.SG.Mueller.ProceduralModelingOfBuildings.final.pdf?utm_source=chatgpt.com "Procedural Modeling of Buildings"
[9]: https://arxiv.org/abs/2303.11989?utm_source=chatgpt.com "Text2Room: Extracting Textured 3D Meshes from 2D Text-to-Image Models"
[10]: https://arxiv.org/abs/2209.14988?utm_source=chatgpt.com "[2209.14988] DreamFusion: Text-to-3D using 2D Diffusion"
[11]: https://arxiv.org/abs/2211.10440?utm_source=chatgpt.com "Magic3D: High-Resolution Text-to-3D Content Creation"
[12]: https://arxiv.org/abs/2309.16653?utm_source=chatgpt.com "DreamGaussian: Generative Gaussian Splatting for Efficient 3D Content Creation"
[13]: https://arxiv.org/abs/2305.02463?utm_source=chatgpt.com "Shap-E: Generating Conditional 3D Implicit Functions"
[14]: https://arxiv.org/abs/2310.13772?utm_source=chatgpt.com "TexFusion: Synthesizing 3D Textures with Text-Guided Image Diffusion Models"
[15]: https://arxiv.org/abs/2309.01700?utm_source=chatgpt.com "ControlMat: A Controlled Generative Approach to Material Capture"
[16]: https://arxiv.org/abs/2209.09898?utm_source=chatgpt.com "Text2Light: Zero-Shot Text-Driven HDR Panorama Generation"
[17]: https://arxiv.org/abs/2303.13873?utm_source=chatgpt.com "Fantasia3D: Disentangling Geometry and Appearance for High-quality Text-to-3D Content Creation"
