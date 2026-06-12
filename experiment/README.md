# 神经渲染对比实验

本目录用于论文的实验部分。当前版本先完成一个轻量、可复现的课程级实验：

1. 生成一个合成三维静态场景，并输出多视角 RGB 图、深度图和相机参数。
2. 用传统显式流程做 baseline：训练视角 RGB-D 反投影为彩色点云，再投影到测试视角。
3. 用轻量学习式坐标场做 baseline：以相机射线坐标为输入，用随机傅里叶特征 + Ridge 回归预测 RGB。
4. 计算 PSNR、SSIM、耗时，并生成对比图。

这里的轻量坐标场不是完整 NeRF。它的作用是先把“传统显式表示 vs 学习式连续表示”的实验链路跑通，避免一开始被 COLMAP、Nerfstudio、3D Gaussian Splatting 的环境安装阻塞。后续可以把 `scripts/neural_ray_field.py` 替换为正式 NeRF/3DGS 输出，只要保持 `outputs/*/metrics.json` 和对比图格式一致即可。

正式 NeRF/3DGS 接入方式见 `FORMAL_EXPERIMENT.md`，当前预实验结果解释见 `RESULTS.md`。

## 运行方式

在项目根目录运行：

```powershell
python experiment\run_experiment.py
```

输出位置：

- `experiment/outputs/dataset/`：合成训练/测试图像、深度和相机参数。
- `experiment/outputs/traditional_point_splat/`：传统点云 splatting 结果。
- `experiment/outputs/neural_ray_field/`：轻量坐标场结果。
- `experiment/outputs/summary/metrics.csv`：指标表。
- `experiment/outputs/summary/comparison.png`：论文可用的结果对比图。

## 后续替换为正式 NeRF/3DGS

正式实验建议保留同一套数据与测试视角，然后加入：

- NeRF/Instant-NGP：输出测试视角 RGB 图，记录训练时间、渲染时间和模型大小。
- 3D Gaussian Splatting：输出测试视角 RGB 图，记录优化时间、FPS、显存和模型大小。

只要最终能与 `dataset/test/rgb_*.png` 对齐，就可以复用 `scripts/metrics.py` 计算指标。
