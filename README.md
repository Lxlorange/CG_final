# 计算机图形学结课论文

本仓库是课程论文“基于神经渲染的三维场景重建与自然语言相机控制研究”的代码、实验产物和论文源码。实验围绕 NeRF Synthetic `lego` 场景展开，包含两条主线：

1. 比较 Visual Hull、Nerfacto 和 Splatfacto 在新视角合成任务中的表现。
2. 比较规则模板与 LLM 将中文镜头描述转换为 Nerfstudio camera path 的能力，并用已训练的 Splatfacto 模型渲染视频。

论文源码为 `CGpaper.tex`，当前 PDF 可由 XeLaTeX 编译生成。

## 当前结论

### 新视角合成

正式统计位于 `experiment/outputs/formal/lego/summary/summary.json`，论文使用 20 个测试视角：

| 方法 | PSNR | SSIM | 说明 |
| --- | ---: | ---: | --- |
| Visual Hull | 15.62 | 0.701 | 传统显式几何基线，主要失败于外壳缺失和细节破碎 |
| Nerfacto | 21.13 | 0.873 | 连续神经辐射场，边缘和高频结构存在软化 |
| Splatfacto | 28.28 | 0.955 | 本实验中图像质量最高，但局部仍可能出现浮点或颜色偏移 |

论文图片已整理到：

- `images/experiments/lego_comparison.png`
- `images/experiments/lego_failure_cases.png`

### LLM 相机控制

相机控制实验使用 8 条中文镜头任务。规则模板和 LLM 均生成了合法 JSON 与 Nerfstudio camera path，并各自渲染出 8 个视频。

客观统计位于 `experiment/outputs/llm_camera/summary.json`：

| 方法 | 任务数 | JSON 解析率 | 参数合法率 | Camera path 生成率 | 平均连续性 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 规则模板 | 8 | 1.00 | 1.00 | 1.00 | 0.882 |
| LLM | 8 | 1.00 | 1.00 | 1.00 | 0.897 |

视频输出位于：

- `experiment/outputs/llm_camera/renders/rule/*.mp4`
- `experiment/outputs/llm_camera/renders/llm/*.mp4`

论文中的主观评分由作者单人完成，用于比较自然语言意图符合度。LLM 平均分为 3.75，规则模板平均分为 2.88；优势主要来自复合镜头任务。

## 目录结构

```text
.
├── CGpaper.tex                         # 论文 LaTeX 源码
├── config.tex                          # 论文格式与宏包配置
├── images/                             # 论文实际引用图片
├── experiment/
│   ├── README.md                       # 实验复现细节
│   ├── llm_camera/                     # 相机任务与 prompt 模板
│   ├── scripts/                        # Windows/Python 后处理与评估脚本
│   ├── wsl/                            # WSL/Nerfstudio 渲染脚本
│   └── outputs/                        # 实验产物
└── README.md
```

## 论文编译

在 Windows PowerShell 中运行：

```powershell
xelatex -interaction=nonstopmode CGpaper.tex
xelatex -interaction=nonstopmode CGpaper.tex
```

当前编译会生成 `CGpaper.pdf`。已知警告主要来自中文字体形状替换和一个很轻微的 overfull hbox，不影响 PDF 输出。

## 复现实验

详细步骤见 `experiment/README.md`。常用命令如下。

重新生成论文使用的 Lego 汇总图：

```powershell
python experiment\scripts\make_formal_summary.py --scene lego --max-views 8
```

重新生成规则轨迹、LLM 轨迹、Nerfstudio camera path 与客观指标：

```powershell
python experiment\scripts\generate_rule_camera_paths.py
python experiment\scripts\generate_llm_camera_paths.py
python experiment\scripts\make_camera_path_from_json.py --matrix-format flat
python experiment\scripts\evaluate_camera_paths.py
```

LLM 默认使用 OpenAI-compatible API，当前实验记录的模型为 `deepseek-chat`。运行前需要设置：

```powershell
$env:OPENAI_API_KEY="你的 API key"
$env:OPENAI_BASE_URL="https://api.deepseek.com"
$env:OPENAI_MODEL="deepseek-chat"
```

在 WSL/Nerfstudio 环境中渲染相机轨迹：

```bash
bash experiment/wsl/render_llm_camera_paths.sh \
  --config /home/orangelxl/CG/nerfstudio/outputs/lego_splatfacto/splatfacto/2026-06-13_124906/config.yml \
  --render-cwd /home/orangelxl/CG/nerfstudio \
  --source rule

bash experiment/wsl/render_llm_camera_paths.sh \
  --config /home/orangelxl/CG/nerfstudio/outputs/lego_splatfacto/splatfacto/2026-06-13_124906/config.yml \
  --render-cwd /home/orangelxl/CG/nerfstudio \
  --source llm
```

如果 `config.yml` 中的数据集或 checkpoint 是相对路径，`--render-cwd` 必须指向对应的 Nerfstudio 工作目录，否则可能出现找不到 `datasets/nerf_synthetic/lego/transforms_train.json` 或 checkpoint 的错误。

## 未纳入正式结论的内容

以下内容没有作为本文正式定量结论：

- LPIPS 感知指标。
- Nerfacto 与 Splatfacto 的统一单帧渲染时间。
- 多场景或真实采集场景实验。
- 多评价者主观评分一致性检验。

这些内容已在论文局限性中说明。
