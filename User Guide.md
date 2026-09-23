# User Guide

版本：2026-09-23。一阶段开发和测试在 Windows/Python 3.13 完成；目标部署平台为 DGX Spark 的 Linux ARM64。真实生成要在 Spark 上补做实机验收。

## 1. 准备系统

在 Spark 上分别准备 Python 3.11、Git、Ollama、Blender 4.2 LTS，以及一个独立运行的 Hunyuan3D 2.1 环境。先执行：

```bash
uname -m
nvidia-smi
python3.11 --version
blender --version
```

`uname -m` 应为 `aarch64`。DGX Spark 使用 128 GB 统一内存；能装入权重不代表 CUDA 扩展适配。Hunyuan3D 的形状与纹理模块需要 GPU 扩展，先按[上游安装说明](https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1)在独立环境试运行，再接入本项目。上游示例环境是 Python 3.10 / CUDA 12.4，不能直接假设与 GB10 兼容。需记录实际 PyTorch/CUDA/扩展版本和编译错误；不要改变本项目的 Python 环境来迁就上游。

## 2. 安装本项目

在项目根目录：

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[test]'
python examples/make_sample.py data/sample-cup.png
```

Windows 开发机可用 `py -3.11 -m venv .venv`、`.venv\Scripts\Activate.ps1`，后续命令相同。建议把所有运行时数据保存在 `data/jobs/`，不要把私有插画或权重提交到 Git。

## 3. 启动三个本地服务

### Ollama 视觉模型

按 [Ollama 官方说明](https://ollama.com/blog/nvidia-spark)在 Spark 安装并启动 Ollama，然后：

```bash
ollama pull qwen3-vl:8b-instruct
curl http://127.0.0.1:11434/api/tags
```

本项目默认请求 `http://127.0.0.1:11434/api/chat`。首次拉取权重需要网络；运行时模型在本地。

### Hunyuan3D 2.1 API

确认[模型许可](https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1/blob/main/LICENSE)后，按上游 README 准备独立环境、扩展与权重。在该环境启动：

```bash
python api_server.py --host 127.0.0.1 --port 8081 --limit-model-concurrency 1
curl http://127.0.0.1:8081/health
```

这两条命令须在 Hunyuan3D 上游仓库目录及其独立环境执行。项目使用其 `/generate` 接口，要求返回 GLB 字节。若 Spark 无法编译/运行上游扩展，先在 `docs/阶段记录.md` 记录完整错误，再考虑纯形状模式或替换适配器；不要将占位模型标作完成。

### Blender

确认 `blender --version` 显示 4.2.x，并用图形驱动环境运行。项目通过 `blender --background --python scripts/blender_toon.py -- model.glb preview.png` 渲染。无屏幕的 Spark 上，Eevee/Freestyle 可能需要额外显示或图形上下文设置，需用实际 GLB 验证。

## 4. 运行样机

在本项目环境：

```bash
bash scripts/start.sh
```

打开 `http://127.0.0.1:8000`，上传单物体 PNG/JPEG。页面轮询步骤，成功后显示三渲二 PNG 并提供 GLB 下载。CLI 方式：

```bash
python -m toonforge.cli run data/sample-cup.png
```

CLI 输出任务目录。任务状态和错误保存在 `data/jobs/<任务ID>/job.json`；中断后再次启动 Web 服务会将未结束任务标为失败，已有文件仍保留。

可设置的环境变量：`TOONFORGE_DATA_ROOT`、`OLLAMA_URL`、`OLLAMA_MODEL`、`HUNYUAN_URL`、`BLENDER_BIN`。两个模型 URL 仅接受本机 HTTP 地址。改动变量后重启本项目进程和 MCP 工具进程。

## 5. 测试与验收

```bash
bash scripts/test.sh
```

此脚本运行 Python 测试和语法编译，不要求 GPU 或 Blender。协议测试会实际启动 MCP stdio 服务并调用工具；建模和渲染单元测试使用可控替身。Spark 实机应依次检查：

1. `curl` 检查 Ollama 和 Hunyuan 健康；`blender --version` 检查版本。
2. 运行示例插画，再运行至少两张团队自有单物体插画。
3. 逐个检查 `model.glb` 能被 Blender 导入、`preview.png` 可正常显示、任务 `job.json` 为 `completed`。
4. 记录每张的总耗时、内存峰值、主观轮廓/颜色差异和失败原因到阶段记录。

## 6. 基本部署流程

单机演示顺序：安装依赖 → `bash scripts/test.sh` → 启动 Ollama 和 Hunyuan → 确认 Blender → `bash scripts/start.sh` → 浏览器演示。也可在三个外部程序就绪后执行 `bash scripts/deploy-spark.sh`，脚本会安装本项目、运行测试、检查服务和 Blender，再以前台进程启动网页。默认只绑定 `127.0.0.1`。若现场需要局域网访问，可执行 `python -m toonforge.cli serve --host 0.0.0.0`，并用防火墙限制访问者；该 MVP 未提供账号认证。

## 7. 排障

| 症状 | 检查 |
|---|---|
| 卡在 analyzing | Ollama 是否启动、权重是否已拉取、`OLLAMA_MODEL` 是否匹配 |
| 卡在 modeling | Hunyuan `/health`、CUDA 扩展、显存/统一内存压力 |
| 卡在 rendering | `BLENDER_BIN`、Blender 4.2、Eevee 图形上下文、GLB 可导入性 |
| `failed` | 打开任务 `job.json` 的 `stage` 和 `error`；保留目录用于复现 |

外部依据：[DGX Spark 硬件](https://docs.nvidia.com/dgx/dgx-spark/hardware.html)、[Hunyuan3D API](https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1/blob/main/API_DOCUMENTATION.md)、[Blender 4.2 手册](https://docs.blender.org/manual/en/4.2/)。
