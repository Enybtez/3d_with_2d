# Illustration to Toon MVP Design

本规范以 [需求文档](../../需求文档.md) 和 [设计文档](../../设计文档.md) 为准。第一阶段交付单物体插画到本地 GLB、Blender 三渲二 PNG 的可运行编排，四个专职 Agent、项目 Skill、MCP 工具、任务持久化与 Web/CLI。真实 DGX Spark 模型与渲染联调作为第二阶段验收，不使用模拟输出冒充成功。

关键接口：`POST /api/jobs`、`GET /api/jobs/{id}`、MCP `generate_mesh(image_path, output_path)` 和 `render_toon(model_path, output_path)`。任务状态与产物由 `data/jobs/<uuid>/job.json` 持久保存。正式推理调用本机 Ollama 和本机 Hunyuan3D 服务，渲染调用本机 Blender。
