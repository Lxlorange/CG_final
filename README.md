# 计算机图形学结课论文

本文主题调整为“基于神经渲染与大语言模型相机控制的三维场景重建流程研究”。当前已经完成 NeRF Synthetic `lego` 场景上的三流程对比：Visual Hull、Nerfacto、Splatfacto。下一步主线是加入 LLM，将自然语言相机意图转换为 Nerfstudio/3DGS 可执行的相机轨迹。

## 当前结果

已完成结果位于 `experiment/outputs/formal/lego/summary/`：

- `summary.json`：PSNR、SSIM、标准差、最差视角等统计结果。
- `comparison.png`：真实图像、Visual Hull、Nerfacto、Splatfacto 的测试视角对比。
- `failure_cases.png`：三种方法的最差视角案例。

当前论文正文只使用已经完成的数据。未完成的数据或实验均以 `TODO_i` 或 `TODO_LLM_i` 标记。

## TODO 标记说明

| 标记 | 需要补充的内容 | 用途 | 建议执行方式 |
| --- | --- | --- | --- |
| `TODO_1` | LPIPS 指标 | 补全感知相似性评价，避免只依赖 PSNR/SSIM | 在安装 `torch` 与 `lpips` 的环境中运行 `evaluate_folder.py --lpips` 或 `postprocess_multiscene.py --lpips` |
| `TODO_2` | Nerfacto 与 Splatfacto 的统一渲染时间 | 补全流程效率对比，避免用已保存图片推断渲染耗时 | 在 WSL/Nerfstudio 环境运行 `experiment/wsl/measure_nerfstudio_render_time.sh` |
| `TODO_3` | 真实场景实验 | 验证真实光照、相机噪声、背景干扰下的稳定性 | 使用 Nerfstudio 官方真实数据，或自采视频后运行 `ns-process-data video` |
| `TODO_4` | 多合成场景实验 | 验证复杂材质、曲面、细结构和遮挡下的泛化性 | 建议增加 `materials`、`drums`、`ficus`，并复用 `write_multiscene_commands.py` 与 `postprocess_multiscene.py` |
| `TODO_5` | 统一硬件、软件版本和训练超参数记录 | 提高实验可复现性 | 记录 GPU、CUDA、Nerfstudio、Python、训练迭代数、batch/ray 设置、输出分辨率 |
| `TODO_6` | 消融实验 | 验证视角数量、训练迭代数或体素分辨率对结果的影响 | 至少选择一种变量，例如训练视角数量或 Nerfstudio 迭代次数 |

## LLM 相机控制实验 TODO

新的实验主线见 `experiment/README.md`。核心思想是参考 ChatCam/CineGPT：LLM 不直接生成三维物体或最终图像，而是把自然语言镜头描述翻译为相机轨迹参数，再驱动已经训练好的 NeRF/3DGS 模型渲染。

| 标记 | 需要补充的内容 | 用途 | 产物 |
| --- | --- | --- | --- |
| `TODO_LLM_1` | 阅读并概括 ChatCam | 补充“大模型参与图形学管线”的相关工作 | 论文相关工作段落 |
| `TODO_LLM_2` | 设计自然语言到 JSON 相机参数的 prompt | 构造 LLM 控制接口 | `experiment/llm_camera/prompts/` |
| `TODO_LLM_3` | 编写 JSON 到 Nerfstudio camera path 的转换脚本 | 让 LLM 输出可被渲染器执行 | `experiment/scripts/make_camera_path_from_json.py` |
| `TODO_LLM_4` | 生成规则模板轨迹和 LLM 轨迹 | 对比“无大模型”和“有大模型” | `experiment/outputs/llm_camera/paths/` |
| `TODO_LLM_5` | 用 Splatfacto 或 Nerfacto 渲染轨迹 | 得到视频或图像序列结果 | `experiment/outputs/llm_camera/renders/` |
| `TODO_LLM_6` | 统计解析成功率、合法率、连续性、渲染成功率和人工评分 | 评价 LLM 控制是否有效 | `experiment/outputs/llm_camera/summary.json` |
| `TODO_LLM_7` | 将实验二写入论文 | 形成最终实验与讨论 | `CGpaper.tex` |

## 常用命令

重新生成 `lego` 汇总图表：

```powershell
python experiment\scripts\make_formal_summary.py --scene lego --max-views 8
```

生成多场景 Nerfstudio 脚本：

```powershell
python experiment\scripts\write_multiscene_commands.py --scenes lego materials drums --methods nerfacto splatfacto --max-num-iterations 30000 --test-limit 20
```

在 WSL 中运行多场景脚本：

```bash
bash /mnt/d/2026_spring/Graphics/final/experiment/wsl/run_multiscene_nerfstudio.sh
```

回到 Windows 后处理：

```powershell
python experiment\scripts\postprocess_multiscene.py --scenes lego materials drums --methods nerfacto splatfacto --limit 20
```
