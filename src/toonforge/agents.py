from .skills import load_skill


class ImageAnalysisAgent:
    name = "image-analysis"

    def __init__(self, vision):
        self.vision = vision

    def run(self, source):
        return self.vision.analyze(source, load_skill(self.name))


class MeshBuilderAgent:
    name = "mesh-builder"

    def __init__(self, tools):
        self.tools = tools

    def run(self, source, output):
        self.tools.run("generate_mesh", {"image_path": str(source), "output_path": str(output)})


class ToonStylistAgent:
    name = "toon-stylist"

    def __init__(self, tools):
        self.tools = tools

    def run(self, model, output):
        self.tools.run("render_toon", {"model_path": str(model), "output_path": str(output)})


class ToonReviewAgent:
    name = "toon-review"

    def __init__(self, vision):
        self.vision = vision

    def run(self, source, preview):
        return self.vision.review(source, preview, load_skill(self.name))
