import time
from src.templates.threadwithstop import ThreadWithStop
from src.utils.messages.allMessages import (DrivingMode, SpeedMotor, mainCamera)
from src.utils.messages.messageHandlerSubscriber import messageHandlerSubscriber
from src.utils.messages.messageHandlerSender import messageHandlerSender
class threadmove(ThreadWithStop):
    """This thread handles move.
    Args:
        queueList (dictionary of multiprocessing.queues.Queue): Dictionary of queues where the ID is the type of messages.
        logging (logging object): Made for debugging.
        debugging (bool, optional): A flag for debugging. Defaults to False.
    """

    def __init__(self, queueList, logging, debugging=False):
        self.queuesList = queueList
        self.logging = logging
        self.debugging = debugging
        self.subscribe()
        super(threadmove, self).__init__()

        self.speed = messageHandlerSender(self.queuesList, SpeedMotor)
        self.driving_mode = messageHandlerSubscriber(self.queuesList, DrivingMode, "lastOnly", True)

    def run(self):
        while self._running:
            drv = self.driving_mode.receive()
            if drv is not None:
                if drv == "auto":
                    self.speed.send("5")
                    print("a")
    def subscribe(self):
        """Subscribes to the messages you are interested in"""
        pass
