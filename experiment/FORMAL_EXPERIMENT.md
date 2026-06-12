# 正式实验执行方案

当前 `run_experiment.py` 已经完成了合成数据、传统点云 baseline 和一个轻量坐标场 baseline。论文正式实验建议在此基础上加入真正的 NeRF 或 3D Gaussian Splatting 结果。

## 1. 当前已完成的预实验

已完成内容：

- 合成静态三维场景：球体、立方体、棋盘地面、固定光照、环绕相机。
- 训练视角：12 个。
- 测试视角：4 个，位于训练视角之间。
- 传统 baseline：RGB-D 反投影成彩色点云，再投影到测试视角。
- 轻量学习 baseline：相机射线/像素/角度坐标到 RGB 的随机傅里叶特征回归。

当前结果见：

- `outputs/summary/metrics.csv`
- `outputs/summary/comparison.png`
- `outputs/summary/summary.json`

这组结果适合作为“预实验”或“消融实验”：它说明简单坐标回归虽然属于学习式图像合成，但缺少 NeRF 的三维密度、可见性和体渲染约束，因此无法稳定完成新视角合成。正式论文中不应把它称为 NeRF。

## 2. 正式 NeRF/3DGS 实验应如何接入

正式方法只需要输出与测试视角一一对应的 RGB 图像：

```text
experiment/outputs/nerf/pred_000.png
experiment/outputs/nerf/pred_001.png
experiment/outputs/nerf/pred_002.png
experiment/outputs/nerf/pred_003.png

experiment/outputs/3dgs/pred_000.png
experiment/outputs/3dgs/pred_001.png
experiment/outputs/3dgs/pred_002.png
experiment/outputs/3dgs/pred_003.png
```

然后运行：

```powershell
python experiment\scripts\evaluate_folder.py --pred-dir experiment\outputs\nerf --method nerf
python experiment\scripts\evaluate_folder.py --pred-dir experiment\outputs\3dgs --method 3dgs
python experiment\scripts\make_summary.py
```

如果外部工具输出文件名不同，先重命名为 `pred_000.png` 到 `pred_003.png` 即可。

## 3. 推荐正式实验路线

优先级从高到低：

1. 使用 Nerfstudio 跑 `nerfacto` 或 `instant-ngp` 类方法。
2. 使用 GraphDECO 官方 3D Gaussian Splatting 实现跑同一数据。
3. 如果安装受阻，使用公开论文或官方 demo 的结果作为方法讨论，当前本地实验只保留传统 baseline 与失败消融。

对于课程论文，最小可接受组合是：

- 一组自己生成或自采的多视角数据。
- 一个传统显式 baseline。
- 一个真正神经渲染方法，最好是 NeRF 或 3DGS。
- 同一测试视角下的图像对比和指标表。

## 4. 论文中可直接讨论的观察

从当前预实验已经可以支持以下观点：

- 传统点云 splatting 能利用显式几何关系，因此轮廓、遮挡和地面纹理相对稳定。
- 传统点云方法的弱点是可见面不完整，测试视角会出现空洞、点状噪声和边缘破碎。
- 简单坐标回归没有显式三维密度与可见性建模，会退化为模糊的颜色插值，不能可靠表示遮挡关系。
- 这说明 NeRF 的核心不是“用了神经网络”，而是把神经场与相机射线采样、体密度、透射率和体渲染积分结合起来。
- 3DGS 的优势也不只是“快”，而是使用可优化的三维高斯集合保留了空间结构，同时通过 splatting 实现高效渲染。
