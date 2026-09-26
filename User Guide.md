# User Guide

版本：2026-09-26。一阶段开发和测试在 Windows/Python 3.13 完成；DGX Spark 的实际部署与验收记录见第 8 节。

## 1. 准备系统

在 Spark 上分别准备 Python 3.11 或 3.12、Git、Ollama、ARM64 版 Blender 4.0.x，以及一个独立运行的 Hunyuan3D 2.1 环境。先执行：

```bash
uname -m
nvidia-smi
python3.12 --version
blender --version
```

也可执行 `bash scripts/doctor-spark.sh` 得到只读检查结果。脚本退出码为 0 表示所检查的命令与本地服务均就绪，1 表示有缺项；它不检查模型生成质量。

`uname -m` 应为 `aarch64`。DGX Spark 使用 128 GB 统一内存；能装入权重不代表 CUDA 扩展适配。Hunyuan3D 的形状与纹理模块需要 GPU 扩展，先按[上游安装说明](https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1)在独立环境试运行，再接入本项目。上游示例环境是 Python 3.10 / CUDA 12.4，不能直接假设与 GB10 兼容。需记录实际 PyTorch/CUDA/扩展版本和编译错误；不要改变本项目的 Python 环境来迁就上游。

## 2. 安装本项目

在项目根目录：

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[test]'
python examples/make_sample.py data/sample-mug.png
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

若上游 API 在 GB10 上无法运行，可选用[社区 Spark 移植项目](https://github.com/simon-lehmann/hunyuan3d-spark-fast)及本项目的本地桥接。该项目公开了 ARM64/CUDA 13 的形状、纹理 Docker 推理脚本，但没有 `/generate` API；桥接服务负责协议转换。该移植已在本项目的 DGX Spark 上完成实机验证；首次部署仍应先检查其构建和模型推理，再运行桥接：

```bash
# 在 Spark 上，先安装 Docker、NVIDIA Container Toolkit，并确认 docker compose 可用
git clone https://github.com/simon-lehmann/hunyuan3d-spark-fast.git ../hunyuan3d-spark-fast
cd ../hunyuan3d-spark-fast
cp .env.example .env
# 编辑 .env 的 HF_HOME 为本机已下载 tencent/Hunyuan3D-2.1 和 facebook/dinov2-giant 的绝对缓存路径
docker compose build shape full
docker compose run --rm shape scripts/shape_infer.py --image /workspace/assets/demo.png --out /workspace/out/shape.glb
docker compose run --rm full scripts/texture_infer.py --mesh /workspace/out/shape.glb --image /workspace/assets/demo.png --out /workspace/out/textured.glb
```

确认 `out/textured.glb` 能打开后，回到本项目目录，在已安装本项目依赖的环境启动桥接：

```bash
python -m toonforge.spark_bridge --repo ../hunyuan3d-spark-fast --port 8081
# 另一个终端
curl --fail http://127.0.0.1:8081/health
```

桥接使用社区镜像的 `ENTRYPOINT python`，因此 `docker compose run` 后直接传脚本路径。桥接只接收带纹理 GLB 请求，逐个调用形状与纹理容器；不要启动多个桥接实例。首次构建、权重下载和首次推理可能较慢。权重许可、Docker GPU 挂载、容器文件权限和具体耗时必须以 Spark 实机结果为准。

### Blender

Ubuntu 24.04 的 ARM64 仓库有 Blender 4.0.2。先检查 `apt-cache policy blender`，确认候选版本后安装：

```bash
sudo apt update
sudo apt install blender
blender --version
```

Blender 官网 4.2 LTS 的 Linux 下载目录只列 x64 构建，不能直接安装到 Spark。渲染脚本会按版本选择 4.0 的 Eevee 或 4.2 的 Eevee Next。项目通过 `blender --background --python scripts/blender_toon.py -- model.glb preview.png` 渲染。无屏幕的 Spark 上，Eevee/Freestyle 可能需要额外显示或图形上下文设置，需用实际 GLB 验证。

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
| 卡在 rendering | `BLENDER_BIN`、Blender 4.0/4.2、Eevee 图形上下文、GLB 可导入性 |
| `failed` | 打开任务 `job.json` 的 `stage` 和 `error`；保留目录用于复现 |

外部依据：[DGX Spark 硬件](https://docs.nvidia.com/dgx/dgx-spark/hardware.html)、[Hunyuan3D API](https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1/blob/main/API_DOCUMENTATION.md)、[Ubuntu ARM64 Blender 包](https://packages.ubuntu.com/noble/blender)、[Blender 4.2 下载目录](https://download.blender.org/release/Blender4.2/)。

## 8. 本次 DGX Spark 部署

项目位于 `/home/lujunliang/project`，Hunyuan3D 的 Spark 适配仓库位于 `/home/lujunliang/hunyuan3d-spark-fast`。项目使用 Python 3.12 虚拟环境 `.venv`，Ollama 模型为 `qwen3.8:27b`。Hunyuan3D 和 DINO 权重复用 `/home/lujunliang/.cache/huggingface`，Blender 4.0.2 的 ARM64 包安装在项目 `.tools/blender`，由 `scripts/blender-spark.sh` 启动。

所有示例输入、任务产物、构建日志和 Hunyuan3D 中间文件位于项目 `data/`。适配仓库的 `assets/` 与 `out/` 指向 `data/.hunyuan/`。运行配置在 `data/run.env`，内容为：

```bash
export TOONFORGE_DATA_ROOT=/home/lujunliang/project/data/jobs
export OLLAMA_MODEL=qwen3.8:27b
export BLENDER_BIN=/home/lujunliang/project/scripts/blender-spark.sh
```

首次部署时，在适配仓库执行 `docker compose build shape full`。本机 Docker Hub 的 Dockerfile 前端及 GitHub Git 入口不稳定，因此适配仓库 Dockerfile 已去掉首行 `# syntax=docker/dockerfile:1.7`，将腾讯官方源码获取方式改为 `codeload.github.com` 归档，并让后续 Python 依赖使用阿里云 PyPI 镜像。Compose 文件已去掉两处 `runtime: nvidia`，保留 `gpus: all`；形状和纹理容器均已实测能访问 GB10。

启动、测试和演示：

```bash
cd /home/lujunliang/project
. data/run.env
.venv/bin/python -m pytest -q
bash scripts/doctor-spark.sh
.venv/bin/python -m toonforge.spark_bridge --repo /home/lujunliang/hunyuan3d-spark-fast --port 8081
# 在另一终端：
.venv/bin/python -m toonforge.cli serve --host 127.0.0.1 --port 8000
# 自行生成简易样图，或使用已生成的透视杯图执行完整任务：
.venv/bin/python examples/make_sample.py data/sample-mug.png
.venv/bin/python -m toonforge.cli run data/generated-mug.png
```

在开发机执行 `ssh -L 8000:127.0.0.1:8000 book_river` 后打开 `http://127.0.0.1:8000/`。任务输出位于 `data/jobs/<任务 ID>/`，应检查 `job.json` 的 `status`、`model.glb` 和 `preview.png`。本机已通过 18 项 Python 测试，并用 `data/generated-mug.png` 完成视觉分析、带纹理 3D 建模、Blender 渲染及视觉审稿。验收任务为 `data/jobs/7619ef12-b17f-4dca-bc73-3b2a40593d68/`：`status=completed`、`error=null`、视觉审稿分数 4/5，GLB 和 PNG 格式均已检查。预览中有少量颗粒与蓝色边线，属于当前模型质量限制。

## 9. 纯本地模型复验（data1）

`data1/` 是独立的复验目录，不写入上面的 `data/`。输入图由 Spark 上的 Blender 脚本 `examples/create_local_mug.py` 本机渲染；视觉分析与复核使用本机 Ollama 的 `qwen3.8:27b`；形状与纹理由已安装的 Hunyuan3D Docker 镜像及本机权重完成。`deploy/spark-offline/compose.yaml` 禁止拉取镜像，容器网络为 `none`，权重缓存只读挂载；Diffusers 必需的动态模块缓存写到 `data1/.cache/`。首次运行前，从仓库中的模板建立运行目录：

```bash
cd /home/lujunliang/project
mkdir -p data1/.hunyuan-run data1/.hunyuan/assets data1/.hunyuan/out data1/.cache/huggingface/modules data1/jobs
ln -s ../.hunyuan/assets data1/.hunyuan-run/assets
ln -s ../.hunyuan/out data1/.hunyuan-run/out
cp deploy/spark-offline/compose.yaml data1/.hunyuan-run/compose.yaml
cp deploy/spark-offline/run.env.example data1/run.env
```

```bash
cd /home/lujunliang/project
. data1/run.env
scripts/blender-spark.sh --background --python examples/create_local_mug.py -- /home/lujunliang/project/data1/local-mug.png
# 若 8082 桥接服务尚未运行，在另一个终端启动：
.venv/bin/python -m toonforge.spark_bridge --repo /home/lujunliang/project/data1/.hunyuan-run --port 8082
# 回到当前终端：
.venv/bin/python -m toonforge.cli run data1/local-mug.png
```

已完成的任务位于 `data1/jobs/c85b2ccc-66be-42d0-9ae9-437de955bbb8/`，含 `input.png`、`model.glb`、`preview.png` 和 `job.json`。状态为 `completed`，四个阶段均成功，视觉复核 4/5。模型权重和 Ollama 模型继续使用 Spark 的本机缓存，不复制到 `data1/`。
