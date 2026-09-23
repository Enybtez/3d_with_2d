from concurrent.futures import ThreadPoolExecutor


class JobQueue:
    def __init__(self, workflow):
        self.workflow = workflow
        self.executor = ThreadPoolExecutor(max_workers=1)

    def submit(self, job_id: str) -> None:
        self.executor.submit(self.workflow.run, job_id)
