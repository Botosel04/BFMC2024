if __name__ == "__main__":
    import sys
    sys.path.insert(0, "../../..")

from src.templates.workerprocess import WorkerProcess
from src.perception.signDetection.threads.threadsignDetection import threadsignDetection

class processsignDetection(WorkerProcess):
    """This process handles signDetection.
    Args:
        queueList (dictionary of multiprocessing.queues.Queue): Dictionary of queues where the ID is the type of messages.
        logging (logging object): Made for debugging.
        debugging (bool, optional): A flag for debugging. Defaults to False.
    """

    def __init__(self, queueList, logging, debugging=False):
        self.queuesList = queueList
        self.logging = logging
        self.debugging = debugging
        super(processsignDetection, self).__init__(self.queuesList)

    def run(self):
        """Apply the initializing methods and start the threads."""
        super(processsignDetection, self).run()

    def _init_threads(self):
        """Create the signDetection Publisher thread and add to the list of threads."""
        signDetectionTh = threadsignDetection(
            self.queuesList, self.logging, self.debugging
        )
        self.threads.append(signDetectionTh)
