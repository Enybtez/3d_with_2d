# Spark 本地建模桥接实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让当前 `/generate` 客户端接入使用 Docker Compose CLI 的 DGX Spark Hunyuan3D 移植。

**Architecture:** 新增本机 HTTP 桥接进程；接收现有 JSON，图片写入社区项目的 `assets/`，串行调用 `shape_infer.py` 和 `texture_infer.py`，从 `out/` 读取 GLB。主编排、MCP 协议和数据目录不改。

**Tech Stack:** Python 3.11、FastAPI、Docker Compose、Hunyuan3D Spark 社区移植。

**Spec:** `docs/设计文档.md`

## Global Constraints

- 输入为单个物体 PNG/JPEG 插画，输出为真实 GLB 字节。
- 推理仅在本地 Spark 运行；桥接仅监听 `127.0.0.1:8081`。
- 社区移植为可选依赖，不能把未实机验证说成已完成。
- 简单单进程串行运行，避免社区纹理脚本固定中间文件名造成并发覆盖。

## Review Focus

- 非法 base64 或非图片输入：返回 400，不能运行 Docker。
- 不支持的输出格式：返回 400。
- Docker 失败或没有有效 GLB：返回 502。
- 并发请求：串行进入共享输出目录。
- 工作目录位置包含空格：命令使用参数数组，不能经 Shell 拼接。

---

### Task 1: 桥接服务与测试

**Files:** `tests/test_spark_bridge.py`、`src/toonforge/spark_bridge.py`

**Interfaces:** `create_app(repo_root: Path, runner=subprocess.run) -> FastAPI`；`GET /health`；`POST /generate` 与现有 `HunyuanClient` 请求兼容。

- [x] 写 FastAPI 测试，模拟 Docker 命令生成 GLB，覆盖命令、请求错误和失败响应。
- [x] 运行测试，确认因模块缺失失败。
- [x] 实现最小桥接服务和单进程启动入口。
- [x] 运行测试，确认通过。

### Task 2: 文档与验证

**Files:** `docs/设计文档.md`、`docs/阶段记录.md`、`User Guide.md`、`README.md`

- [x] 写 Spark 移植构建和桥接启动步骤，列出待实机验收项。
- [x] 运行全套测试、语法编译和启动帮助检查。
- [x] 记录本阶段完成与未完成内容，提交改动。
