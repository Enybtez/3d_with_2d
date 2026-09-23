from .agents import ImageAnalysisAgent, MeshBuilderAgent, ToonReviewAgent, ToonStylistAgent


class Workflow:
    def __init__(self, store, vision, tools):
        self.store = store
        self.analysis_agent = ImageAnalysisAgent(vision)
        self.mesh_agent = MeshBuilderAgent(tools)
        self.stylist_agent = ToonStylistAgent(tools)
        self.review_agent = ToonReviewAgent(vision)

    def _record(self, job_id: str, agent: str, **fields) -> dict:
        trace = self.store.get(job_id)["agent_trace"] + [{"agent": agent, "status": "completed"}]
        return self.store.update(job_id, agent_trace=trace, **fields)

    def run(self, job_id: str) -> dict:
        directory = self.store.directory(job_id)
        source = directory / self.store.get(job_id)["input"]
        model = directory / "model.glb"
        preview = directory / "preview.png"
        stage = "analyzing"
        try:
            self.store.update(job_id, status=stage, stage=stage)
            analysis = self.analysis_agent.run(source)
            stage = "modeling"
            self._record(job_id, self.analysis_agent.name, status=stage, stage=stage, analysis=analysis)
            self.mesh_agent.run(source, model)
            if not model.is_file():
                raise RuntimeError("建模工具未生成 GLB")
            stage = "rendering"
            self._record(job_id, self.mesh_agent.name, status=stage, stage=stage)
            self.stylist_agent.run(model, preview)
            if not preview.is_file():
                raise RuntimeError("渲染工具未生成 PNG")
            stage = "reviewing"
            self._record(job_id, self.stylist_agent.name, status=stage, stage=stage)
            review = self.review_agent.run(source, preview)
            return self._record(job_id, self.review_agent.name, status="completed", stage="completed", review=review)
        except Exception as exc:
            return self.store.update(job_id, status="failed", stage=stage, error=str(exc))
