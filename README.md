# ToonForge MVP

面向 NVIDIA DGX Spark 黑客松的本地多 Agent 样机：单物体插画 → 3D GLB → Blender 三渲二 PNG。分析与复核使用本地视觉模型；建模和渲染通过 MCP 工具执行。正式运行不调用云端推理 API。

## 快速入口

- [方案](docs/方案.md) · [需求文档](docs/需求文档.md) · [设计文档](docs/设计文档.md)
- [完整启动、测试和部署流程](User%20Guide.md)
- [阶段记录与断点续做](docs/阶段记录.md)

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
python examples/make_sample.py data/sample-cup.png
pytest -q
python -m toonforge.cli serve
```

网页地址 `http://127.0.0.1:8000`。真正生成前还需本地 Ollama、Hunyuan3D API 或 Spark CLI 桥接，以及 Blender，见用户指南。当前开发机没有 DGX Spark 或 Blender，真实模型/渲染效果尚未实机验收。

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
