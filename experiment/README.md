# 实验流程说明

本目录只保留论文实验所需的代码、配置和产物说明。论文正文引用的图片统一放在 `images/` 下，目前实际被 `CGpaper.tex` 使用的图片为：

- `images/BJTU_emblem.png`
- `images/experiments/lego_comparison.png`
- `images/experiments/lego_failure_cases.png`

## 实验主线

论文实验由两部分组成：

1. 场景表示对比：在 NeRF Synthetic `lego` 场景上比较 Visual Hull、Nerfacto、Splatfacto 的新视角合成质量。
2. LLM 相机控制：比较规则模板与 LLM 将自然语言镜头描述转换为相机轨迹的能力，再用已训练好的 Splatfacto 模型渲染少量短轨迹。

后续不再训练新场景。算力优先用于复用已有权重、生成 LLM 轨迹和少量 Splatfacto 推理。

## 当前目录结构

```text
experiment/
  README.md                         # 本文件，唯一需要阅读的实验说明
  llm_camera/                       # LLM 相机控制实验的输入任务与 prompt
    prompts/qwen_camera_prompt.md
    tasks/camera_tasks.json
  scripts/                          # Windows/本地 Python 后处理脚本
  wsl/                              # WSL/Nerfstudio 运行脚本
  outputs/                          # 实验产物
```

## outputs 结构说明

```text
experiment/outputs/formal/lego/
  gt/                               # 20 个测试视角真值图
  traditional_visual_hull/           # 传统 Visual Hull 预测图与指标
  nerfacto/                          # Nerfacto 归一化预测图与指标
  splatfacto/                        # Splatfacto 归一化预测图与指标
  summary/                           # 论文实验一的汇总数据和原始对比图
  raw_renders/                       # Nerfstudio 原始渲染输出，可删除后由 config 复现
  nerfstudio_runs/                   # Windows 侧保存的 Nerfacto config/checkpoint 信息
  render_timing/                     # 旧的 Nerfacto 计时尝试，不作为论文正式数据
  eval_manifest.json                 # 测试视角对应关系

experiment/outputs/llm_camera/
  paths/rule/                        # 规则模板生成的结构化相机参数 JSON
  paths/llm/                         # LLM 生成的相机参数 JSON；dry-run 时只包含 prompt/raw 目录
  camera_paths/rule/                 # 转换后的 Nerfstudio camera-path JSON
  camera_paths/llm/                  # LLM 轨迹转换后的 camera-path JSON
  renders/                           # 后续 WSL 渲染输出视频或关键帧
  summary.json                       # 解析成功率、参数合法率、轨迹连续性等统计
```

## 待手动清理的数据

以下内容不作为最终论文证据使用，可以删除以节省空间。若当前环境阻止自动删除，可在 PowerShell 中手动执行：

```powershell
Remove-Item -Recurse -Force experiment\outputs\dataset
Remove-Item -Recurse -Force experiment\outputs\neural_ray_field
Remove-Item -Recurse -Force experiment\outputs\summary
Remove-Item -Recurse -Force experiment\outputs\traditional_point_splat
Remove-Item -Recurse -Force experiment\scripts\__pycache__
Remove-Item -Force experiment\FORMAL_EXPERIMENT.md
Remove-Item -Force experiment\LLM_CAMERA_EXPERIMENT.md
Remove-Item -Force experiment\RESULTS.md
Remove-Item -Force experiment\run_experiment.py
```

`formal/lego/raw_renders/` 和 `formal/lego/nerfstudio_runs/` 体积可能较大，但保留它们便于追溯 Nerfstudio 原始输出与 config。若磁盘紧张，论文正文只依赖 `formal/lego/{gt,traditional_visual_hull,nerfacto,splatfacto,summary}` 和 `images/experiments/`。

## 已完成内容

已经完成：

```powershell
python experiment\scripts\generate_rule_camera_paths.py
python experiment\scripts\generate_llm_camera_paths.py --dry-run
python experiment\scripts\make_camera_path_from_json.py --matrix-format flat
python experiment\scripts\evaluate_camera_paths.py
```

预期结果：

- `experiment/outputs/llm_camera/paths/rule/*.json`
- `experiment/outputs/llm_camera/camera_paths/rule/*.json`
- `experiment/outputs/llm_camera/summary.json`

## 你接下来需要执行

### 1. 重新评估已有规则轨迹

先在当前目录运行一次，确认 `summary.json` 是最新格式：

```powershell
python experiment\scripts\evaluate_camera_paths.py
```

预期结果：更新 `experiment/outputs/llm_camera/summary.json`，其中 `rule` 的解析率、合法率和 camera path 生成率应为 1.0。

### 2. 配置 ds/qwen API

PowerShell 中设置 OpenAI-compatible 环境变量：

```powershell
$env:OPENAI_API_KEY="你的 API key"
$env:OPENAI_BASE_URL="你的 OpenAI-compatible base url"
$env:OPENAI_MODEL="你的模型名"
```

DeepSeek 示例：

```powershell
$env:OPENAI_BASE_URL="https://api.deepseek.com"
$env:OPENAI_MODEL="deepseek-chat"
```

Qwen/DashScope 如果使用 OpenAI-compatible endpoint，也按同样方式设置。

### 3. 生成 LLM 相机参数

```powershell
python experiment\scripts\generate_llm_camera_paths.py
```

预期结果：

```text
experiment/outputs/llm_camera/paths/llm/*.json
experiment/outputs/llm_camera/paths/llm/raw/*.txt
```

如果报 JSON 解析错误，先打开 `raw/*.txt` 看模型是否输出了 Markdown 或解释文字；必要时把 prompt 再收紧。

### 4. 转换为 Nerfstudio camera path 并评估

```powershell
python experiment\scripts\make_camera_path_from_json.py --matrix-format flat
python experiment\scripts\evaluate_camera_paths.py
```

预期结果：

```text
experiment/outputs/llm_camera/camera_paths/llm/*.json
experiment/outputs/llm_camera/summary.json
```

论文中可报告：

- JSON 解析成功率
- 参数合法率
- camera path 生成成功率
- 轨迹连续性
- 目标保持率

### 5. 找到 Splatfacto config

在 WSL 中找：

```bash
find /home/orangelxl/CG -path '*splatfacto*config.yml'
```

你需要的是类似：

```text
/home/orangelxl/CG/outputs/lego_splatfacto/splatfacto/2026-xx-xx_xxxxxx/config.yml
```

### 6. 只渲染少量轨迹

建议先只渲染 2 条规则轨迹和 2 条 LLM 轨迹：

```bash
cd /mnt/d/2026_spring/Graphics/final

bash experiment/wsl/render_llm_camera_paths.sh \
  --config /home/orangelxl/CG/outputs/lego_splatfacto/splatfacto/2026-xx-xx_xxxxxx/config.yml \
  --source rule \
  --limit 2

bash experiment/wsl/render_llm_camera_paths.sh \
  --config /home/orangelxl/CG/outputs/lego_splatfacto/splatfacto/2026-xx-xx_xxxxxx/config.yml \
  --source llm \
  --limit 2
```

预期结果：

```text
experiment/outputs/llm_camera/renders/rule/*.mp4
experiment/outputs/llm_camera/renders/llm/*.mp4
```

如果渲染脚本提示 camera path 格式不兼容，则重新生成 nested 格式：

```powershell
python experiment\scripts\make_camera_path_from_json.py --matrix-format nested
```

然后再运行 WSL 渲染命令。

### 7. 人工评分

看每个视频，手工给 1-5 分：

- 5：完全符合文本意图，运动平滑，目标始终在画面中。
- 4：基本符合，有轻微构图或速度问题。
- 3：大体方向正确，但镜头控制一般。
- 2：只有部分意图被执行。
- 1：明显失败或无法渲染。

评分后把结果补入论文实验二表格。

## 最终论文需要补的内容

1. 摘要和引言：把题目从纯神经渲染对比调整为“神经渲染 + LLM 相机控制”。
2. 相关工作：补 ChatCam/CineGPT。
3. 方法设计：增加“自然语言 -> JSON 相机参数 -> camera path -> NeRF/3DGS 渲染”模块。
4. 实验与对比：新增实验二，报告规则模板与 LLM 的对比。
5. 结果讨论：说明 LLM 改善输入理解和相机控制效率，但引入 JSON 不合法、参数越界、路径不可控等新问题。

## 可选长时间实验

如果最后仍有时间和算力，再考虑运行多场景 Nerfstudio 脚本。该脚本会写入 `experiment/wsl/run_multiscene_nerfstudio.sh`，不再写入 `outputs/`：

```powershell
python experiment\scripts\write_multiscene_commands.py --scenes lego materials drums --methods nerfacto splatfacto --max-num-iterations 30000 --test-limit 20
```

WSL 中运行：

```bash
bash /mnt/d/2026_spring/Graphics/final/experiment/wsl/run_multiscene_nerfstudio.sh
```

此步骤不是当前最短完成路径。
