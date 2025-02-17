

from src.templates.workerprocess import WorkerProcess
from src.movement.move.threads.threadmove import threadmove

class processmove(WorkerProcess):
    """This process handles movement.
    Args:
        queueList (dictionary of multiprocessing.queues.Queue): Dictionary of queues where the ID is the type of messages.
        logging (logging object): Made for debugging.
        debugging (bool, optional): A flag for debugging. Defaults to False.
    """

    def __init__(self, queueList, logging, debugging=False):
        self.queuesList = queueList
        self.logging = logging
        self.debugging = debugging
        super(processmove, self).__init__(self.queuesList)

    def run(self):
        """Apply the initializing methods and start the threads."""
        super(processmove, self).run()

    def _init_threads(self):
        """Create the move Publisher thread and add to the list of threads."""
        moveTh = threadmove(
            self.queuesList, self.logging, self.debugging
        )
        self.threads.append(moveTh)

if __name__ == "__main__":
    from multiprocessing import Queue, Pipe
    import logging
    import time

    allProcesses = list()
    debugg = False
    # We have a list of multiprocessing.Queue() which individualy represent a priority for processes.
    queueList = {
        "Critical": Queue(),
        "Warning": Queue(),
        "General": Queue(),
        "Config": Queue(),
    }
    logger = logging.getLogger()
    pipeRecv, pipeSend = Pipe(duplex=False)
    process = processmove(queueList, logger, debugg, True)
    process.daemon = True
    process.start()
    time.sleep(4)  # modify the value to increase/decrease the time of the example
    process.stop()
