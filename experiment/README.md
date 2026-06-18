# 实验流程说明

本目录保存论文实验所需的输入、脚本和产物。论文正文实际引用的图片统一放在仓库根目录 `images/` 下：

- `images/BJTU_emblem.png`
- `images/experiments/lego_comparison.png`
- `images/experiments/lego_failure_cases.png`

## 实验组成

论文实验分为两部分。

第一部分是新视角合成质量对比：在 NeRF Synthetic `lego` 场景上比较 Visual Hull、Nerfacto 和 Splatfacto。正式结果位于 `experiment/outputs/formal/lego/summary/summary.json`。

第二部分是自然语言相机控制：给定 8 条中文镜头任务，分别由规则模板和 LLM 生成结构化相机参数，再转换为 Nerfstudio camera path，并用已训练好的 Splatfacto 模型渲染视频。正式结果位于 `experiment/outputs/llm_camera/summary.json` 和 `experiment/outputs/llm_camera/renders/`。

## 目录结构

```text
experiment/
  README.md
  llm_camera/
    prompts/qwen_camera_prompt.md       # JSON 约束 prompt 模板
    tasks/camera_tasks.json             # 8 条中文镜头任务
  scripts/
    make_formal_summary.py              # 汇总 Lego 新视角合成结果并生成论文图
    generate_rule_camera_paths.py       # 规则模板轨迹生成
    generate_llm_camera_paths.py        # LLM 轨迹生成，默认 deepseek-chat
    make_camera_path_from_json.py       # 参数 JSON -> Nerfstudio camera path
    evaluate_camera_paths.py            # JSON、参数、轨迹连续性等统计
    evaluate_folder.py                  # 图像 PSNR/SSIM 评估
    normalize_nerfstudio_renders.py     # Nerfstudio 渲染输出归一化
    traditional_visual_hull.py          # Visual Hull 基线
  wsl/
    render_llm_camera_paths.sh          # WSL 中调用 ns-render 渲染轨迹视频
    measure_nerfstudio_render_time.sh   # 可选计时脚本，未纳入正式结论
  outputs/
    formal/lego/                        # 新视角合成实验产物
    llm_camera/                         # 相机控制实验产物
```

## 新视角合成产物

```text
experiment/outputs/formal/lego/
  gt/                                   # 20 个测试视角真值图
  traditional_visual_hull/              # Visual Hull 预测图与指标
  nerfacto/                             # Nerfacto 预测图与指标
  splatfacto/                           # Splatfacto 预测图与指标
  summary/
    summary.json                        # 论文表 1 数据
    metrics.csv                         # 每视角指标
    comparison.png                      # 原始对比图
    failure_cases.png                   # 原始失败案例图
  raw_renders/                          # Nerfstudio 原始渲染输出
  nerfstudio_runs/                      # Windows 侧保存的 config/checkpoint 信息
  eval_manifest.json                    # 测试视角对应关系
```

重新生成论文使用的汇总图：

```powershell
python experiment\scripts\make_formal_summary.py --scene lego --max-views 8
```

生成后检查：

```text
images/experiments/lego_comparison.png
images/experiments/lego_failure_cases.png
experiment/outputs/formal/lego/summary/summary.json
```

## LLM 相机控制产物

```text
experiment/outputs/llm_camera/
  paths/rule/                            # 规则模板生成的相机参数 JSON
  paths/llm/                             # LLM 生成的相机参数 JSON、prompt 和 raw 输出
  camera_paths/rule/                     # 规则轨迹对应的 Nerfstudio camera path
  camera_paths/llm/                      # LLM 轨迹对应的 Nerfstudio camera path
  renders/rule/                          # 规则轨迹视频，共 8 个 mp4
  renders/llm/                           # LLM 轨迹视频，共 8 个 mp4
  summary.json                           # 表 2 的客观统计
```

当前 8 个任务为：

- `orbit_full`
- `dolly_in`
- `pan_left_to_right`
- `descend_to_eye_level`
- `orbit_pull_back`
- `high_reveal_orbit`
- `closeup_pullback_orbit`
- `diagonal_sweep_reveal`

## 重新生成相机轨迹

### 1. 配置 LLM API

`generate_llm_camera_paths.py` 使用 OpenAI-compatible API。当前论文实验使用：

- 模型：`deepseek-chat`
- temperature：`0.2`
- timeout：`60 s`

PowerShell 示例：

```powershell
$env:OPENAI_API_KEY="你的 API key"
$env:OPENAI_BASE_URL="https://api.deepseek.com"
$env:OPENAI_MODEL="deepseek-chat"
```

### 2. 生成规则轨迹和 LLM 轨迹

```powershell
python experiment\scripts\generate_rule_camera_paths.py
python experiment\scripts\generate_llm_camera_paths.py
```

如果只想检查 prompt，不调用 API：

```powershell
python experiment\scripts\generate_llm_camera_paths.py --dry-run
```

### 3. 转换为 Nerfstudio camera path

```powershell
python experiment\scripts\make_camera_path_from_json.py --matrix-format flat
```

如遇到 Nerfstudio 版本要求 nested matrix，可改用：

```powershell
python experiment\scripts\make_camera_path_from_json.py --matrix-format nested
```

### 4. 评估轨迹

```powershell
python experiment\scripts\evaluate_camera_paths.py
```

输出文件：

```text
experiment/outputs/llm_camera/summary.json
```

论文使用的客观指标包括 JSON 解析率、参数合法率、camera path 生成率、轨迹连续性和目标保持率。

## WSL 中渲染视频

渲染依赖 Nerfstudio 环境和已训练好的 Splatfacto config。示例命令：

```bash
cd /mnt/d/2026_spring/Graphics/final

bash experiment/wsl/render_llm_camera_paths.sh \
  --config /home/orangelxl/CG/nerfstudio/outputs/lego_splatfacto/splatfacto/2026-06-13_124906/config.yml \
  --render-cwd /home/orangelxl/CG/nerfstudio \
  --source rule

bash experiment/wsl/render_llm_camera_paths.sh \
  --config /home/orangelxl/CG/nerfstudio/outputs/lego_splatfacto/splatfacto/2026-06-13_124906/config.yml \
  --render-cwd /home/orangelxl/CG/nerfstudio \
  --source llm
```

只渲染前两条用于测试：

```bash
bash experiment/wsl/render_llm_camera_paths.sh \
  --config "$CONFIG" \
  --render-cwd /home/orangelxl/CG/nerfstudio \
  --source llm \
  --limit 2
```

常见问题：

- 如果报 `transforms_train.json` 不存在，通常是 `config.yml` 中的数据路径为相对路径，而当前工作目录不对。设置 `--render-cwd /home/orangelxl/CG/nerfstudio`。
- 如果报 checkpoint 不存在，确认 `config.yml` 指向的 `outputs/.../nerfstudio_models/` 下存在 `.ckpt` 文件。
- 如果构建 `gsplat_cuda` 报错，优先确认 CUDA、gcc/g++ 版本匹配。脚本会自动优先使用 `/usr/bin/gcc-11` 和 `/usr/bin/g++-11`，并设置 `MAX_JOBS=2` 降低编译压力。

## 论文中未使用的内容

以下脚本或产物保留用于扩展实验，但未作为最终论文主要结论：

- `measure_nerfstudio_render_time.sh`：统一渲染计时尚未完成。
- `run_multiscene_nerfstudio.sh` 和 `write_multiscene_commands.py`：多场景实验未纳入正文。
- `formal/lego/render_timing/`：旧计时尝试，不作为正式效率数据。

如果需要节省空间，优先保留：

```text
experiment/outputs/formal/lego/{gt,traditional_visual_hull,nerfacto,splatfacto,summary}
experiment/outputs/llm_camera/{paths,camera_paths,renders,summary.json}
images/experiments/
```
