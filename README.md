# ToonForge MVP

面向 NVIDIA DGX Spark 黑客松的本地多 Agent 样机：单物体插画 → 3D GLB → Blender 三渲二 PNG。分析与复核使用本地视觉模型；建模和渲染通过 MCP 工具执行。正式运行不调用云端推理 API。

## 项目说明：功能与核心亮点

ToonForge 面向需要把一张单物体插画快速变为可展示 3D 资产的参赛团队。用户上传主体清楚的 PNG/JPEG 后，网页显示任务阶段，并在完成时提供三渲二 PNG 预览和 GLB 模型下载；命令行也能运行同一流程。每个任务独立保存输入、模型、预览和状态，方便回看生成结果或排查失败。项目专注单主体演示，背面细节由模型推断，不承诺复杂场景或商用级拓扑质量。

工作流由四个职责明确的 Agent 串接：分析 Agent 提取主体描述与主色，建模 Agent 生成带纹理 GLB，风格 Agent 调用 Blender 输出三渲二预览，质检 Agent 比较原图与预览并记录 0～5 分及最明显的差异。评分是复核提示，不是客观质量证明。Agent Skills 的设计是把分析与质检规则分别写入 [image-analysis Skill](skills/image-analysis/SKILL.md) 和 [toon-review Skill](skills/toon-review/SKILL.md)：两个 Markdown 文件规定模型的关注点和 JSON 输出，运行时由 `skills.py` 读取，因此领域规则可单独修改和复查。建模与渲染由本地 MCP stdio 工具执行，工具限制输入和输出路径必须位于任务数据目录，减少越界写入风险。

## 技术实现与架构设计

```text
Web / CLI（接口层）
  → Workflow + 四个 Agent（应用编排层）
    → Skill 读取与任务存储（领域能力）
    → Ollama 视觉适配器 / MCP 客户端（基础设施层）
      → MCP stdio 服务 → 本地 Hunyuan3D HTTP / Blender 后台脚本
```

项目使用 Python 3.11/3.12、FastAPI、Pillow 和 MCP Python SDK。`api.py` 与 `cli.py` 提供入口，`workflow.py` 按分析、建模、渲染、复核的固定顺序交接结果；`storage.py` 将阶段、错误、分析结果、质检结果和 Agent 轨迹写入 `data/jobs/<任务 ID>/job.json`。页面轮询任务状态；进程重启后未完成的任务标记为失败，已有文件保留。接口层只进入应用编排，模型与渲染适配器承担外部依赖：`hunyuan.py` 调用本机 `/generate` 协议，Spark 上可由 `spark_bridge.py` 将该协议转换为形状和纹理两个 Docker Compose 推理步骤；Blender 脚本使用 Eevee、分段明暗和轮廓线渲染，不覆盖原始 GLB 材质。这样更换模型服务时主要修改基础设施适配器；任务 JSON 字段、MCP 工具签名和产物文件名则需保持兼容。模块依赖和接口契约见[设计文档](docs/设计文档.md)。

## 本地算力部署与大模型优化

目标设备是一台 DGX Spark。Ollama 在本机提供视觉分析和结果复核；Hunyuan3D 2.1 在独立环境生成形状与纹理；Blender 在后台渲染。Spark 的 ARM64/CUDA 推理环境与项目 Python 环境分开，避免 3D 模型的 GPU 扩展依赖污染 Web 服务。Hunyuan3D 可使用上游本机 API，也可经本项目桥接服务调用已在 Spark 上验证的社区移植容器。运行前需分别准备权重、Blender 与 GPU 容器环境；首次下载可联网，完成准备后的正式推理只访问本机服务。完整步骤和实机验收记录见 [User Guide.md](User%20Guide.md)。

四个 Agent 在项目进程中按阶段实例化和调用：视觉 Agent 访问同一个本机 Ollama 端点，建模与风格 Agent 通过 MCP 客户端启动本项目的 stdio 工具服务，后者再调用 Hunyuan3D 或 Blender。这种部署方式让 Agent 的规则、编排状态和 GPU 推理进程各有明确边界。

当前优化聚焦资源使用与演示稳定性：分析和复核共用一套本地视觉模型权重，避免为两个角色各加载一份；视觉请求指定 JSON 格式及温度 0，并校验关键字段，减少不可解析的输出；桥接服务单实例串行执行形状与纹理阶段，避免容器脚本的固定中间文件互相覆盖；[离线 Compose 配置](deploy/spark-offline/compose.yaml) 使用本地镜像、禁止拉取、关闭容器网络并只读挂载权重缓存，以便复验。项目尚未实现模型量化、蒸馏或自研 CUDA 内核。串行启动容器会增加时延，如需优化为常驻推理服务，应先测量耗时、内存峰值和结果质量。

### NVIDIA 与 StepFun 阶跃星辰技术栈

| 类别 | 当前项目中的实际用途 |
|---|---|
| NVIDIA 硬件与运行环境 | DGX Spark GPU 执行本地模型推理；部署依赖 NVIDIA 驱动、CUDA 兼容环境及 NVIDIA Container Toolkit 提供容器 GPU 访问。Compose 配置了 `gpus: all`。 |
| NVIDIA SDK | 项目代码没有直接调用 NVIDIA SDK；GPU 能力由 Ollama、Hunyuan3D 的推理环境和容器运行时使用。 |
| NVIDIA 模型 | 当前工作流未使用 NVIDIA 发布的模型。 |
| StepFun 阶跃星辰模型 | 当前工作流未接入 StepFun 模型或 API；视觉模型为本机 Ollama 运行的 Qwen 系列模型，3D 模型为 Hunyuan3D 2.1。 |

此表按仓库实现和实机记录填写。若比赛提交要求必须使用指定 NVIDIA SDK 或 StepFun 模型，当前版本尚不满足该技术栈条件，需要完成真实集成与验证后再更新说明。

## 快速入口

- [方案](docs/方案.md) · [需求文档](docs/需求文档.md) · [设计文档](docs/设计文档.md)
- [完整启动、测试和部署流程](User%20Guide.md)
- [阶段记录与断点续做](docs/阶段记录.md)

以下命令安装项目并启动网页；运行完整生成任务前，须按用户指南先启动本机 Ollama、Hunyuan3D 服务并安装 Blender。

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
python examples/make_sample.py data/sample-cup.png
pytest -q
python -m toonforge.cli serve
```

网页地址 `http://127.0.0.1:8000`。DGX Spark 上的项目位于 `/home/lujunliang/project`；已用 `data/generated-mug.png` 实机跑通本地视觉分析、Hunyuan3D 形状与纹理、Blender 渲染和视觉复核。`data1/` 另有完全本地的复验任务，输入图由本机 Blender 生成，Hunyuan3D 容器断网运行。模型与预览保存在各自的任务目录，启动和验收命令见用户指南。

基本部署顺序是：准备模型权重及 GPU 环境 → 安装项目并运行 `bash scripts/test.sh` → 启动本机 Ollama 与 Hunyuan3D → 检查 Blender → 执行 `bash scripts/start.sh` → 上传自有图片，检查 GLB、PNG 与 `job.json`。外部服务就绪后也可执行 `bash scripts/deploy-spark.sh`，让脚本完成安装、测试、健康检查和前台启动。默认仅监听 `127.0.0.1`。

## 结构

```text
src/toonforge/      接口、专职 Agent、应用编排、领域存储、模型/MCP/Blender 适配器
src/toonforge/static/  本地网页
skills/             分析与质检的可复用 Skill
scripts/            Blender 渲染、启动与测试脚本
examples/           演示输入生成代码
tests/              单元和协议测试
docs/               方案、需求、设计、阶段记录
data/jobs/          运行时产物，默认不纳入版本管理
```

依赖方向与契约见 [设计文档](docs/设计文档.md)。项目代码以本地演示为目标；权重、Blender 和 Hunyuan3D 均由运行者独立安装并遵守各自许可。
