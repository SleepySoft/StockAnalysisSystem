import sys
import time
import traceback
import threading


class TaskQueue:

    # ---------------------------------------- Task -----------------------------------------

    class Task:
        def __init__(self, name: str):
            self.__name = name

        def __str__(self):
            return 'Task %s [%s]' % (self.name(), self.identity())

        def name(self) -> str:
            return self.__name

        def status(self) -> int:
            # TODO: Waiting, Running, Finished, Canceled
            pass

        def run(self):
            pass

        def quit(self):
            pass

        def identity(self) -> str:
            pass

    # -------------------------------------- Observer ---------------------------------------

    class Observer:
        def __init__(self):
            pass

        def on_task_updated(self, task, change: str):
            pass

    # -------------------------------------- TaskQueue --------------------------------------

    def __init__(self):
        self.__lock = threading.Lock()
        self.__quit_flag = True
        self.__observers = []
        self.__task_queue = []
        self.__task_thread = None
        self.__running_task = None
        self.__will_task = None

    def join(self, timeout: int):
        if self.__task_thread is not None:
            self.__task_thread.join(timeout)

    def quit(self):
        self.__lock.acquire()
        self.__quit_flag = True
        self.__clear_pending_task()
        self.__cancel_running_task()
        self.__lock.release()

    def start(self):
        if self.__task_thread is None or self.__task_thread.is_alive():
            self.__quit_flag = False
            self.__task_thread = threading.Thread(target=self.__task_thread_entry)
            self.__task_thread.start()

    def is_busy(self) -> bool:
        return self.__running_task is not None or len(self.__task_queue) > 0

    # -------------------------------- Task Related --------------------------------

    def get_tasks(self, name: str or None, identity: str or None) -> [Task]:
        task_list = []
        self.__lock.acquire()
        for task in self.__task_queue:
            if (name is None and identity is None) or \
                    (name is not None and task.name):
                task_list.append(task)
        if self.__running_task is not None:
            if identity is None or self.__running_task.identity() == identity:
                task_list.insert(0, self.__running_task)
        self.__lock.release()
        return task_list

    def append_task(self, task: Task, unique: bool = True) -> bool:
        print('Task queue -> append : ' + str(task))
        self.__lock.acquire()
        if unique and (task.identity() is not None and
                       len(self.__find_adapt_tasks(None, task.identity())) > 0):
            self.__lock.release()
            print('Task queue -> found duplicate, drop.')
            return False
        self.__task_queue.append(task)
        self.__lock.release()
        self.notify_task_updated(task, 'append')
        return True

    def insert_task(self, task: Task, index: int = 0, unique: bool = True):
        print('Task queue -> insert : ' + str(task))
        self.__lock.acquire()
        if unique:
            self.__remove_pending_task(task.identity())
            self.__check_cancel_running_task(task.identity())
        if index >= len(self.__task_queue):
            self.__task_queue.append(task)
        else:
            self.__task_queue.insert(index, task)
        self.__lock.release()
        self.notify_task_updated(task, 'insert')

    def set_will_task(self, task: Task):
        self.__will_task = task

    def cancel_task(self, identity: str or None):
        self.__lock.acquire()
        if identity is None:
            self.__clear_pending_task()
            self.__cancel_running_task()
        else:
            self.__remove_pending_task(identity)
            self.__check_cancel_running_task(identity)
        self.__lock.release()
        self.notify_task_updated(None, 'canceled')

    def cancel_running_task(self):
        self.__lock.acquire()
        self.__cancel_running_task()
        self.__lock.release()
        self.notify_task_updated(None, 'canceled')

    def find_matching_tasks(self, name: str or None, identity: str or None) -> [Task]:
        self.__lock.acquire()
        tasks = self.__find_adapt_tasks(name, identity)
        self.__lock.release()
        return tasks

    # ------------------------------------ Observer -------------------------------------

    def add_observer(self, ob: Observer):
        if ob not in self.__observers:
            self.__observers.append(ob)

    def notify_task_updated(self, task: Task, action: str):
        for ob in self.__observers:
            ob.on_task_updated(task, action)

    # ------------------------------------- private --------------------------------------

    def __adapted_task(self, task: Task, name: str or None, identity: str or None) -> Task or None:
        adapt = True
        if task is not None:
            if name is not None and name != '':
                adapt = (adapt and (task.name() == name))
            if identity is not None and identity != '':
                adapt = (adapt and (task.identity() == identity))
        return task if adapt else None

    def __find_adapt_tasks(self, name: str or None, identity: str or None) -> [Task]:
        tasks = []
        for task in self.__task_queue:
            if self.__adapted_task(task, name, identity):
                tasks.append(task)
        if self.__adapted_task(self.__running_task, name, identity):
            tasks.append(self.__running_task)
        return tasks

    def __remove_pending_task(self, identity):
        if identity is None:
            return
        task_queue = self.__task_queue.copy()
        for task in task_queue:
            if task.identity() == identity:
                self.__task_queue.remove(task)

    def __clear_pending_task(self):
        self.__task_queue.clear()

    def __check_cancel_running_task(self, identity: str or None):
        if identity is None or \
                (self.__running_task is not None and
                 self.__running_task.identity() == identity):
            self.__cancel_running_task()

    def __cancel_running_task(self):
        if self.__running_task is not None:
            self.__running_task.quit()

    # ----------------------------------- Thread Entry -----------------------------------

    def __task_thread_entry(self):
        quit_thread = False
        while not quit_thread:
            self.__lock.acquire()
            if self.__quit_flag:
                quit_thread = True
                task = self.__will_task
            else:
                task = self.__task_queue.pop(0) if len(self.__task_queue) > 0 else None
            self.__running_task = task
            self.__lock.release()

            clock = time.time()
            if task is not None:
                try:
                    print('Task queue -> start: ' + str(task))
                    self.notify_task_updated(task, 'started')
                    task.run()
                except Exception as e:
                    print('Task queue -> ' + str(task) + ' got exception:')
                    print(e)
                    print(traceback.format_exc())
                finally:
                    print('Task queue -> finish: %s, time spending: %.2f ms' %
                          (str(task), (time.time() - clock) * 1000))
                    self.notify_task_updated(task, 'finished')
                    self.__lock.acquire()
                    self.__running_task = None
                    self.__lock.release()
            else:
                time.sleep(0.1)


# ----------------------------------------------------------------------------------------------------------------------

class TestTask(TaskQueue.Task):
    LOG_START = []
    LOG_FINISH = []

    @staticmethod
    def reset():
        TestTask.LOG_START.clear()
        TestTask.LOG_FINISH.clear()

    def __init__(self, name: str, _id: str, delay: int):
        super(TestTask, self).__init__(name)
        self.__id = _id
        self.__delay = delay
        self.__quit_flag = False

    def run(self):
        TestTask.LOG_START.append(self.__id)
        print('Task %s started' % self.__id)
        slept = 0
        while not self.__quit_flag and slept < self.__delay:
            time.sleep(0.1)
            slept += 0.1
        TestTask.LOG_FINISH.append(self.__id)
        print('Task %s finished' % self.__id)

    def quit(self):
        self.__quit_flag = True

    def identity(self) -> str:
        return self.__id


def test_basic_feature():
    task_queue = TaskQueue()
    task_queue.start()
    TestTask.reset()

    task_a = TestTask('TaskA', 'task_a', 30)
    task_b = TestTask('TaskB', 'task_b', 4)
    task_c = TestTask('TaskB', 'task_c', 3)
    task_will = TestTask('TaskWill', 'will', 0)
    task_blocking = TestTask('TaskBlocking', 'task_blocking', 999)

    task_queue.append_task(task_a)
    task_queue.append_task(task_b)
    task_queue.append_task(task_c)
    task_queue.append_task(task_blocking)
    task_queue.set_will_task(task_will)

    assert task_queue.is_busy()
    time.sleep(1)
    assert 'task_a' in TestTask.LOG_START
    task_queue.cancel_running_task()
    time.sleep(1)
    assert 'task_a' in TestTask.LOG_FINISH

    assert task_queue.is_busy()
    time.sleep(1)
    assert 'task_b' in TestTask.LOG_START

    task_queue.cancel_task('task_c')
    assert 'task_b' not in TestTask.LOG_FINISH

    assert task_queue.is_busy()
    time.sleep(4)
    assert 'task_b' in TestTask.LOG_FINISH
    assert 'task_c' not in TestTask.LOG_START

    assert task_queue.is_busy()
    time.sleep(1)
    assert 'task_blocking' in TestTask.LOG_START
    assert task_queue.is_busy()

    task_queue.quit()
    task_queue.join(1)

    assert not task_queue.is_busy()
    assert 'task_blocking' in TestTask.LOG_FINISH
    assert 'will' in TestTask.LOG_START
    assert 'will' in TestTask.LOG_FINISH


def test_entry() -> bool:
    test_basic_feature()
    return True


def main():
    test_entry()


# ----------------------------------------------------------------------------------------------------------------------

def exception_hook(type, value, tback):
    # log the exception here
    print('Exception hook triggered.')
    print(type)
    print(value)
    print(tback)
    # then call the default handler
    sys.__excepthook__(type, value, tback)


sys.excepthook = exception_hook


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print('Error =>', e)
        print('Error =>', traceback.format_exc())
        exit()
    finally:
        pass











































