from .common import ProgressRate
from .task_queue import TaskQueue


class TaskFuture(TaskQueue.Task):
    def __init__(self, task_name: str):
        self.__result = None
        self.__progress = ProgressRate()
        super(TaskFuture, self).__init__(task_name)

    def get_result(self) -> any:
        return self.__result

    def update_result(self, result: any):
        self.__result = result

    def get_progress_rage(self) -> ProgressRate:
        return self.__progress

    # -------------- Must Override --------------

    def run(self):
        pass

    def quit(self):
        pass

    def identity(self) -> str:
        # Must override
        assert False


