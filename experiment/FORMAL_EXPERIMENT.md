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

## 2. 使用 NeRF Synthetic 的正式实验接入

你已经下载了 NeRF Synthetic 数据集，目录为：

```text
experiment/outputs/dataset/nerf_synthetic
```

建议先选一个场景，例如 `lego` 或 `chair`。`lego` 是 NeRF 论文中最常用的展示场景之一，适合论文图；`chair` 结构清晰，适合观察几何轮廓。

注意：使用 Nerfstudio 的 `blender-data` dataparser 时，NeRF Synthetic 的 `transforms_train.json` 中 `file_path` 应保持 `./train/r_0` 这种不带扩展名的形式，因为 dataparser 会自动补 `.png`。如果之前把路径改成了 `./train/r_0.png`，并报 `.../train/r_0.png.png`，在 WSL 中运行：

```bash
python /mnt/d/2026_spring/Graphics/final/experiment/scripts/fix_nerf_synthetic_paths.py ~/CG/datasets/nerf_synthetic/lego --mode strip-png --cleanup-aliases
```

脚本会备份原始 `transforms_*.json` 为 `.bak`，并把 `./train/r_0.png` 或 `./train/r_0.png.png` 还原成 `./train/r_0`；如果你之前创建了 `train/r_0` 这种 extensionless 软链接或拷贝，也会一并清理。

运行后可以检查：

```bash
grep -m 3 file_path ~/CG/datasets/nerf_synthetic/lego/transforms_train.json
```

应看到 `./train/r_0` 这类不带后缀的路径。不要再创建无后缀软链接；使用 `blender-data` 时由 Nerfstudio 自动补 `.png`。

## 2.1 过夜训练脚本

如果要先做超小验证，运行：

```bash
bash /mnt/d/2026_spring/Graphics/final/experiment/wsl/validate_nerfstudio_lego.sh
```

该脚本默认对 `nerfacto` 和 `splatfacto` 各训练 20 iterations，并确认 checkpoint/config 能生成。默认不渲染 test split，因为 `ns-render dataset` 会渲染整个 test 集，NeRF Synthetic 通常有 200 张图，验证阶段会很慢。

如果确实要验证渲染命令，可运行：

```bash
RUN_RENDER=1 bash /mnt/d/2026_spring/Graphics/final/experiment/wsl/validate_nerfstudio_lego.sh
```

验证通过后，建议在 `tmux` 中运行完整脚本：

```bash
tmux new -s nerf
bash /mnt/d/2026_spring/Graphics/final/experiment/wsl/run_nerfstudio_lego_full.sh
```

完整脚本默认训练：

- `nerfacto`: 30000 iterations
- `splatfacto`: 30000 iterations

如需降低时间或显存压力，可覆盖环境变量：

```bash
MAX_ITERS_NERFACTO=10000 MAX_ITERS_SPLATFACTO=10000 \
bash /mnt/d/2026_spring/Graphics/final/experiment/wsl/run_nerfstudio_lego_full.sh
```

脚本会尝试启动 Windows 侧的 `keep_awake.ps1` 阻止系统睡眠。注意，电脑真正进入睡眠后 GPU 不会继续训练；防休眠脚本的作用是避免系统自动睡眠。

如果 `splatfacto` 首次运行时报 `Error building extension 'gsplat_cuda'`，并且日志中出现 `unsupported GNU version! gcc versions later than 11 are not supported!`，说明 CUDA 11.8 正在调用过新的 GCC。安装 GCC/G++ 11 并设置编译器：

```bash
sudo apt-get update
sudo apt-get install -y gcc-11 g++-11

export CC=/usr/bin/gcc-11
export CXX=/usr/bin/g++-11
export CUDAHOSTCXX=/usr/bin/g++-11
export MAX_JOBS=2
rm -rf ~/.cache/torch_extensions
```

之后重新运行 `splatfacto`。本目录的 WSL 脚本会在检测到 `/usr/bin/gcc-11` 和 `/usr/bin/g++-11` 时自动设置这些变量。

如果编译阶段显示 `gsplat: Setting up CUDA with MAX_JOBS=10` 后进程被 `terminated`，通常是 WSL 内存不足导致编译进程被杀。将 `MAX_JOBS` 降为 1 或 2 后重试：

```bash
export MAX_JOBS=1
rm -rf ~/.cache/torch_extensions
```

如果只需要渲染论文中足够使用的前 20 张测试图，而不是完整 test split，可先临时裁剪 `transforms_test.json`：

```bash
python /mnt/d/2026_spring/Graphics/final/experiment/scripts/limit_nerf_synthetic_split.py ~/CG/datasets/nerf_synthetic/lego --split test --limit 20
```

渲染完成后如需恢复完整 test split：

```bash
python /mnt/d/2026_spring/Graphics/final/experiment/scripts/limit_nerf_synthetic_split.py ~/CG/datasets/nerf_synthetic/lego --split test --restore
```

如果 `splatfacto` 或 `gsplat` 编译时报 `unsupported GNU version! gcc versions later than 11 are not supported`，说明 CUDA 11.8 正在调用过新的系统 GCC。安装 GCC 11 并指定 host compiler：

```bash
sudo apt-get update
sudo apt-get install -y gcc-11 g++-11

export CC=/usr/bin/gcc-11
export CXX=/usr/bin/g++-11
export CUDAHOSTCXX=/usr/bin/g++-11
rm -rf ~/.cache/torch_extensions
```

之后重新运行验证或完整脚本。脚本会在检测到 `/usr/bin/gcc-11` 和 `/usr/bin/g++-11` 时自动设置这些环境变量。

先准备测试视角 ground truth：

```powershell
python experiment\scripts\prepare_nerf_synthetic_eval.py --scene lego --max-views 20 --copy-mode composite
```

这会生成：

```text
experiment/outputs/formal/lego/gt/gt_000.png
experiment/outputs/formal/lego/gt/gt_001.png
...
experiment/outputs/formal/lego/eval_manifest.json
```

然后生成 WSL 中可运行的 Nerfstudio 命令模板：

```powershell
python experiment\scripts\write_nerfstudio_commands.py --scene lego --methods nerfacto splatfacto --max-num-iterations 30000
```

脚本会写出：

```text
experiment/outputs/formal/lego/run_nerfstudio.sh
```

切到 WSL 后，在 Nerfstudio 环境中运行这个 `.sh` 文件即可。它会训练：

- `nerfacto`：作为 NeRF 类神经辐射场方法。
- `splatfacto`：作为 3D Gaussian Splatting 类方法。

如果手动运行命令，NeRF Synthetic 必须显式指定 `blender-data` dataparser，例如：

```bash
ns-train nerfacto \
  --output-dir outputs \
  --experiment-name lego_nerfacto \
  --max-num-iterations 30000 \
  --viewer.quit-on-train-completion True \
  blender-data \
  --data datasets/nerf_synthetic/lego
```

如果省略 `blender-data`，Nerfstudio 会默认使用 `nerfstudio-data` 解析器，并报类似 `AssertionError: fx not specified in frame` 的错误。这是因为 NeRF Synthetic 的相机内参通常写在全局 `camera_angle_x` 中，而不是每个 frame 的 `fl_x` 字段中。

Nerfstudio 输出的渲染图通常需要整理成统一命名。回到当前项目后运行：

```powershell
python experiment\scripts\normalize_nerfstudio_renders.py --src-dir experiment\outputs\formal\lego\raw_renders\nerfacto --dst-dir experiment\outputs\formal\lego\nerfacto --limit 20
python experiment\scripts\normalize_nerfstudio_renders.py --src-dir experiment\outputs\formal\lego\raw_renders\splatfacto --dst-dir experiment\outputs\formal\lego\splatfacto --limit 20
```

再计算指标：

```powershell
python experiment\scripts\evaluate_folder.py --pred-dir experiment\outputs\formal\lego\nerfacto --method nerfacto --gt-dir experiment\outputs\formal\lego\gt --limit 20
python experiment\scripts\evaluate_folder.py --pred-dir experiment\outputs\formal\lego\splatfacto --method splatfacto --gt-dir experiment\outputs\formal\lego\gt --limit 20
```

最后生成正式实验的指标表与对比图：

```powershell
python experiment\scripts\make_formal_summary.py --scene lego --max-views 8
```

输出位置：

```text
experiment/outputs/formal/lego/summary/metrics.csv
experiment/outputs/formal/lego/summary/summary.json
experiment/outputs/formal/lego/summary/comparison.png
```

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

如果你不用 Nerfstudio，而是用其他 NeRF/3DGS 仓库，也只需要把输出图像整理成上面的命名，然后运行：

```powershell
python experiment\scripts\evaluate_folder.py --pred-dir experiment\outputs\formal\lego\nerf --method nerf --gt-dir experiment\outputs\formal\lego\gt --limit 20
python experiment\scripts\evaluate_folder.py --pred-dir experiment\outputs\formal\lego\3dgs --method 3dgs --gt-dir experiment\outputs\formal\lego\gt --limit 20
python experiment\scripts\make_formal_summary.py --scene lego --max-views 8
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
