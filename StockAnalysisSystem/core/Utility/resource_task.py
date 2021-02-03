from .common import ProgressRate
from .task_queue import TaskQueue
from .resource_manager import ResourceManager


class ResourceTask(TaskQueue.Task):
    def __init__(self, task_name: str, resource_manager: ResourceManager):
        self.__resource_manager = resource_manager

        self.__result = None
        self.__progress = ProgressRate()
        self.__resource_id = resource_manager.allocate_resource(
            task_name, master=self, progress=self.__progress, result=None)

        super(ResourceTask, self).__init__(task_name)

    def finished(self) -> bool:
        return self.status() in \
               [TaskQueue.Task.STATUS_CANCELED, TaskQueue.Task.STATUS_FINISHED, TaskQueue.Task.STATUS_EXCEPTION]

    def res_id(self) -> str:
        return self.__resource_id

    def result(self) -> any:
        return self.__result

    def progress(self) -> ProgressRate:
        return self.__progress

    def update_result(self, result: any):
        self.__result = result
        self.__resource_manager.set_resource(
            self.__resource_id, ResourceManager.RESOURCE_RESULT, result)

    # -------------- Must Override --------------

    def run(self):
        pass

    def quit(self):
        pass

    def identity(self) -> str:
        # Must override
        assert False


