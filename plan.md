# 结课论文计划：基于神经渲染的图像驱动三维场景重建与传统图形渲染流程对比

## 1. 选题定位

原题“基于大语言模型的文本驱动室内家具布局生成与规则方法对比”更接近自动布局、程序化建模或内容生成，虽然可以纳入计算机图形学讨论，但它的核心矛盾容易落在文本理解和场景语义规划上，图形学过程本身不够突出。新的选题应将问题收束到渲染与三维表示：给定一组同一场景的多视角图像，传统图形学流程通常需要显式几何重建、网格清理、纹理映射、材质与光照设置，再通过光栅化或路径追踪生成新视角；神经渲染则学习一个可微的场景表示，通过体渲染、神经场查询或高斯 splatting 直接合成新视角图像。

建议论文题目：

**基于神经渲染的图像驱动三维场景重建与传统图形渲染流程对比**

可选副标题：

**以 NeRF 与 3D Gaussian Splatting 的新视角合成为例**

该题目比“文本驱动布局生成”更贴近课程中的建模、相机、光照、可见性、体渲染、采样、图像合成等知识点，也能自然回答作业要求中的四个核心问题：结果质量、控制性、效率和新局限。

## 2. 核心研究问题

本文不讨论“AI 直接生成一张图片”这一类二维生成问题，而讨论神经渲染如何改变传统三维图形管线。核心问题定义为：

1. 在多视角图像输入下，传统几何重建加显式渲染流程与神经渲染流程分别如何构建可渲染的三维场景表示？
2. 神经渲染是否提升新视角合成质量，尤其是在细节纹理、复杂材质、半透明/反光区域和遮挡边界上是否优于传统网格与纹理流程？
3. 神经渲染是否提高流程效率，包括建模成本、人工处理时间、训练或优化时间、渲染速度和复现实验难度？
4. 神经渲染是否降低控制性，例如几何结构不显式、材质和光照难以独立编辑、相机外推不稳定、训练视角不足时出现漂浮物或几何不一致？

这里的“有无模型”对比应明确为：无神经模型的传统 CG/视觉重建管线，与引入神经场或可微辐射场后的神经渲染管线。NeRF、Instant-NGP、TensoRF、Plenoxels 和 3D Gaussian Splatting 都不是简单的图像生成器，而是学习或优化一个可从连续视角渲染的场景表示。

## 3. 相关技术现状的组织方式

相关技术现状建议分四条线展开，每条线服务后续实验设计，而不是堆论文。

第一条线是传统图形学与图像式重建流程。传统流程依赖显式几何和物理或近似物理的渲染模型：通过 SfM/MVS 获取相机位姿和稠密点云，生成网格，进行纹理映射，再在 Blender、Unity 或其他渲染器中设置材质、光照和相机。该流程的优点是几何、材质和光照具有清晰的编辑接口，缺点是重建破损、反光和细薄结构容易出错，手工清理成本较高。

第二条线是 NeRF 及神经辐射场。NeRF 将场景表示为从三维位置和观察方向到密度、颜色的连续函数，再用经典体渲染公式合成图像。该方向应重点说明它并未抛弃图形学，而是把体渲染、相机射线采样、可微优化和神经网络表示结合起来。

第三条线是加速与显式化的神经渲染。Instant-NGP、PlenOctrees、SNeRG、Plenoxels、TensoRF 和 Zip-NeRF 都在解决 NeRF 训练慢、渲染慢或抗锯齿不足的问题。3D Gaussian Splatting 进一步将场景表示为可优化的三维高斯集合，用可微 splatting 实现实时新视角渲染，是本文实验最适合作为高效神经渲染方法的代表。

第四条线是几何、控制和真实场景鲁棒性。NeuS、VolSDF、DeepSDF 讨论隐式表面和 SDF 表示，BARF 讨论相机位姿误差，NeRF-W 讨论非受控照片中的光照变化和临时遮挡，RegNeRF 和 pixelNeRF 讨论稀疏输入下的先验与正则。这些工作可用于结果讨论部分解释神经渲染的局限：高质量图像不等于可编辑几何，少视角或错误位姿会显著影响稳定性。

## 4. 方法设计

本文方法部分不写成“调用某个工具”的说明，而写成两个可比较的图形学管线。

### 4.1 传统显式重建与渲染管线

输入为同一静态场景的多视角图像。首先使用 COLMAP 或同类 SfM 方法估计相机内外参并重建稀疏点云；再通过 MVS 或深度估计获得稠密点云和三角网格；随后进行网格清理、法线修正、纹理映射和材质设置；最后在 Blender 中采用固定相机路径输出测试视角图像。该管线对应传统 CG 思路：场景由显式几何、纹理、材质、光照和相机组成，渲染器根据这些可解释对象生成图像。

### 4.2 神经辐射场管线

同样输入多视角图像和相机位姿。NeRF 类方法用 MLP 或混合网格结构表示体密度与视角相关辐射度，对每条相机射线采样多个空间点，并通过体渲染积分得到像素颜色。训练目标是使渲染图像与训练图像一致。该管线应突出两点：一是它仍然使用相机射线、体密度、透射率和图像形成模型；二是场景表示由手工建模转为数据驱动优化。

### 4.3 高效神经渲染管线

为避免只比较原始 NeRF 的慢速版本，实验中加入 Instant-NGP 或 3D Gaussian Splatting。Instant-NGP 通过多分辨率哈希编码减少网络计算，3D Gaussian Splatting 则从 SfM 点云初始化三维高斯，优化位置、协方差、透明度和球谐颜色，并通过可微 splatting 进行实时渲染。该管线适合和传统显式渲染比较效率，也适合讨论“神经表示是否牺牲可控性”。

### 4.4 对比逻辑

三条流程的输入、相机路径和测试视角保持一致：

1. 传统流程：SfM/MVS/mesh/texture/Blender 渲染。
2. NeRF 流程：基于相机位姿训练辐射场并进行体渲染。
3. 高效神经渲染流程：Instant-NGP 或 3DGS 优化场景表示并实时渲染。

这样实验比较的不是“哪张图更好看”，而是三种图形学过程在表示形式、渲染方式、可编辑性和效率上的差异。

## 5. 实验设计

### 5.1 数据选择

优先选择公开数据集或可快速复现实验的数据：

1. Blender Synthetic / NeRF Synthetic：相机位姿准确、可得到无噪声测试图，适合做 PSNR、SSIM、LPIPS 的定量比较。
2. LLFF 或 Mip-NeRF 360 场景：真实照片场景，适合观察反光、薄结构、边界和远近尺度变化。
3. 自采小场景：如桌面物体、教室角落或室内摆件，用手机环绕拍摄 40-80 张照片，作为课程展示图文材料。

如果时间有限，建议以公开数据为主，自采数据作为定性展示。

### 5.2 变量设置

实验变量围绕作业要求设计：

1. 方法变量：传统 mesh+texture 渲染、原始 NeRF 或 Nerfstudio-NeRF、Instant-NGP 或 3D Gaussian Splatting。
2. 输入视角变量：完整视角、稀疏视角、局部遮挡或较大视角外推。
3. 控制变量：固定相机路径、固定输出分辨率、固定训练/优化预算，尽量使用相同训练/测试划分。
4. 流程变量：人工清理网格的传统流程、少量参数调节的 AI 辅助流程、脚本化自动重建流程。

### 5.3 指标设计

定量指标：

1. PSNR：衡量像素级重建误差，适合公开数据集的测试视角。
2. SSIM：衡量结构相似度，适合比较边缘和纹理结构。
3. LPIPS：衡量感知相似度，适合说明人眼感知质量。
4. 训练或重建时间：从输入图像到可渲染表示的总耗时。
5. 单帧渲染时间或 FPS：比较实时交互能力。
6. 模型或资产大小：比较存储成本。

定性指标：

1. 视角外推时是否出现漂浮物、空洞、拉伸纹理或模糊。
2. 反光、透明、细薄结构和遮挡边缘是否稳定。
3. 是否能够单独编辑几何、材质、光照和相机。
4. 是否可以导出可供传统引擎使用的 mesh、texture、obj、glb 或 ply。

### 5.4 预期结果

预期传统流程在几何编辑和引擎兼容性上更强，但在复杂外观和手工处理成本上较弱。NeRF 类方法在训练视角附近的新视角合成质量上通常更好，但训练和渲染成本较高，几何显式性较弱。3D Gaussian Splatting 预计在渲染速度和视觉质量之间取得较好平衡，但可能带来较大显存占用、外推视角 artifacts、光照和材质不可分离等问题。

## 6. 论文结构规划

摘要：概括问题、方法、对比实验和主要结论。摘要应强调神经渲染改变的是三维场景表示和渲染过程，而不是二维图片生成。

引言：从传统图形学管线切入，说明显式几何、材质、光照和相机组成了可控但成本较高的渲染流程；再引出神经渲染通过多视角图像学习场景表示，改变了重建与渲染的分工；最后给出本文比较问题。

相关技术现状：按“传统重建与显式渲染”“NeRF 与体渲染”“高效神经渲染与 3DGS”“几何控制与真实场景鲁棒性”四部分组织。

方法设计：写清传统管线、NeRF 管线和高效神经渲染管线的输入输出、核心表示、渲染方程或渲染过程，以及为什么它们可公平对比。

实验与对比：展示数据集、实验设置、指标表格、图像对比、相机路径截图、时间和资源消耗。

结果讨论：围绕质量、控制性、效率和局限逐项回答作业要求。重点讨论神经渲染的边界：它能以图像监督获得逼真的新视角，但不天然提供完全可编辑的几何、材质和光照分解。

参考文献：采用神经渲染综述、NeRF 基础论文、效率改进、几何重建和真实场景鲁棒性相关论文。

## 7. 图表计划

1. 传统 CG/重建渲染管线图：图像采集 -> SfM/MVS -> mesh/texture -> material/light -> render。
2. NeRF 管线图：图像和位姿 -> 坐标编码/MLP 或网格 -> 射线采样 -> 体渲染 -> 新视角。
3. 3DGS 管线图：SfM 点云 -> 三维高斯初始化 -> 高斯参数优化 -> splatting 渲染。
4. 测试视角对比图：Ground truth、传统 mesh、NeRF、3DGS 并列。
5. 指标表：PSNR、SSIM、LPIPS、训练时间、FPS、资产大小。
6. 局限案例图：少视角、反光、边界漂浮物、视角外推失败。

## 8. 已核对摘要的参考文献与引用位置

以下论文均已核对到原文摘要页或出版页摘要，数量为 20 篇，不少于原计划的 17 篇；其中 [1] 和 [2] 为综述类文献，满足至少包含一篇综述论文的要求。

| 编号 | 文献 | 用于论文位置 |
| --- | --- | --- |
| [1] Tewari et al., **State of the Art on Neural Rendering**, Computer Graphics Forum / arXiv:2004.03805, 2020. https://arxiv.org/abs/2004.03805 | 摘要、引言、相关技术现状。作为神经渲染定义和整体发展脉络的综述依据。 |
| [2] Xie et al., **Neural Fields in Visual Computing and Beyond**, Computer Graphics Forum / arXiv:2111.11426, 2021. https://arxiv.org/abs/2111.11426 | 相关技术现状。用于解释 neural field / implicit neural representation 的统一表述。 |
| [3] Mildenhall et al., **NeRF: Representing Scenes as Neural Radiance Fields for View Synthesis**, ECCV / arXiv:2003.08934, 2020. https://arxiv.org/abs/2003.08934 | 引言、方法设计。作为神经辐射场与体渲染主线的基础文献。 |
| [4] Tancik et al., **Fourier Features Let Networks Learn High Frequency Functions in Low Dimensional Domains**, NeurIPS / arXiv:2006.10739, 2020. https://arxiv.org/abs/2006.10739 | 相关技术现状。用于说明位置编码和高频细节学习。 |
| [5] Sitzmann et al., **Scene Representation Networks**, NeurIPS / arXiv:1906.01618, 2019. https://arxiv.org/abs/1906.01618 | 相关技术现状。用于说明 NeRF 之前的连续神经场场景表示。 |
| [6] Park et al., **DeepSDF: Learning Continuous Signed Distance Functions for Shape Representation**, CVPR / arXiv:1901.05103, 2019. https://arxiv.org/abs/1901.05103 | 相关技术现状、结果讨论。用于说明 SDF 与显式表面控制问题。 |
| [7] Barron et al., **Mip-NeRF: A Multiscale Representation for Anti-Aliasing Neural Radiance Fields**, ICCV / arXiv:2103.13415, 2021. https://arxiv.org/abs/2103.13415 | 相关技术现状。用于说明反走样与多尺度采样。 |
| [8] Barron et al., **Mip-NeRF 360: Unbounded Anti-Aliased Neural Radiance Fields**, CVPR / arXiv:2111.12077, 2022. https://arxiv.org/abs/2111.12077 | 实验设计、结果讨论。用于真实无界场景与外推难点。 |
| [9] Müller et al., **Instant Neural Graphics Primitives with a Multiresolution Hash Encoding**, SIGGRAPH / arXiv:2201.05989, 2022. https://arxiv.org/abs/2201.05989 | 方法设计、实验对比。作为高效 NeRF 类方法代表。 |
| [10] Yu et al., **PlenOctrees for Real-time Rendering of Neural Radiance Fields**, ICCV / arXiv:2103.14024, 2021. https://arxiv.org/abs/2103.14024 | 相关技术现状。用于说明将 NeRF 烘焙到显式结构以实现实时渲染。 |
| [11] Hedman et al., **Baking Neural Radiance Fields for Real-Time View Synthesis**, ICCV / arXiv:2103.14645, 2021. https://arxiv.org/abs/2103.14645 | 相关技术现状。用于讨论 SNeRG 和实时渲染。 |
| [12] Yu et al., **Plenoxels: Radiance Fields without Neural Networks**, CVPR / arXiv:2112.05131, 2022. https://arxiv.org/abs/2112.05131 | 方法设计、结果讨论。用于说明可微体渲染和优化表示不一定依赖深 MLP。 |
| [13] Chen et al., **TensoRF: Tensorial Radiance Fields**, ECCV / arXiv:2203.09517, 2022. https://arxiv.org/abs/2203.09517 | 相关技术现状。用于说明低秩张量分解带来的速度和存储优势。 |
| [14] Kerbl et al., **3D Gaussian Splatting for Real-Time Radiance Field Rendering**, ACM TOG / arXiv:2308.04079, 2023. https://arxiv.org/abs/2308.04079 | 方法设计、实验对比、结果讨论。作为高效神经渲染主实验对象。 |
| [15] Wang et al., **NeuS: Learning Neural Implicit Surfaces by Volume Rendering for Multi-view Reconstruction**, NeurIPS / arXiv:2106.10689, 2021. https://arxiv.org/abs/2106.10689 | 相关技术现状、局限讨论。用于说明从体渲染转向高质量表面重建。 |
| [16] Yariv et al., **Volume Rendering of Neural Implicit Surfaces**, NeurIPS / arXiv:2106.12052, 2021. https://arxiv.org/abs/2106.12052 | 相关技术现状。用于说明 SDF 与体密度耦合的 VolSDF 思路。 |
| [17] Lin et al., **BARF: Bundle-Adjusting Neural Radiance Fields**, ICCV / arXiv:2104.06405, 2021. https://arxiv.org/abs/2104.06405 | 实验设计、局限讨论。用于相机位姿误差和联合优化问题。 |
| [18] Martin-Brualla et al., **NeRF in the Wild**, CVPR / arXiv:2008.02268, 2021. https://arxiv.org/abs/2008.02268 | 相关技术现状、结果讨论。用于非受控照片、光照变化和临时遮挡。 |
| [19] Niemeyer et al., **RegNeRF: Regularizing Neural Radiance Fields for View Synthesis from Sparse Inputs**, CVPR / arXiv:2112.00724, 2022. https://arxiv.org/abs/2112.00724 | 实验设计。用于稀疏输入和正则化变量讨论。 |
| [20] Barron et al., **Zip-NeRF: Anti-Aliased Grid-Based Neural Radiance Fields**, ICCV / arXiv:2304.06706, 2023. https://arxiv.org/abs/2304.06706 | 相关技术现状、结果讨论。用于连接抗锯齿与网格加速方法。 |

## 9. 写作边界

论文应避免把神经渲染写成“AI 画图”。神经渲染的关键不是从文本直接输出二维图像，而是从多视角图像、相机位姿和可微渲染损失中学习一个三维场景表示。它能够生成新的视角，但这种生成受相机、射线、空间坐标、密度、辐射度和可见性约束，因此与普通图像生成模型不同。

论文也不应把 3D Gaussian Splatting 简单写成“不是神经网络所以不是神经渲染”。它继承了辐射场和可微图像重建的目标，只是把 MLP 查询替换为显式三维高斯参数和快速 splatting 渲染。将它放入神经渲染的高效分支中是合理的。

最终结论应保持平衡：神经渲染明显改变了三维内容获取和新视角合成流程，在视觉质量和自动化程度上具有优势；但传统显式图形管线在可编辑性、物理可解释性、引擎兼容性和精确几何控制上仍有不可替代的价值。
